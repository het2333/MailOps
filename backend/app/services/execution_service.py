from typing import Literal
from uuid import UUID

from langgraph.types import Command
from sqlalchemy.orm import Session

from app.db.models import Approval, Execution
from app.domain.schemas import ApprovalStatus, ExecutionView


ApprovalDecision = Literal["approve", "reject", "edit_and_approve"]


class ExecutionService:
    """Starts and resumes exactly one durable graph thread per email."""

    def __init__(self, session: Session, graph):
        self.session = session
        self.graph = graph

    def start(self, email_id: UUID) -> ExecutionView:
        execution = self.session.query(Execution).filter(Execution.email_id == email_id).one_or_none()
        if execution is None:
            raise LookupError("No execution exists for this email")
        email = execution.email
        execution.graph_thread_id = str(email_id)
        self.session.commit()
        self.graph.invoke(
            {
                "email_id": str(email.id),
                "execution_id": str(execution.id),
                "gmail_thread_id": email.gmail_thread_id,
                "sender": email.sender,
                "subject": email.subject,
                "body": email.body,
            },
            {"configurable": {"thread_id": execution.graph_thread_id}},
        )
        self.session.refresh(execution)
        return ExecutionView.model_validate(execution)

    def resume(
        self,
        approval_id: UUID,
        decision: ApprovalDecision,
        edited_reply: str | None = None,
    ) -> ExecutionView:
        approval = self.session.get(Approval, approval_id)
        if approval is None:
            raise LookupError("Approval not found")
        if approval.status is not ApprovalStatus.PENDING:
            raise ValueError("Approval has already been resolved")
        if decision not in {"approve", "reject", "edit_and_approve"}:
            raise ValueError("Unsupported approval decision")
        execution = approval.execution
        if not execution.graph_thread_id:
            raise RuntimeError("Approval is missing its graph thread")
        payload: dict[str, str] = {"decision": decision}
        if edited_reply is not None:
            payload["edited_reply"] = edited_reply
        self.graph.invoke(Command(resume=payload), {"configurable": {"thread_id": execution.graph_thread_id}})
        self.session.refresh(execution)
        return ExecutionView.model_validate(execution)
