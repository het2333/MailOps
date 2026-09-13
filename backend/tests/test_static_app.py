from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app


def test_compiled_frontend_is_served_without_shadowing_api(monkeypatch, tmp_path: Path):
    static_dir = tmp_path / "static"
    static_dir.mkdir()
    (static_dir / "index.html").write_text("<html><title>MailOps portfolio</title></html>")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'static.db'}")
    monkeypatch.setenv("DEMO_MODE", "true")
    monkeypatch.setenv("STATIC_DIR", str(static_dir))

    with TestClient(create_app()) as client:
        page = client.get("/")
        health = client.get("/api/health")

    assert page.status_code == 200
    assert "MailOps portfolio" in page.text
    assert health.status_code == 200
    assert health.json()["status"] == "ok"
