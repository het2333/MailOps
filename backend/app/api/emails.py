from uuid import UUID

from fastapi import APIRouter, HTTPException, Request

from app.domain.schemas import EmailDetail, EmailStatus, EmailSummary
from app.services.email_service import EmailService

router = APIRouter(prefix="/api/emails", tags=["emails"])


def email_service(request: Request) -> EmailService:
    return request.app.state.email_service


@router.get("", response_model=list[EmailSummary])
def list_emails(request: Request, status: EmailStatus | None = None) -> list[EmailSummary]:
    return email_service(request).list_emails(status)


@router.get("/{email_id}", response_model=EmailDetail)
def get_email(email_id: UUID, request: Request) -> EmailDetail:
    email = email_service(request).get_email(email_id)
    if email is None:
        raise HTTPException(status_code=404, detail="Email not found")
    return email
