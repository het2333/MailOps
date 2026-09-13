import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.models import Approval, Email, Execution
from app.db.seed import seed_business_data
from app.main import create_app
from app.providers.demo import DemoCalendarProvider, DemoGmailProvider, DemoTriageClient
from app.services.business_tools import BusinessTools
from app.services.execution_service import ExecutionService
from app.workflow.checkpoints import sqlite_checkpointer
from app.workflow.graph import WorkflowDependencies, build_graph


class CountingGmail(DemoGmailProvider):
    def __init__(self):
        self.send_count = 0

    def send_reply(self, **kwargs: str) -> str:
        self.send_count += 1
        return super().send_reply(**kwargs)


def _graph(session, database_url: str, gmail: CountingGmail):
    saver = sqlite_checkpointer(database_url)
    graph = build_graph(
        WorkflowDependencies(
            session=session,
            triage=DemoTriageClient(),
            tools=BusinessTools(session, DemoCalendarProvider()),
            gmail=gmail,
        ),
        saver,
    )
    return graph, saver


def test_approval_resumes_from_sqlite_checkpoint_after_service_reconstruction(tmp_path: Path):
    database_url = f"sqlite:///{tmp_path / 'recovery.db'}"
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    first_session = Session()
    seed_business_data(first_session)
    email = Email(
        gmail_message_id="recover-quote",
        gmail_thread_id="recover-thread",
        sender="buyer@example.com",
        subject="Pricing request",
        body="Please quote 25 units of MODEL-X",
    )
    first_session.add(email)
    first_session.flush()
    first_session.add(Execution(email_id=email.id))
    first_session.commit()
    gmail = CountingGmail()
    first_graph, first_saver = _graph(first_session, database_url, gmail)

    waiting = ExecutionService(first_session, first_graph).start(email.id)
    approval_id = first_session.scalar(select(Approval.id))
    assert waiting.status.value == "waiting_for_approval"
    first_session.close()
    first_saver.conn.close()

    second_session = Session()
    second_graph, second_saver = _graph(second_session, database_url, gmail)
    completed = ExecutionService(second_session, second_graph).resume(approval_id, "approve")

    assert completed.status.value == "completed"
    assert gmail.send_count == 1
    second_session.close()
    second_saver.conn.close()


def test_runtime_publishes_versioned_reliability_evidence(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'runtime.db'}")
    monkeypatch.setenv("DEMO_MODE", "true")
    with TestClient(create_app()) as client:
        evidence = client.get("/api/runtime").json()["reliability"]

    assert {item["id"] for item in evidence} == {
        "checkpoint_resume",
        "deduplicated_ingest",
        "single_send",
        "bounded_retry",
    }
    assert all(item["verified_by"].startswith("pytest:") for item in evidence)


def test_app_closes_checkpoint_connection_on_shutdown(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'shutdown.db'}")
    monkeypatch.setenv("DEMO_MODE", "true")
    with TestClient(create_app()) as client:
        saver = client.app.state.checkpointer
        saver.conn.execute("SELECT 1")

    with pytest.raises(sqlite3.ProgrammingError, match="closed database"):
        saver.conn.execute("SELECT 1")
