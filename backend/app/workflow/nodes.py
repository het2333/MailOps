from datetime import datetime, timezone
from typing import Protocol
from uuid import UUID, uuid4

from langgraph.types import interrupt
from sqlalchemy.orm import Session

from app.core.retry import with_retry
from app.db.models import Approval, AuditEvent, Email, Execution
from app.domain.policy import evaluate_risk
from app.domain.schemas import ApprovalStatus, EmailStatus, ExecutionStatus, Intent
from app.services.business_tools import BusinessTools
from app.workflow.state import MailOpsState, TriageClient


class GmailPort(Protocol):
    def send_reply(self, *, thread_id: str, to: str, subject: str, body: str) -> str: ...


class WorkflowDependencies:
    def __init__(self, session: Session, triage: TriageClient, tools: BusinessTools, gmail: GmailPort):
        self.session = session
        self.triage = triage
        self.tools = tools
        self.gmail = gmail


def _execution(deps: WorkflowDependencies, state: MailOpsState) -> Execution:
    execution = deps.session.get(Execution, UUID(state["execution_id"]))
    if execution is None:
        raise RuntimeError("Execution no longer exists")
    return execution


def _email(deps: WorkflowDependencies, state: MailOpsState) -> Email:
    email = deps.session.get(Email, UUID(state["email_id"]))
    if email is None:
        raise RuntimeError("Email no longer exists")
    return email


def _save(deps: WorkflowDependencies) -> None:
    deps.session.commit()


def triage_email(deps: WorkflowDependencies, state: MailOpsState) -> MailOpsState:
    execution = _execution(deps, state)
    execution.status = ExecutionStatus.RUNNING
    execution.current_node = "triage_email"
    try:
        triage = with_retry(lambda: deps.triage.classify(state["subject"], state["body"]))
    except Exception as error:
        execution.status = ExecutionStatus.FAILED
        execution.error_message = str(error)
        _email(deps, state).status = EmailStatus.FAILED
        _save(deps)
        return {"error_message": str(error)}
    execution.intent = triage.intent
    execution.confidence = triage.confidence
    _save(deps)
    return {
        "intent": triage.intent.value,
        "confidence": triage.confidence,
        "rationale": triage.rationale,
        "arguments": triage.arguments,
    }


def execute_tool(deps: WorkflowDependencies, state: MailOpsState) -> MailOpsState:
    intent = Intent(state["intent"])
    arguments = state.get("arguments", {})
    execution = _execution(deps, state)
    execution.current_node = "execute_tool"
    if intent is Intent.ORDER_STATUS:
        result = deps.tools.get_order(str(arguments.get("po_number", "")))
    elif intent is Intent.QUOTATION:
        try:
            quantity = int(arguments.get("quantity", 0))
        except (TypeError, ValueError):
            quantity = 0
        result = deps.tools.get_quote(str(arguments.get("model_code", "")), quantity)
    elif intent is Intent.MEETING:
        result = with_retry(lambda: deps.tools.find_calendar_slots(str(arguments.get("request", state["body"]))))
    elif intent is Intent.FAQ:
        result = deps.tools.search_knowledge(state["body"])
    else:
        from app.services.business_tools import ToolResult

        result = ToolResult(ok=False, error="This email type has no automatic tool")
    execution.tool_result = result.data if result.ok else {"error": result.error}
    _save(deps)
    return {"tool_result": execution.tool_result, "tool_ok": result.ok}


def draft_reply(deps: WorkflowDependencies, state: MailOpsState) -> MailOpsState:
    intent = Intent(state["intent"])
    result = state.get("tool_result", {})
    if not state.get("tool_ok"):
        reply = "Thank you for your message. Our team is reviewing your request and will follow up shortly."
    elif intent is Intent.ORDER_STATUS:
        reply = (
            f"Thank you for your inquiry. Order {result['po_number']} is {result['status']}. "
            f"Expected delivery: {result['delivery_date']}. Tracking: {result['tracking_number']}."
        )
    elif intent is Intent.QUOTATION:
        reply = (
            f"Thank you for your request. Our quote for {result['quantity']} units of {result['model_code']} is "
            f"{result['currency']} {result['total']} (unit price {result['currency']} {result['unit_price']})."
        )
    elif intent is Intent.MEETING:
        reply = "Thank you for your request. The following times are available: " + ", ".join(result["slots"])
    elif intent is Intent.FAQ:
        reply = f"{result['body']}"
    else:
        reply = "Thank you for contacting us. Our team will follow up shortly."
    execution = _execution(deps, state)
    execution.current_node = "draft_reply"
    execution.draft_reply = reply
    _save(deps)
    return {"draft_reply": reply}


def risk_check(deps: WorkflowDependencies, state: MailOpsState) -> MailOpsState:
    decision = evaluate_risk(Intent(state["intent"]), state["confidence"], state.get("tool_ok", False))
    execution = _execution(deps, state)
    execution.current_node = "risk_check"
    execution.risk_reasons = decision.reasons
    _save(deps)
    return {"requires_approval": decision.requires_approval, "risk_reasons": decision.reasons}


def human_approval(deps: WorkflowDependencies, state: MailOpsState) -> MailOpsState:
    execution = _execution(deps, state)
    approval = next((item for item in execution.approvals if item.status is ApprovalStatus.PENDING), None)
    if approval is None:
        approval = Approval(
            execution_id=execution.id,
            draft_reply=state["draft_reply"],
            action_summary=f"{state['intent']} email to {state['sender']}",
            risk_reasons=state.get("risk_reasons", []),
        )
        deps.session.add(approval)
        execution.status = ExecutionStatus.WAITING_FOR_APPROVAL
        execution.current_node = "human_approval"
        _email(deps, state).status = EmailStatus.AWAITING_APPROVAL
        _save(deps)
    payload = interrupt(
        {
            "approval_id": str(approval.id),
            "draft_reply": approval.draft_reply,
            "action_summary": approval.action_summary,
            "risk_reasons": approval.risk_reasons,
        }
    )
    decision = payload.get("decision") if isinstance(payload, dict) else None
    if decision not in {"approve", "reject", "edit_and_approve"}:
        raise ValueError("Approval decision must be approve, reject, or edit_and_approve")
    if approval.status is not ApprovalStatus.PENDING:
        raise RuntimeError("Approval has already been resolved")
    if decision == "reject":
        approval.status = ApprovalStatus.REJECTED
        approval.resolved_at = datetime.now(timezone.utc)
        execution.status = ExecutionStatus.REJECTED
        execution.current_node = "rejected"
        _email(deps, state).status = EmailStatus.NEEDS_ATTENTION
        _save(deps)
        return {"approval_id": str(approval.id), "decision": decision}
    if decision == "edit_and_approve":
        edited_reply = str(payload.get("edited_reply", "")).strip()
        if not edited_reply:
            raise ValueError("An edited approval requires a non-empty reply")
        approval.edited_reply = edited_reply
        execution.draft_reply = edited_reply
    approval.status = ApprovalStatus.APPROVED
    approval.resolved_at = datetime.now(timezone.utc)
    execution.status = ExecutionStatus.RUNNING
    execution.current_node = "approved"
    _save(deps)
    return {"approval_id": str(approval.id), "decision": decision, "draft_reply": execution.draft_reply}


def approved_meeting_action(deps: WorkflowDependencies, state: MailOpsState) -> MailOpsState:
    if Intent(state["intent"]) is not Intent.MEETING:
        return {}
    result = deps.tools.create_calendar_event(str(state.get("arguments", {}).get("request", state["body"])))
    execution = _execution(deps, state)
    execution.current_node = "create_calendar_event"
    if not result.ok:
        execution.status = ExecutionStatus.FAILED
        execution.error_message = result.error
        _email(deps, state).status = EmailStatus.FAILED
        _save(deps)
        return {"error_message": result.error or "Calendar event creation failed"}
    tool_result = dict(state.get("tool_result", {}))
    tool_result["event_id"] = result.data["event_id"]
    execution.tool_result = tool_result
    _save(deps)
    return {"tool_result": tool_result}


def send_email(deps: WorkflowDependencies, state: MailOpsState) -> MailOpsState:
    execution = _execution(deps, state)
    if execution.gmail_sent_message_id:
        return {"send_outcome": {"sent": True, "message_id": execution.gmail_sent_message_id}}
    if execution.send_marker:
        execution.status = ExecutionStatus.FAILED
        execution.error_message = "A previous send attempt is unresolved; human review is required"
        _email(deps, state).status = EmailStatus.FAILED
        _save(deps)
        return {"send_outcome": {"sent": False, "error": execution.error_message}}
    execution.current_node = "send_email"
    execution.send_marker = str(uuid4())
    _save(deps)
    try:
        message_id = deps.gmail.send_reply(
            thread_id=state["gmail_thread_id"],
            to=state["sender"],
            subject=state["subject"],
            body=state["draft_reply"],
        )
    except Exception as error:
        execution.status = ExecutionStatus.FAILED
        execution.error_message = str(error)
        _email(deps, state).status = EmailStatus.FAILED
        _save(deps)
        return {"send_outcome": {"sent": False, "error": str(error)}}
    execution.gmail_sent_message_id = message_id
    execution.sent_at = datetime.now(timezone.utc)
    execution.status = ExecutionStatus.COMPLETED
    execution.current_node = "completed"
    _email(deps, state).status = EmailStatus.COMPLETED
    deps.session.add(AuditEvent(email_id=execution.email_id, event_type="gmail_reply_sent", detail={"message_id": message_id}))
    _save(deps)
    return {"send_outcome": {"sent": True, "message_id": message_id}}
