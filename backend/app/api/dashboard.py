from fastapi import APIRouter, Request
from sqlalchemy import func, select

from app.db.models import AuditEvent, Email
from app.domain.schemas import EmailStatus
from app.services.demo_service import demo_prefix

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("")
def dashboard(request: Request) -> dict[str, object]:
    session = request.app.state.email_service.session
    prefix = demo_prefix(request)
    counts = {}
    for status in EmailStatus:
        statement = select(func.count()).select_from(Email).where(Email.status == status)
        if prefix is not None:
            statement = statement.where(Email.gmail_message_id.startswith(prefix))
        counts[status.value] = int(session.scalar(statement) or 0)
    activity_statement = select(AuditEvent).join(Email, AuditEvent.email_id == Email.id).order_by(AuditEvent.created_at.desc()).limit(8)
    if prefix is not None:
        activity_statement = activity_statement.where(Email.gmail_message_id.startswith(prefix))
    activity = session.scalars(activity_statement).all()
    return {
        "counts": counts,
        "activity": [{"type": item.event_type, "detail": item.detail, "created_at": item.created_at} for item in activity],
    }
