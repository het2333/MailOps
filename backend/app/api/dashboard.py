from fastapi import APIRouter, Request
from sqlalchemy import func, select

from app.db.models import AuditEvent, Email
from app.domain.schemas import EmailStatus

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("")
def dashboard(request: Request) -> dict[str, object]:
    session = request.app.state.email_service.session
    counts = {
        status.value: int(session.scalar(select(func.count()).select_from(Email).where(Email.status == status)) or 0)
        for status in EmailStatus
    }
    activity = session.scalars(select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(8)).all()
    return {
        "counts": counts,
        "activity": [{"type": item.event_type, "detail": item.detail, "created_at": item.created_at} for item in activity],
    }
