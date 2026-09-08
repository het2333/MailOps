from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.domain.schemas import InboundMessage
from app.main import create_app


@pytest.fixture
def client(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'mailops-test.db'}")
    with TestClient(create_app()) as test_client:
        yield test_client


def test_email_detail_endpoint_returns_persisted_message_and_execution(client: TestClient):
    email = client.app.state.email_service.ingest(
        InboundMessage(
            gmail_message_id="g-002",
            gmail_thread_id="t-2",
            sender="buyer@example.com",
            subject="PO-002 delivery update",
            body="Where is PO-002?",
        )
    )

    response = client.get(f"/api/emails/{email.id}")

    assert response.status_code == 200
    assert response.json()["subject"] == "PO-002 delivery update"
    assert response.json()["execution"] is not None
