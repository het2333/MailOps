# MailOps job-ready demo design

## Goal

Upgrade MailOps from a tested MVP into a portfolio project that a recruiter can open, understand, and exercise without receiving Google credentials. The result must demonstrate a complete persisted workflow, measurable agent behavior, and failure handling while keeping the existing Gmail, Calendar, and DeepSeek production path available.

## Product modes

MailOps has two explicit runtime modes selected by `DEMO_MODE`.

- In real mode, the existing Google OAuth, Gmail, Calendar, and DeepSeek adapters remain authoritative. The application reports missing configuration honestly and never substitutes demo behavior.
- In demo mode, deterministic local adapters replace only the external Gmail, Calendar, and model calls. Emails, executions, approvals, tool queries, risk decisions, audit events, and dashboard reads still pass through FastAPI, SQLite, SQLAlchemy, and LangGraph.

The UI always shows the current mode. Demo actions use anonymous browser session IDs so one visitor does not see or modify another visitor's sample emails. The session ID is temporary UI state; all product records remain server-side. Demo recipients use reserved `example.com` addresses, and demo sends create auditable delivery records without contacting an external service.

## Demo workflow

The backend exposes a scenario catalog and a scenario launch endpoint. The catalog contains four representative cases: a low-risk order-status request that completes automatically, a quotation that pauses for approval, a meeting request that creates a simulated Calendar event only after approval, and a prompt-injection message that is routed to human attention.

Launching a scenario is idempotent within a demo session. It ingests an `InboundMessage` through `EmailService`, creates the normal `Execution`, and starts the normal LangGraph graph. The API returns the persisted email detail. A reset endpoint deletes only records belonging to that demo session and recreates no hidden browser fixtures.

Normal email, approval, dashboard, and audit queries apply the session scope when demo mode is active. Real mode remains single-account and ignores demo session headers.

## Reliability

External classification and read-only Calendar availability calls use a small retry utility with three total attempts and bounded exponential backoff. The workflow does not add an outer retry around Gmail delivery because a network failure after server acceptance is ambiguous. The existing durable send marker continues to stop a second delivery and forces human review for unresolved attempts.

Reliability is proved with executable tests for:

- duplicate scenario launch and duplicate Gmail synchronization;
- transient classification recovery and exhausted retry behavior;
- SQLite-checkpoint approval recovery after constructing a new graph and service instance;
- duplicate approval rejection;
- successful delivery replay returning the original Gmail message ID without sending again;
- unresolved send markers preventing delivery retries;
- session isolation for inbox, approvals, and dashboard data.

The public UI exposes a compact reliability evidence panel based on a versioned backend summary. The panel describes tested guarantees rather than claiming live infrastructure properties.

## Evaluation

Versioned JSONL fixtures cover all supported intents, required arguments, low-confidence unknown requests, tool failures, and prompt injection. A command-line evaluator runs the same triage and policy contracts used by the application. It supports `demo` for deterministic CI results and `deepseek` for an optional real-model benchmark when a key is configured.

The evaluator writes JSON with per-case outcomes and aggregate metrics: intent accuracy, argument exact-match rate, unsafe-auto-send count, human-review recall, latency p50/p95, and evaluated case count. A Markdown report records the command, dataset version, timestamp, environment label, limitations, and aggregate results. Generated results must never contain API keys or full private emails.

The committed report is produced from the deterministic public dataset so it is reproducible. A real-model run may be reported separately and must be labeled with its model name and run date.

## Frontend

The workbench adds a recruiter-oriented opening state with three clear actions: run an automatic order workflow, run a quotation approval workflow, or test an injection defense. The existing three-column inbox remains the core interface.

The top area shows Demo or Live mode, a concise explanation of what is simulated, and a reset control in demo mode. Scenario launch, approval, reset, loading, empty, and error states all reflect backend responses. After a mutation, the frontend reloads the inbox, approval list, dashboard, and selected persisted email.

An evidence drawer or section shows evaluation metrics and the reliability guarantees returned by backend endpoints. Copy distinguishes deterministic demo results from real-provider results.

## API contracts

- `GET /api/runtime` returns mode, external-service behavior, evaluation summary, and reliability evidence.
- `GET /api/demo/scenarios` returns scenario IDs, titles, descriptions, and expected workflow outcomes; it is available only in demo mode.
- `POST /api/demo/scenarios/{scenario_id}` launches or returns the session-scoped scenario.
- `POST /api/demo/reset` removes session-scoped demo records.
- Existing email, approval, dashboard, integration, and sync endpoints remain compatible. Demo mode requires a valid `X-Demo-Session` header on demo-scoped data routes.

## Deployment

A multi-stage Dockerfile builds the React frontend and installs the Python backend. FastAPI serves the compiled assets and falls back to `index.html` for client navigation while preserving `/api` routes. The container listens on `PORT`, stores SQLite under a configurable path, and exposes `/api/health` for deployment checks.

`render.yaml` defines a demo-mode web service with generated encryption configuration and no Google or model credentials. The repository README provides local live-mode steps, local demo-mode steps, Docker commands, evaluator commands, architecture, measured evidence, and the verified public URL after deployment.

## Security and boundaries

Demo mode cannot initialize Google clients or DeepSeek, even if credentials are accidentally present. It accepts only catalog scenarios, validates demo session identifiers, uses reserved recipient domains, and never accepts arbitrary outbound recipients or message bodies. Reset is scoped to one session.

Real mode never falls back to deterministic classification or simulated delivery. Google credentials remain encrypted at rest, API keys remain server-side, and configuration responses expose booleans and labels only.

## Completion criteria

The work is complete when backend and frontend tests pass, production frontend and Docker builds succeed, an API-driven demo scenario persists across page reload, the quotation resumes after approval, the evaluation report is reproducible from its command, session isolation is verified, and a public URL serves the demo health endpoint and workbench. If cloud-account authorization prevents deployment, all deployable artifacts must be complete and the exact external authorization blocker must be reported without claiming a public URL exists.
