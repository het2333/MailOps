from typing import Any, Protocol, TypedDict

from pydantic import BaseModel, Field

from app.domain.schemas import Intent


class TriageResult(BaseModel):
    intent: Intent
    confidence: float = Field(ge=0, le=1)
    rationale: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class TriageClient(Protocol):
    def classify(self, subject: str, body: str) -> TriageResult: ...


class MailOpsState(TypedDict, total=False):
    email_id: str
    execution_id: str
    gmail_thread_id: str
    sender: str
    subject: str
    body: str
    intent: str
    confidence: float
    rationale: str
    arguments: dict[str, Any]
    tool_result: dict[str, Any]
    tool_ok: bool
    draft_reply: str
    requires_approval: bool
    risk_reasons: list[str]
    approval_id: str
    decision: str
    send_outcome: dict[str, Any]
    error_message: str
