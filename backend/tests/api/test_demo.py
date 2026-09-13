from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


SESSION_A = {"X-Demo-Session": "candidate_a1"}
SESSION_B = {"X-Demo-Session": "reviewer_b2"}


@pytest.fixture
def demo_client(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'demo.db'}")
    monkeypatch.setenv("DEMO_MODE", "true")
    with TestClient(create_app()) as client:
        yield client


def test_demo_catalog_and_runtime_describe_safe_external_behavior(demo_client: TestClient):
    runtime = demo_client.get("/api/runtime")
    scenarios = demo_client.get("/api/demo/scenarios", headers=SESSION_A)

    assert runtime.status_code == 200
    assert runtime.json()["mode"] == "demo"
    assert runtime.json()["delivery"] == "simulated"
    assert runtime.json()["evaluation"]["case_count"] == 12
    assert runtime.json()["evaluation"]["unsafe_auto_send_count"] == 0
    assert scenarios.status_code == 200
    assert {item["id"] for item in scenarios.json()} == {"order", "quotation", "meeting", "injection"}


def test_quotation_launch_pauses_and_approval_completes_without_external_send(demo_client: TestClient):
    launched = demo_client.post("/api/demo/scenarios/quotation", headers=SESSION_A)

    assert launched.status_code == 200
    assert launched.json()["status"] == "awaiting_approval"
    approvals = demo_client.get("/api/approvals", headers=SESSION_A).json()
    assert len(approvals) == 1

    completed = demo_client.post(
        f"/api/approvals/{approvals[0]['id']}/decision",
        headers=SESSION_A,
        json={"decision": "approve"},
    )

    assert completed.status_code == 200
    assert completed.json()["status"] == "completed"
    detail = demo_client.get(f"/api/emails/{launched.json()['id']}", headers=SESSION_A).json()
    assert detail["execution"]["status"] == "completed"
    assert detail["execution"]["gmail_sent_message_id"].startswith("demo-sent-")


def test_demo_launch_is_idempotent_and_sessions_are_isolated(demo_client: TestClient):
    first = demo_client.post("/api/demo/scenarios/order", headers=SESSION_A).json()
    second = demo_client.post("/api/demo/scenarios/order", headers=SESSION_A).json()
    other = demo_client.post("/api/demo/scenarios/injection", headers=SESSION_B).json()

    assert first["id"] == second["id"]
    assert [item["id"] for item in demo_client.get("/api/emails", headers=SESSION_A).json()] == [first["id"]]
    assert [item["id"] for item in demo_client.get("/api/emails", headers=SESSION_B).json()] == [other["id"]]
    assert demo_client.get(f"/api/emails/{other['id']}", headers=SESSION_A).status_code == 404


def test_demo_reset_removes_only_calling_session(demo_client: TestClient):
    demo_client.post("/api/demo/scenarios/order", headers=SESSION_A)
    demo_client.post("/api/demo/scenarios/meeting", headers=SESSION_B)

    response = demo_client.post("/api/demo/reset", headers=SESSION_A)

    assert response.status_code == 200
    assert response.json() == {"deleted": 1}
    assert demo_client.get("/api/emails", headers=SESSION_A).json() == []
    assert len(demo_client.get("/api/emails", headers=SESSION_B).json()) == 1


def test_demo_routes_validate_session_and_disable_google_actions(demo_client: TestClient):
    assert demo_client.get("/api/emails").status_code == 422
    assert demo_client.get("/api/emails", headers={"X-Demo-Session": "bad"}).status_code == 422
    assert demo_client.post("/api/integrations/google/connect", headers=SESSION_A).status_code == 409
    assert demo_client.post("/api/integrations/sync", headers=SESSION_A).status_code == 409
