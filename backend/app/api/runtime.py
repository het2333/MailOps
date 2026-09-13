from fastapi import APIRouter, Request


router = APIRouter(prefix="/api/runtime", tags=["runtime"])


@router.get("")
def runtime(request: Request) -> dict[str, object]:
    demo = request.app.state.settings.demo_mode
    return {
        "mode": "demo" if demo else "live",
        "delivery": "simulated" if demo else "gmail",
        "calendar": "simulated" if demo else "google_calendar",
        "description": "External delivery is simulated; workflow state and approvals are persisted." if demo else "Connected external services execute real actions.",
        "reliability": [],
        "evaluation": None,
    }
