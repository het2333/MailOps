from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.db.models import Email, Execution
from app.domain.schemas import EmailDetail, EmailStatus, EmailSummary, ExecutionStatus, ExecutionView, InboundMessage


class EmailService:
    """Persists mailbox records and presents them to API consumers."""

    def __init__(self, session: Session, gmail_id_prefix: str | None = None):
        self.session = session
        self.gmail_id_prefix = gmail_id_prefix

    def _scope(self, statement):
        if self.gmail_id_prefix is not None:
            statement = statement.where(Email.gmail_message_id.startswith(self.gmail_id_prefix))
        return statement

    def ingest(self, inbound: InboundMessage) -> Email:
        existing = self.session.scalar(select(Email).where(Email.gmail_message_id == inbound.gmail_message_id))
        if existing is not None:
            return existing

        email = Email(
            gmail_message_id=inbound.gmail_message_id,
            gmail_thread_id=inbound.gmail_thread_id,
            sender=inbound.sender,
            subject=inbound.subject,
            body=inbound.body,
            received_at=inbound.received_at or None,
        )
        self.session.add(email)
        self.session.flush()
        self.session.add(Execution(email_id=email.id, status=ExecutionStatus.QUEUED, current_node="received"))
        self.session.commit()
        self.session.refresh(email)
        return email

    def count_emails(self) -> int:
        return int(self.session.scalar(self._scope(select(func.count()).select_from(Email))) or 0)

    def list_emails(self, status: EmailStatus | None = None) -> list[EmailSummary]:
        statement = select(Email).options(selectinload(Email.execution)).order_by(Email.received_at.desc())
        if status is not None:
            statement = statement.where(Email.status == status)
        statement = self._scope(statement)
        emails = self.session.scalars(statement).all()
        return [self._summary(email) for email in emails]

    def get_email(self, email_id: UUID) -> EmailDetail | None:
        statement = select(Email).options(selectinload(Email.execution)).where(Email.id == email_id)
        email = self.session.scalar(self._scope(statement))
        if email is None:
            return None
        return EmailDetail(
            id=email.id,
            sender=email.sender,
            subject=email.subject,
            status=email.status,
            received_at=email.received_at,
            gmail_thread_id=email.gmail_thread_id,
            body=email.body,
            execution=self._execution_view(email.execution),
            execution_status=email.execution.status if email.execution else None,
        )

    @staticmethod
    def _execution_view(execution: Execution | None) -> ExecutionView | None:
        if execution is None:
            return None
        return ExecutionView.model_validate(execution)

    def _summary(self, email: Email) -> EmailSummary:
        return EmailSummary(
            id=email.id,
            sender=email.sender,
            subject=email.subject,
            status=email.status,
            received_at=email.received_at,
            execution_status=email.execution.status if email.execution else None,
        )
