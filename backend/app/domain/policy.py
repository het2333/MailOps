from pydantic import BaseModel

from app.domain.schemas import Intent


class RiskDecision(BaseModel):
    requires_approval: bool
    reasons: list[str]


def evaluate_risk(intent: Intent, confidence: float, tool_ok: bool) -> RiskDecision:
    """Keep irreversible customer-facing actions behind a human decision."""

    reasons: list[str] = []
    if intent in {Intent.QUOTATION, Intent.MEETING}:
        reasons.append(f"{intent.value} requires human approval")
    if intent in {Intent.OTHER, Intent.SPAM}:
        reasons.append(f"{intent.value} cannot be automatically replied to")
    if confidence < 0.8:
        reasons.append("classification confidence is below 0.80")
    if not tool_ok:
        reasons.append("business tool could not verify the requested information")
    return RiskDecision(requires_approval=bool(reasons), reasons=reasons)
