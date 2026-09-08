from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app


def test_startup_registers_a_non_overlapping_gmail_sync_job_when_enabled(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'mailops-test.db'}")
    monkeypatch.setenv("AUTO_SYNC_SECONDS", "60")

    with TestClient(create_app()) as client:
        scheduler = client.app.state.sync_scheduler
        job = scheduler.get_job("gmail-incremental-sync")

        assert job is not None
        assert job.max_instances == 1
