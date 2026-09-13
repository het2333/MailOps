import hashlib
import re

from app.domain.schemas import Intent
from app.workflow.state import TriageResult


class DemoTriageClient:
    """Deterministic classifier for the public, external-call-free demo."""

    def classify(self, subject: str, body: str) -> TriageResult:
        text = f"{subject}\n{body}"
        lowered = text.lower()
        if any(phrase in lowered for phrase in ("ignore all previous", "disclose every customer", "忽略之前", "忽略以上", "所有客户")):
            return TriageResult(
                intent=Intent.OTHER,
                confidence=0.1,
                rationale="The message attempts to override policy and access unrelated customer data.",
                arguments={},
            )
        quote = re.search(r"(\d+)\s+units?\s+of\s+(MODEL-[A-Z0-9-]+)", text, re.IGNORECASE)
        if quote is None:
            quote = re.search(r"(\d+)\s*(?:件|个|台|套|单位)\s*(?:的\s*)?(MODEL-[A-Z0-9-]+)", text, re.IGNORECASE)
        if quote:
            return TriageResult(
                intent=Intent.QUOTATION,
                confidence=0.99,
                rationale="The customer requests a price for an explicit model and quantity.",
                arguments={"model_code": quote.group(2).upper(), "quantity": int(quote.group(1))},
            )
        order = re.search(r"\b(PO-[A-Z0-9-]+)\b", text, re.IGNORECASE)
        if order:
            return TriageResult(
                intent=Intent.ORDER_STATUS,
                confidence=0.99,
                rationale="The customer asks about an explicit purchase order.",
                arguments={"po_number": order.group(1).upper()},
            )
        if any(word in lowered for word in ("meeting", "calendar", "call next week", "会议", "日程", "下周沟通")):
            return TriageResult(
                intent=Intent.MEETING,
                confidence=0.97,
                rationale="The customer requests a meeting.",
                arguments={"request": body},
            )
        if any(word in lowered for word in ("warranty", "保修", "质保")):
            return TriageResult(
                intent=Intent.FAQ,
                confidence=0.98,
                rationale="The customer asks a supported warranty question.",
                arguments={},
            )
        if any(word in lowered for word in ("unsubscribe", "lottery", "退订", "彩票")):
            return TriageResult(intent=Intent.SPAM, confidence=0.98, rationale="The message is unsolicited spam.", arguments={})
        return TriageResult(intent=Intent.OTHER, confidence=0.4, rationale="No supported business intent was verified.", arguments={})


class DemoGmailProvider:
    """Records a deterministic outcome without contacting Gmail."""

    def send_reply(self, *, thread_id: str, to: str, subject: str, body: str) -> str:
        digest = hashlib.sha256(f"{thread_id}\0{to}\0{subject}\0{body}".encode()).hexdigest()[:16]
        return f"demo-sent-{digest}"


class DemoCalendarProvider:
    def list_free_slots(self, _request: str) -> list[str]:
        return [
            "2026-09-16T10:00:00+00:00",
            "2026-09-16T14:00:00+00:00",
            "2026-09-17T10:00:00+00:00",
        ]

    def create_event(self, request: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", request.lower()).strip("-")[:32]
        return f"demo-event-{slug or 'meeting'}"
