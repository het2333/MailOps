import argparse
import json
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

EVAL_DIR = Path(__file__).resolve().parent
BACKEND_ROOT = EVAL_DIR.parent
REPO_ROOT = BACKEND_ROOT.parent
sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import get_settings
from app.domain.policy import evaluate_risk
from app.domain.schemas import Intent
from app.providers.demo import DemoTriageClient
from app.providers.llm import DeepSeekTriageClient


def nearest_rank_percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, math.ceil(percentile * len(ordered)) - 1)
    return ordered[index]


def evaluate_cases(cases: list[dict[str, Any]], classifier, provider_label: str) -> dict[str, Any]:
    outcomes: list[dict[str, Any]] = []
    latencies: list[float] = []
    expected_reviews = 0
    caught_reviews = 0
    unsafe_auto_sends = 0
    intent_matches = 0
    argument_matches = 0
    for case in cases:
        started = time.perf_counter()
        prediction = classifier.classify(case["subject"], case["body"])
        latency_ms = round((time.perf_counter() - started) * 1000, 3)
        latencies.append(latency_ms)
        decision = evaluate_risk(prediction.intent, prediction.confidence, bool(case["tool_ok"]))
        intent_match = prediction.intent.value == case["expected_intent"]
        argument_match = prediction.arguments == case["expected_arguments"]
        expected_review = bool(case["expected_review"])
        if intent_match:
            intent_matches += 1
        if argument_match:
            argument_matches += 1
        if expected_review:
            expected_reviews += 1
            if decision.requires_approval:
                caught_reviews += 1
            else:
                unsafe_auto_sends += 1
        outcomes.append({
            "id": case["id"],
            "predicted_intent": prediction.intent.value,
            "predicted_arguments": prediction.arguments,
            "requires_review": decision.requires_approval,
            "intent_match": intent_match,
            "argument_match": argument_match,
            "latency_ms": latency_ms,
        })
    count = len(cases)
    return {
        "dataset_version": "2026-09-14.1",
        "provider": provider_label,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "case_count": count,
            "intent_accuracy": round(intent_matches / count, 4) if count else 0.0,
            "argument_exact_match": round(argument_matches / count, 4) if count else 0.0,
            "human_review_recall": round(caught_reviews / expected_reviews, 4) if expected_reviews else 1.0,
            "unsafe_auto_send_count": unsafe_auto_sends,
            "latency_p50_ms": nearest_rank_percentile(latencies, 0.5),
            "latency_p95_ms": nearest_rank_percentile(latencies, 0.95),
        },
        "cases": outcomes,
    }


def render_markdown(result: dict[str, Any], *, command: str) -> str:
    summary = result["summary"]
    percent = lambda value: f"{value * 100:.1f}%"
    return f"""# MailOps evaluation report

Generated: {result['generated_at']}  
Dataset: `{result['dataset_version']}`  
Provider: `{result['provider']}`  
Command: `{command}`

| Metric | Result |
| --- | ---: |
| Evaluated cases | {summary['case_count']} |
| Intent accuracy | {percent(summary['intent_accuracy'])} |
| Argument exact match | {percent(summary['argument_exact_match'])} |
| Human-review recall | {percent(summary['human_review_recall'])} |
| Unsafe auto-send count | {summary['unsafe_auto_send_count']} |
| Classification latency p50 | {summary['latency_p50_ms']:.3f} ms |
| Classification latency p95 | {summary['latency_p95_ms']:.3f} ms |

## Interpretation

This public benchmark checks routing, literal argument extraction, and policy escalation on synthetic business emails. The deterministic demo provider makes the committed result reproducible in CI and does not measure Gmail delivery, Google Calendar availability, real-model drift, production latency, or private customer data. Run the same dataset with `--provider deepseek` to benchmark the configured real model separately.
"""


def load_cases(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate MailOps triage and safety policy")
    parser.add_argument("--provider", choices=("demo", "deepseek"), default="demo")
    parser.add_argument("--cases", type=Path, default=EVAL_DIR / "cases.jsonl")
    parser.add_argument("--output", type=Path, default=EVAL_DIR / "latest-results.json")
    parser.add_argument("--report", type=Path, default=REPO_ROOT / "docs" / "evaluation-report.md")
    args = parser.parse_args()
    classifier = DemoTriageClient() if args.provider == "demo" else DeepSeekTriageClient(get_settings())
    provider_label = "deterministic-demo" if args.provider == "demo" else get_settings().llm_model
    result = evaluate_cases(load_cases(args.cases), classifier, provider_label)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    command = f"uv run python evals/run_evaluation.py --provider {args.provider}"
    args.report.write_text(render_markdown(result, command=command))
    print(json.dumps(result["summary"], indent=2))


if __name__ == "__main__":
    main()
