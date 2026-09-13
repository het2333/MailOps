# MailOps Job-Ready Demo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a safe public MailOps demo with a persisted end-to-end workflow, executable reliability evidence, a reproducible agent evaluation report, and deployable production assets.

**Architecture:** `DEMO_MODE` selects deterministic external adapters while preserving the same FastAPI, SQLAlchemy, SQLite, LangGraph, approval, and audit path used by real integrations. A scoped demo service accepts catalog scenarios only, the frontend drives those APIs, an evaluation runner measures the same classification and risk contracts, and one container serves both the API and compiled React app.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy, SQLite, LangGraph, pytest, React 18, TypeScript, Vite, Vitest, Docker, Render.

**Spec:** `docs/superpowers/specs/2026-09-14-job-ready-demo-design.md`

## Global Constraints

- Demo mode never initializes Google or DeepSeek clients and never contacts external recipients.
- Real mode never falls back to demo adapters.
- Demo messages use `example.com` recipients and catalog-defined content only.
- Browser session IDs scope all demo inbox, approval, dashboard, launch, and reset operations.
- Gmail delivery is never retried outside the provider because an accepted-but-unacknowledged send is ambiguous.
- Every new behavior follows red-green-refactor and all existing API contracts remain compatible in real mode.

---

### Task 1: Retry policy and deterministic external adapters

**Files:**
- Create: `backend/app/core/retry.py`
- Create: `backend/app/providers/demo.py`
- Create: `backend/tests/core/test_retry.py`
- Create: `backend/tests/providers/test_demo.py`
- Modify: `backend/app/workflow/nodes.py`

**Interfaces:**
- Produces: `with_retry(operation, attempts=3, base_delay=0.05, sleep=time.sleep)` and `DemoTriageClient`, `DemoGmailProvider`, `DemoCalendarProvider`.
- Consumes: `TriageResult`, `Intent`, and existing provider method signatures.

- [ ] **Step 1: Write failing retry and adapter tests** proving a transient operation succeeds on attempt three, exhaustion raises the final error, catalog messages produce literal expected intent/arguments, and demo delivery returns a stable `demo-sent-*` ID.
- [ ] **Step 2: Run `uv run pytest tests/core/test_retry.py tests/providers/test_demo.py -q`** and confirm imports fail because the modules do not exist.
- [ ] **Step 3: Implement the minimal retry loop and deterministic adapters**. Retry only classification and Calendar availability reads in workflow nodes; do not wrap `send_reply`.
- [ ] **Step 4: Run the focused tests and `uv run pytest tests/workflow -q`** and confirm they pass.
- [ ] **Step 5: Commit with `git commit -m "feat: add deterministic demo adapters and retries"`**.

### Task 2: Session-scoped demo workflow API

**Files:**
- Create: `backend/app/services/demo_service.py`
- Create: `backend/app/api/demo.py`
- Create: `backend/app/api/runtime.py`
- Create: `backend/tests/api/test_demo.py`
- Modify: `backend/app/core/config.py`
- Modify: `backend/app/services/email_service.py`
- Modify: `backend/app/api/emails.py`
- Modify: `backend/app/api/approvals.py`
- Modify: `backend/app/api/dashboard.py`
- Modify: `backend/app/api/integrations.py`
- Modify: `backend/app/main.py`

**Interfaces:**
- Consumes: Task 1 demo adapters and the existing `ExecutionService.start` and `resume` methods.
- Produces: `GET /api/runtime`, `GET /api/demo/scenarios`, `POST /api/demo/scenarios/{scenario_id}`, and `POST /api/demo/reset`.

- [ ] **Step 1: Write failing API tests** for scenario catalog, quotation pause, approval completion, idempotent launch, session A/B isolation, session reset, invalid session IDs, and Google endpoints being disabled in demo mode.
- [ ] **Step 2: Run `uv run pytest tests/api/test_demo.py -q`** and confirm route-not-found and isolation assertions fail.
- [ ] **Step 3: Add `demo_mode: bool = False` and session-scope helpers**. Prefix catalog Gmail IDs with `demo:{session}:`, filter existing queries by that prefix, and validate session IDs against `^[A-Za-z0-9_-]{8,64}$`.
- [ ] **Step 4: Implement catalog launch/reset and runtime routes**, inject demo adapters from `create_app`, and return the normal persisted `EmailDetail` after launch.
- [ ] **Step 5: Run focused API tests and the complete backend suite**.
- [ ] **Step 6: Commit with `git commit -m "feat: add session-scoped demo workflow"`**.

### Task 3: Durable reliability verification

**Files:**
- Create: `backend/tests/reliability/test_recovery.py`
- Modify: `backend/tests/workflow/test_graph.py`
- Modify: `backend/tests/services/test_sync_scheduler.py`
- Modify: `backend/app/api/runtime.py`

**Interfaces:**
- Consumes: SQLite checkpointer, execution graph, send marker, sync service, and Task 2 runtime contract.
- Produces: versioned reliability evidence entries returned by `/api/runtime`.

- [ ] **Step 1: Write failing recovery tests** that create a file-backed SQLite graph, pause a quotation, close its first service context, create a new graph/checkpointer, resume the approval, and assert one send and a completed execution.
- [ ] **Step 2: Add replay tests** asserting a completed execution returns its original message ID without calling Gmail and an unresolved marker returns a human-review error without calling Gmail.
- [ ] **Step 3: Run `uv run pytest tests/reliability tests/workflow/test_graph.py tests/services/test_sync_scheduler.py -q`** and confirm any missing recovery behavior or evidence fails.
- [ ] **Step 4: Make the smallest lifecycle/checkpointer fixes required**, close checkpoint contexts on shutdown, and expose evidence IDs `checkpoint_resume`, `deduplicated_ingest`, `single_send`, and `bounded_retry`.
- [ ] **Step 5: Run the focused tests and full backend suite**.
- [ ] **Step 6: Commit with `git commit -m "test: prove durable workflow reliability"`**.

### Task 4: Reproducible agent evaluation

**Files:**
- Create: `backend/evals/cases.jsonl`
- Create: `backend/evals/run_evaluation.py`
- Create: `backend/evals/latest-results.json`
- Create: `backend/tests/evals/test_evaluation.py`
- Create: `docs/evaluation-report.md`
- Modify: `backend/app/api/runtime.py`

**Interfaces:**
- Consumes: `DemoTriageClient`, optional `DeepSeekTriageClient`, `evaluate_risk`, and JSONL cases.
- Produces: `evaluate_cases(cases, classifier, provider_label) -> dict`, JSON results, Markdown report, and runtime evaluation summary.

- [ ] **Step 1: Write failing evaluator tests** with hand-derived expected metrics for correct/incorrect intents, argument matches, review recall, unsafe auto-send count, and nearest-rank p50/p95 latency.
- [ ] **Step 2: Run `uv run pytest tests/evals/test_evaluation.py -q`** and confirm the missing runner import fails.
- [ ] **Step 3: Implement JSONL loading, metric calculation, CLI provider selection, result JSON writing, and Markdown rendering** without storing full message bodies.
- [ ] **Step 4: Add at least twelve public fixtures** spanning all intents, business arguments, tool-risk expectations, and prompt injection.
- [ ] **Step 5: Run `uv run python evals/run_evaluation.py --provider demo`**, then run evaluator tests and verify the report values equal the JSON summary.
- [ ] **Step 6: Commit with `git commit -m "feat: add reproducible agent evaluation"`**.

### Task 5: Recruiter-facing frontend workflow

**Files:**
- Create: `frontend/src/components/DemoLauncher.tsx`
- Create: `frontend/src/components/EvidencePanel.tsx`
- Create: `frontend/src/components/DemoLauncher.test.tsx`
- Modify: `frontend/src/pages/WorkbenchPage.tsx`
- Modify: `frontend/src/pages/WorkbenchPage.test.tsx`
- Modify: `frontend/src/components/ConnectionBanner.tsx`
- Modify: `frontend/src/api/client.ts`
- Modify: `frontend/src/types/api.ts`
- Modify: `frontend/src/styles.css`

**Interfaces:**
- Consumes: Task 2 demo/runtime routes and existing email/approval contracts.
- Produces: session-scoped API headers, scenario actions, mode badge, reset control, evidence display, and mutation refresh behavior.

- [ ] **Step 1: Write failing component/page tests** that expect the Demo badge, scenario catalog, launch button, persisted launched email selection, evidence metrics, reset behavior, and a clear simulated-delivery notice.
- [ ] **Step 2: Run `npm run test -- --run`** and confirm the new UI expectations fail.
- [ ] **Step 3: Extend the central API client** with a generated stable demo session header and typed runtime/demo methods.
- [ ] **Step 4: Implement launcher/evidence components and page state**, then style desktop and mobile layouts with honest loading, error, empty, and success states.
- [ ] **Step 5: Run `npm run test -- --run` and `npm run build`**.
- [ ] **Step 6: Commit with `git commit -m "feat: add recruiter-facing demo experience"`**.

### Task 6: Single-container deployment and end-to-end proof

**Files:**
- Create: `Dockerfile`
- Create: `.dockerignore`
- Create: `render.yaml`
- Create: `backend/tests/test_static_app.py`
- Create: `frontend/e2e/demo-flow.spec.ts`
- Modify: `backend/app/main.py`
- Modify: `frontend/package.json`
- Modify: `.env.example`
- Modify: `README.md`

**Interfaces:**
- Consumes: compiled `frontend/dist`, Task 2 API, and Task 5 UI.
- Produces: a `PORT`-aware web container, SPA fallback, Render service definition, and browser-level workflow proof.

- [ ] **Step 1: Write a failing static-app test** expecting `/` to return the compiled shell when `STATIC_DIR` points to a fixture directory while `/api/health` remains JSON.
- [ ] **Step 2: Run the focused test** and confirm `/` returns 404.
- [ ] **Step 3: Implement conditional static mounting after API routes**, add Docker build stages and Render environment settings, and document demo/live/evaluation commands plus measured results.
- [ ] **Step 4: Build the frontend, run backend tests, and build the Docker image** tagged `mailops-demo:verify`.
- [ ] **Step 5: Run the container on an unused port and exercise health, scenario launch, quotation approval, page reload, and session isolation through HTTP and Playwright**.
- [ ] **Step 6: Deploy from the GitHub repository using available authenticated hosting, then verify the public `/api/health`, `/api/runtime`, and `/` responses**. If hosting authorization is unavailable, preserve `render.yaml` and record that exact blocker.
- [ ] **Step 7: Commit with `git commit -m "feat: package and document public demo"`**.

### Task 7: Final verification and publication

**Files:**
- Modify only files required by failures found during final verification.

**Interfaces:**
- Consumes: all prior tasks.
- Produces: a reviewed branch and synchronized GitHub repository.

- [ ] **Step 1: Run `uv run pytest -q` in `backend` and confirm zero failures**.
- [ ] **Step 2: Run `npm run test -- --run && npm run build` in `frontend` and confirm zero failures**.
- [ ] **Step 3: Run the deterministic evaluator and compare its generated report and JSON**.
- [ ] **Step 4: Run `git diff --check`, credential-pattern scanning, and inspect `git status --short`**.
- [ ] **Step 5: Use the finishing-a-development-branch workflow, merge the verified branch, push `main`, and verify the remote commit**.
