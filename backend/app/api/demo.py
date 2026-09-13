from fastapi import APIRouter, HTTPException, Request

from app.domain.schemas import EmailDetail
from app.services.demo_service import DemoService, SCENARIOS, demo_session


router = APIRouter(prefix="/api/demo", tags=["demo"])


def _require_demo(request: Request) -> str:
    if not request.app.state.settings.demo_mode:
        raise HTTPException(status_code=404, detail="Demo mode is disabled")
    return demo_session(request) or ""


@router.get("/scenarios")
def scenarios(request: Request) -> list[dict[str, str]]:
    _require_demo(request)
    return [scenario.public() for scenario in SCENARIOS.values()]


@router.post("/scenarios/{scenario_id}", response_model=EmailDetail)
def launch(scenario_id: str, request: Request) -> EmailDetail:
    session_id = _require_demo(request)
    try:
        return DemoService(request.app.state.email_service.session, request.app.state.execution_service_factory).launch(session_id, scenario_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/reset")
def reset(request: Request) -> dict[str, int]:
    session_id = _require_demo(request)
    deleted = DemoService(request.app.state.email_service.session, request.app.state.execution_service_factory).reset(session_id)
    return {"deleted": deleted}
