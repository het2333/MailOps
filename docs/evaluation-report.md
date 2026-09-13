# MailOps evaluation report

Generated: 2026-09-13T20:00:33.659127+00:00  
Dataset: `2026-09-14.1`  
Provider: `deterministic-demo`  
Command: `uv run python evals/run_evaluation.py --provider demo`

| Metric | Result |
| --- | ---: |
| Evaluated cases | 12 |
| Intent accuracy | 100.0% |
| Argument exact match | 100.0% |
| Human-review recall | 100.0% |
| Unsafe auto-send count | 0 |
| Classification latency p50 | 0.003 ms |
| Classification latency p95 | 0.610 ms |

## Interpretation

This public benchmark checks routing, literal argument extraction, and policy escalation on synthetic business emails. The deterministic demo provider makes the committed result reproducible in CI and does not measure Gmail delivery, Google Calendar availability, real-model drift, production latency, or private customer data. Run the same dataset with `--provider deepseek` to benchmark the configured real model separately.
