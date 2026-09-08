from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from langgraph.checkpoint.memory import MemorySaver

from app.db.base import Base
from app.db.models import Approval, Email, Execution
from app.db.seed import seed_business_data
from app.domain.schemas import Intent
from app.services.business_tools import BusinessTools
from app.services.execution_service import ExecutionService
from app.workflow.graph import WorkflowDependencies, build_graph
from app.workflow.state import TriageResult


class FakeCalendar:
    def list_free_slots(self, _request: str) -> list[str]:
        return ["2026-09-09T14:00:00+00:00"]

    def create_event(self, _request: str) -> str:
        return "event-1"


class QuoteTriage:
    def classify(self, _subject: str, _body: str) -> TriageResult:
        return TriageResult(intent=Intent.QUOTATION, confidence=0.96, rationale="quote", arguments={"model_code": "MODEL-X", "quantity": 100})


class FakeGmail:
    def send_reply(self, **_kwargs: str) -> str:
        return "sent-1"


def test_service_resumes_the_existing_approval_checkpoint():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    seed_business_data(session)
    email = Email(gmail_message_id="g-service", gmail_thread_id="t-service", sender="buyer@example.com", subject="Quote", body="100 MODEL-X")
    session.add(email)
    session.flush()
    session.add(Execution(email_id=email.id, graph_thread_id=str(email.id)))
    session.commit()
    graph = build_graph(
        WorkflowDependencies(session=session, triage=QuoteTriage(), tools=BusinessTools(session, FakeCalendar()), gmail=FakeGmail()),
        checkpointer=MemorySaver(),
    )
    service = ExecutionService(session, graph)

    waiting = service.start(email.id)
    approval = session.scalar(select(Approval))
    completed = service.resume(approval.id, "approve")

    assert waiting.status.value == "waiting_for_approval"
    assert completed.status.value == "completed"
