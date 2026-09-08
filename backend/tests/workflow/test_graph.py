from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from app.db.base import Base
from app.db.models import Approval, Email, Execution
from app.db.seed import seed_business_data
from app.domain.schemas import ApprovalStatus, Intent
from app.services.business_tools import BusinessTools
from app.workflow.graph import WorkflowDependencies, build_graph
from app.workflow.state import TriageResult


class FakeCalendar:
    def list_free_slots(self, _request: str) -> list[str]:
        return ["2026-09-09T14:00:00+00:00"]

    def create_event(self, _request: str) -> str:
        return "event-1"


class QuoteTriage:
    def classify(self, _subject: str, _body: str) -> TriageResult:
        return TriageResult(
            intent=Intent.QUOTATION,
            confidence=0.96,
            rationale="The customer asks for a product quantity and price.",
            arguments={"model_code": "MODEL-X", "quantity": 100},
        )


class FakeGmail:
    def __init__(self):
        self.sent_count = 0

    def send_reply(self, **_kwargs: str) -> str:
        self.sent_count += 1
        return f"sent-{self.sent_count}"


def test_quotation_interrupts_and_persists_approval():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    seed_business_data(session)
    email = Email(gmail_message_id="g-quote", gmail_thread_id="t-quote", sender="buyer@example.com", subject="Quote", body="100 MODEL-X")
    session.add(email)
    session.flush()
    execution = Execution(email_id=email.id, graph_thread_id=str(email.id))
    session.add(execution)
    session.commit()
    graph = build_graph(
        WorkflowDependencies(session=session, triage=QuoteTriage(), tools=BusinessTools(session, FakeCalendar()), gmail=FakeGmail()),
        checkpointer=MemorySaver(),
    )

    result = graph.invoke(
        {"email_id": str(email.id), "execution_id": str(execution.id), "subject": email.subject, "body": email.body, "sender": email.sender, "gmail_thread_id": email.gmail_thread_id},
        {"configurable": {"thread_id": str(email.id)}},
    )

    assert "__interrupt__" in result
    approval = session.scalar(select(Approval))
    assert approval is not None
    assert approval.status == ApprovalStatus.PENDING


def test_approval_resume_sends_once_and_marks_completed():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    seed_business_data(session)
    email = Email(gmail_message_id="g-quote-2", gmail_thread_id="t-quote-2", sender="buyer@example.com", subject="Quote", body="100 MODEL-X")
    session.add(email)
    session.flush()
    execution = Execution(email_id=email.id, graph_thread_id=str(email.id))
    session.add(execution)
    session.commit()
    gmail = FakeGmail()
    graph = build_graph(
        WorkflowDependencies(session=session, triage=QuoteTriage(), tools=BusinessTools(session, FakeCalendar()), gmail=gmail),
        checkpointer=MemorySaver(),
    )
    config = {"configurable": {"thread_id": str(email.id)}}
    graph.invoke(
        {"email_id": str(email.id), "execution_id": str(execution.id), "subject": email.subject, "body": email.body, "sender": email.sender, "gmail_thread_id": email.gmail_thread_id},
        config,
    )

    result = graph.invoke(Command(resume={"decision": "approve"}), config)

    assert result["send_outcome"]["sent"] is True
    assert gmail.sent_count == 1
    session.refresh(execution)
    assert execution.status.value == "completed"
