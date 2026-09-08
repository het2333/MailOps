import json
from typing import Any

from google.oauth2.credentials import Credentials
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.security import GoogleCredentialCipher
from app.db.models import IntegrationState

GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/calendar",
]


class GoogleCredentialStore:
    def __init__(self, session: Session, settings: Settings):
        self.session = session
        self.settings = settings

    def _cipher(self) -> GoogleCredentialCipher:
        if not self.settings.token_encryption_key:
            raise RuntimeError("TOKEN_ENCRYPTION_KEY is required before connecting Google")
        return GoogleCredentialCipher(self.settings.token_encryption_key.get_secret_value())

    def state(self) -> IntegrationState | None:
        return self.session.scalar(select(IntegrationState).where(IntegrationState.provider == "google"))

    def credentials(self) -> Credentials:
        state = self.state()
        if state is None or state.credential_blob is None:
            raise RuntimeError("Google account is not connected")
        return Credentials.from_authorized_user_info(self._cipher().decrypt(state.credential_blob), GOOGLE_SCOPES)

    def save(self, credentials: Credentials, account_email: str) -> IntegrationState:
        state = self.state() or IntegrationState(provider="google")
        state.account_email = account_email
        state.credential_blob = self._cipher().encrypt(json.loads(credentials.to_json()))
        self.session.add(state)
        self.session.commit()
        return state

    def save_cursor(self, cursor: str | None) -> None:
        state = self.state()
        if state is None:
            raise RuntimeError("Google account is not connected")
        state.sync_cursor = cursor
        self.session.commit()
