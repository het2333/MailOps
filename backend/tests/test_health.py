from fastapi.testclient import TestClient

from app.main import create_app


def test_health_never_exposes_secret_values(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "private-value")

    response = TestClient(create_app()).get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["configuration"]["llm"] is True
    assert "private-value" not in response.text
