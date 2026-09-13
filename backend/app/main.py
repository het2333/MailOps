from contextlib import asynccontextmanager
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.approvals import router as approvals_router
from app.api.dashboard import router as dashboard_router
from app.api.demo import router as demo_router
from app.api.emails import router as emails_router
from app.api.integrations import router as integrations_router
from app.api.runtime import router as runtime_router
from app.core.config import get_settings
from app.db.session import Database
from app.providers.calendar import CalendarProvider
from app.providers.demo import DemoCalendarProvider, DemoGmailProvider, DemoTriageClient
from app.providers.gmail import GmailProvider
from app.providers.google_credentials import GoogleCredentialStore
from app.providers.llm import DeepSeekTriageClient
from app.services.business_tools import BusinessTools
from app.services.email_service import EmailService
from app.services.execution_service import ExecutionService
from app.services.sync_service import SyncService
from app.workflow.checkpoints import sqlite_checkpointer
from app.workflow.graph import WorkflowDependencies, build_graph


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        settings = get_settings()
        app.state.settings = settings
        database = Database(settings.database_url)
        database.initialize()
        app.state.database = database
        app.state.email_service = EmailService(database.session())
        app.state.checkpointer = sqlite_checkpointer(settings.database_url)

        def build_execution_service(session) -> ExecutionService:
            current_settings = get_settings()
            if current_settings.demo_mode:
                triage = DemoTriageClient()
                calendar = DemoCalendarProvider()
                gmail = DemoGmailProvider()
            else:
                credentials = GoogleCredentialStore(session, current_settings).credentials()
                triage = DeepSeekTriageClient(current_settings)
                calendar = CalendarProvider(credentials)
                gmail = GmailProvider(credentials)
            dependencies = WorkflowDependencies(
                session=session,
                triage=triage,
                tools=BusinessTools(session, calendar),
                gmail=gmail,
            )
            return ExecutionService(session, build_graph(dependencies, app.state.checkpointer))

        def execution_service_factory() -> ExecutionService:
            return build_execution_service(app.state.email_service.session)

        app.state.execution_service_factory = execution_service_factory
        scheduler = BackgroundScheduler()
        app.state.sync_scheduler = scheduler
        if settings.auto_sync_seconds > 0:
            def scheduled_sync() -> None:
                with database.session() as session:
                    try:
                        SyncService(
                            GoogleCredentialStore(session, get_settings()),
                            EmailService(session),
                            lambda: build_execution_service(session),
                        ).run_once()
                    except Exception:
                        logging.getLogger(__name__).exception("MailOps scheduled Gmail sync failed")

            scheduler.add_job(
                scheduled_sync,
                "interval",
                seconds=settings.auto_sync_seconds,
                id="gmail-incremental-sync",
                max_instances=1,
                coalesce=True,
                replace_existing=True,
            )
            scheduler.start()
        yield
        if scheduler.running:
            scheduler.shutdown(wait=False)
        app.state.email_service.session.close()
        app.state.checkpointer.conn.close()

    app = FastAPI(title="MailOps Agent", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    def health() -> dict[str, object]:
        settings = get_settings()
        return {
            "status": "ok",
            "configuration": {
                "google": settings.google_configured,
                "llm": settings.llm_configured,
            },
        }

    app.include_router(emails_router)
    app.include_router(approvals_router)
    app.include_router(dashboard_router)
    app.include_router(integrations_router)
    app.include_router(demo_router)
    app.include_router(runtime_router)
    return app


app = create_app()
