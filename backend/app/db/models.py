from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.domain.schemas import ApprovalStatus, EmailStatus, ExecutionStatus, Intent


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Email(Base):
    __tablename__ = "emails"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    gmail_message_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    gmail_thread_id: Mapped[str] = mapped_column(String(255), index=True)
    sender: Mapped[str] = mapped_column(String(320))
    subject: Mapped[str] = mapped_column(String(998), default="")
    body: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[EmailStatus] = mapped_column(Enum(EmailStatus), default=EmailStatus.NEEDS_ATTENTION)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    execution: Mapped["Execution"] = relationship(back_populates="email", uselist=False, cascade="all, delete-orphan")


class Execution(Base):
    __tablename__ = "executions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    email_id: Mapped[UUID] = mapped_column(ForeignKey("emails.id"), unique=True, index=True)
    status: Mapped[ExecutionStatus] = mapped_column(Enum(ExecutionStatus), default=ExecutionStatus.QUEUED)
    current_node: Mapped[str] = mapped_column(String(100), default="received")
    intent: Mapped[Intent | None] = mapped_column(Enum(Intent), nullable=True)
    confidence: Mapped[float | None] = mapped_column(nullable=True)
    draft_reply: Mapped[str | None] = mapped_column(Text, nullable=True)
    tool_result: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    risk_reasons: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    graph_thread_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    send_marker: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    gmail_sent_message_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    email: Mapped[Email] = relationship(back_populates="execution")
    approvals: Mapped[list["Approval"]] = relationship(back_populates="execution", cascade="all, delete-orphan")


class Approval(Base):
    __tablename__ = "approvals"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    execution_id: Mapped[UUID] = mapped_column(ForeignKey("executions.id"), index=True)
    status: Mapped[ApprovalStatus] = mapped_column(Enum(ApprovalStatus), default=ApprovalStatus.PENDING)
    draft_reply: Mapped[str] = mapped_column(Text)
    action_summary: Mapped[str] = mapped_column(Text)
    risk_reasons: Mapped[list[str]] = mapped_column(JSON, default=list)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    edited_reply: Mapped[str | None] = mapped_column(Text, nullable=True)

    execution: Mapped[Execution] = relationship(back_populates="approvals")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    email_id: Mapped[UUID] = mapped_column(ForeignKey("emails.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(100))
    detail: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    po_number: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    customer_name: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(100))
    delivery_date: Mapped[str] = mapped_column(String(50))
    tracking_number: Mapped[str] = mapped_column(String(255))


class Product(Base):
    __tablename__ = "products"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    model_code: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3), default="USD")


class KnowledgeArticle(Base):
    __tablename__ = "knowledge_articles"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(Text)
    keywords: Mapped[str] = mapped_column(String(500))


class IntegrationState(Base):
    __tablename__ = "integration_state"
    __table_args__ = (UniqueConstraint("provider", name="uq_integration_provider"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    provider: Mapped[str] = mapped_column(String(100))
    sync_cursor: Mapped[str | None] = mapped_column(String(255), nullable=True)
    account_email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    credential_blob: Mapped[bytes | None] = mapped_column(nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
