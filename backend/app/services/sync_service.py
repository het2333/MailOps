from pydantic import BaseModel

from app.providers.gmail import GmailProvider
from app.providers.google_credentials import GoogleCredentialStore
from app.services.email_service import EmailService


class SyncSummary(BaseModel):
    scanned: int
    ingested: int
    started: int
    cursor: str | None


class SyncService:
    def __init__(self, credential_store: GoogleCredentialStore, email_service: EmailService, execution_service_factory):
        self.credential_store = credential_store
        self.email_service = email_service
        self.execution_service_factory = execution_service_factory

    def run_once(self) -> SyncSummary:
        credentials = self.credential_store.credentials()
        provider = GmailProvider(credentials)
        state = self.credential_store.state()
        result = provider.sync_since(state.sync_cursor if state else None)
        ingested = 0
        started = 0
        for message in result.messages:
            if result.account_email.lower() in message.sender.lower():
                continue
            before = self.email_service.count_emails()
            email = self.email_service.ingest(message)
            if self.email_service.count_emails() != before:
                ingested += 1
                self.execution_service_factory().start(email.id)
                started += 1
        self.credential_store.save_cursor(result.cursor)
        return SyncSummary(scanned=len(result.messages), ingested=ingested, started=started, cursor=result.cursor)
