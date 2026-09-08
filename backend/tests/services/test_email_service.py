from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.domain.schemas import InboundMessage
from app.services.email_service import EmailService


def test_ingesting_the_same_gmail_message_twice_returns_one_email():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    service = EmailService(session)

    inbound = InboundMessage(
        gmail_message_id="g-001",
        gmail_thread_id="t-1",
        sender="buyer@example.com",
        subject="Status?",
        body="Could you check PO-001?",
    )
    first = service.ingest(inbound)
    second = service.ingest(inbound)

    assert first.id == second.id
    assert service.count_emails() == 1
