import json
from typing import Any

from cryptography.fernet import Fernet


class GoogleCredentialCipher:
    """Encrypts OAuth credentials before they enter SQLite."""

    def __init__(self, key: bytes | str):
        self.fernet = Fernet(key)

    def encrypt(self, values: dict[str, Any]) -> bytes:
        return self.fernet.encrypt(json.dumps(values).encode("utf-8"))

    def decrypt(self, blob: bytes) -> dict[str, Any]:
        return json.loads(self.fernet.decrypt(blob).decode("utf-8"))
