from fastapi import APIRouter, Request


router = APIRouter(prefix="/api/runtime", tags=["runtime"])

RELIABILITY_EVIDENCE = [
    {"id": "checkpoint_resume", "label": "Durable approval recovery", "verified_by": "pytest: tests/reliability/test_recovery.py"},
    {"id": "deduplicated_ingest", "label": "Duplicate message suppression", "verified_by": "pytest: tests/services/test_email_service.py"},
    {"id": "single_send", "label": "Single-send guard", "verified_by": "pytest: tests/workflow/test_graph.py"},
    {"id": "bounded_retry", "label": "Bounded transient retries", "verified_by": "pytest: tests/core/test_retry.py"},
]


@router.get("")
def runtime(request: Request) -> dict[str, object]:
    demo = request.app.state.settings.demo_mode
    return {
        "mode": "demo" if demo else "live",
        "delivery": "simulated" if demo else "gmail",
        "calendar": "simulated" if demo else "google_calendar",
        "description": "External delivery is simulated; workflow state and approvals are persisted." if demo else "Connected external services execute real actions.",
        "reliability": RELIABILITY_EVIDENCE,
        "evaluation": None,
    }
