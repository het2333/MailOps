from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.models import Approval, Email, Execution
from app.domain.schemas import ApprovalDecisionRequest, ApprovalStatus, ApprovalView, ExecutionView
from app.services.demo_service import demo_prefix

router = APIRouter(prefix="/api/approvals", tags=["approvals"])


def _view(approval: Approval) -> ApprovalView:
    return ApprovalView(
        id=approval.id,
        status=approval.status,
        draft_reply=approval.draft_reply,
        action_summary=approval.action_summary,
        risk_reasons=approval.risk_reasons,
        email_id=approval.execution.email_id,
        email_subject=approval.execution.email.subject,
        email_sender=approval.execution.email.sender,
    )


@router.get("", response_model=list[ApprovalView])
def list_approvals(request: Request, status: ApprovalStatus = ApprovalStatus.PENDING) -> list[ApprovalView]:
    session = request.app.state.email_service.session
    statement = (
        select(Approval)
        .join(Approval.execution)
        .join(Execution.email)
        .options(selectinload(Approval.execution).selectinload(Execution.email))
        .where(Approval.status == status)
        .order_by(Approval.id.desc())
    )
    prefix = demo_prefix(request)
    if prefix is not None:
        statement = statement.where(Email.gmail_message_id.startswith(prefix))
    approvals = session.scalars(statement).all()
    return [_view(approval) for approval in approvals]


@router.post("/{approval_id}/decision", response_model=ExecutionView)
def decide_approval(approval_id: UUID, payload: ApprovalDecisionRequest, request: Request) -> ExecutionView:
    if payload.decision not in {"approve", "reject", "edit_and_approve"}:
        raise HTTPException(status_code=422, detail="Unsupported approval decision")
    prefix = demo_prefix(request)
    if prefix is not None:
        approval = request.app.state.email_service.session.get(Approval, approval_id)
        if approval is None or not approval.execution.email.gmail_message_id.startswith(prefix):
            raise HTTPException(status_code=404, detail="Approval not found")
    try:
        return request.app.state.execution_service_factory().resume(
            approval_id, payload.decision, payload.edited_reply
        )
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except (RuntimeError, ValueError) as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
