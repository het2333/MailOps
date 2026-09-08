import pytest

from app.domain.policy import evaluate_risk
from app.domain.schemas import Intent


@pytest.mark.parametrize(
    ("intent", "confidence", "tool_ok", "expected"),
    [
        (Intent.ORDER_STATUS, 0.95, True, False),
        (Intent.FAQ, 0.95, True, False),
        (Intent.QUOTATION, 0.99, True, True),
        (Intent.MEETING, 0.99, True, True),
        (Intent.ORDER_STATUS, 0.51, True, True),
        (Intent.FAQ, 0.99, False, True),
    ],
)
def test_risk_policy_selects_required_human_review(intent, confidence, tool_ok, expected):
    assert evaluate_risk(intent, confidence, tool_ok).requires_approval is expected
