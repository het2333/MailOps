from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EmailStatus(StrEnum):
    NEEDS_ATTENTION = "needs_attention"
    AWAITING_APPROVAL = "awaiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"


class ExecutionStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    WAITING_FOR_APPROVAL = "waiting_for_approval"
    COMPLETED = "completed"
    REJECTED = "rejected"
    FAILED = "failed"


class ApprovalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Intent(StrEnum):
    ORDER_STATUS = "order_status"
    QUOTATION = "quotation"
    MEETING = "meeting"
    FAQ = "faq"
    SPAM = "spam"
    OTHER = "other"


class InboundMessage(BaseModel):
    gmail_message_id: str = Field(min_length=1)
    gmail_thread_id: str = Field(min_length=1)
    sender: str = Field(min_length=3)
    subject: str = ""
    body: str = ""
    received_at: datetime | None = None


class ExecutionView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: ExecutionStatus
    current_node: str
    intent: Intent | None = None
    confidence: float | None = None
    draft_reply: str | None = None
    tool_result: dict[str, Any] | None = None
    risk_reasons: list[str] | None = None
    error_message: str | None = None
    sent_at: datetime | None = None


class EmailSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    sender: str
    subject: str
    status: EmailStatus
    received_at: datetime
    execution_status: ExecutionStatus | None = None


class EmailDetail(EmailSummary):
    body: str
    gmail_thread_id: str
    execution: ExecutionView | None = None


class ApprovalDecisionRequest(BaseModel):
    decision: str
    edited_reply: str | None = None


class ApprovalView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: ApprovalStatus
    draft_reply: str
    action_summary: str
    risk_reasons: list[str]
    email_id: UUID
    email_subject: str
    email_sender: str
