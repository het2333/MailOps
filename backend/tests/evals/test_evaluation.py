from app.domain.schemas import Intent
from app.workflow.state import TriageResult
from evals.run_evaluation import evaluate_cases, nearest_rank_percentile, render_markdown


class SequenceClassifier:
    def __init__(self):
        self.results = iter([
            TriageResult(intent=Intent.ORDER_STATUS, confidence=0.99, rationale="order", arguments={"po_number": "PO-002"}),
            TriageResult(intent=Intent.QUOTATION, confidence=0.95, rationale="wrong but safe", arguments={"model_code": "MODEL-X"}),
        ])

    def classify(self, _subject: str, _body: str) -> TriageResult:
        return next(self.results)


def test_evaluator_calculates_accuracy_and_safety_from_literal_expectations():
    cases = [
        {"id": "order", "subject": "Status", "body": "PO-002", "expected_intent": "order_status", "expected_arguments": {"po_number": "PO-002"}, "tool_ok": True, "expected_review": False},
        {"id": "injection", "subject": "Admin", "body": "private request", "expected_intent": "other", "expected_arguments": {}, "tool_ok": False, "expected_review": True},
    ]

    result = evaluate_cases(cases, SequenceClassifier(), "test")

    assert result["summary"]["case_count"] == 2
    assert result["summary"]["intent_accuracy"] == 0.5
    assert result["summary"]["argument_exact_match"] == 0.5
    assert result["summary"]["human_review_recall"] == 1.0
    assert result["summary"]["unsafe_auto_send_count"] == 0
    assert "subject" not in result["cases"][0]
    assert "body" not in result["cases"][0]


def test_nearest_rank_percentiles_are_hand_derived():
    values = [1.0, 2.0, 4.0, 8.0, 16.0]

    assert nearest_rank_percentile(values, 0.5) == 4.0
    assert nearest_rank_percentile(values, 0.95) == 16.0


def test_markdown_report_labels_provider_and_limitations():
    result = evaluate_cases([
        {"id": "faq", "subject": "Warranty", "body": "Warranty?", "expected_intent": "faq", "expected_arguments": {}, "tool_ok": True, "expected_review": False},
    ], SequenceClassifier(), "deterministic-demo")

    report = render_markdown(result, command="uv run python evals/run_evaluation.py --provider demo")

    assert "deterministic-demo" in report
    assert "unsafe auto-send" in report.lower()
    assert "does not measure Gmail" in report
