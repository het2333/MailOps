from pathlib import Path

from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

from app.core.security import GoogleCredentialCipher
from app.main import create_app


def test_stored_google_credentials_do_not_contain_refresh_token_plaintext():
    cipher = GoogleCredentialCipher(Fernet.generate_key())

    blob = cipher.encrypt({"refresh_token": "secret-refresh-token"})

    assert b"secret-refresh-token" not in blob
    assert cipher.decrypt(blob)["refresh_token"] == "secret-refresh-token"


def test_integration_status_is_honest_when_google_is_not_connected(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'mailops-test.db'}")
    with TestClient(create_app()) as client:
        response = client.get("/api/integrations/status")

    assert response.status_code == 200
    assert response.json()["connected"] is False
