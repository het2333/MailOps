# MailOps Agent design

## Goal

MailOps Agent is a single-tenant enterprise email execution product. It connects one Google Workspace or Gmail account, classifies incoming customer email, queries approved business data, prepares an answer, and automatically sends it only when the risk policy permits it or an operator has approved it.

The first release must demonstrate a real Gmail and Google Calendar integration, LangGraph routing, persisted human-in-the-loop pauses, tool execution, auditability, and an operational web console. It is not a generic email drafting assistant and it does not integrate an ERP in this release.

## Chosen architecture

The repository contains two applications:

* `backend/`: Python 3.12, FastAPI, SQLAlchemy/SQLite, LangGraph, DeepSeek through the OpenAI-compatible client, and Google API clients.
* `frontend/`: React, TypeScript, Vite, and a responsive operations UI.

The browser only talks to FastAPI. FastAPI owns OAuth, the database, Gmail/Calendar access, and the agent graph. The UI never receives Google refresh tokens or the DeepSeek key.

Configuration comes from environment variables: `OPENAI_API_KEY`, `LLM_BASE_URL` (default `https://api.deepseek.com/v1`), `LLM_MODEL` (default `deepseek-chat`), `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`, `TOKEN_ENCRYPTION_KEY`, `DATABASE_URL`, and optional sync settings. A startup diagnostic reports missing integration configuration without exposing secret values.

## Email lifecycle

1. The operator connects the Gmail account using Google OAuth scopes for readonly/modify Gmail access, sending Gmail messages, and Google Calendar events/free-busy availability.
2. A persisted Gmail cursor incrementally synchronizes incoming messages. It excludes messages sent by the connected account and deduplicates by Gmail message ID. A user-triggered sync endpoint makes the integration usable in local development; the same cursor works with a scheduled worker in deployment.
3. The service creates an email record, then invokes the LangGraph state machine under `thread_id = email.id`.
4. `triage_email` uses a structured DeepSeek response to classify `order_status`, `quotation`, `meeting`, `faq`, `spam`, or `other`, with confidence and rationale.
5. A conditional edge executes the matching tool: an order lookup, product/price lookup and quote construction, Calendar free/busy lookup, or knowledge-base search. Business records live in SQLite seed data for the release.
6. `draft_reply` writes a thread-aware email reply using the original message and verified tool output. The graph never invents prices, order state, policies, or availability.
7. `risk_check` sends quotations and meetings, plus low-confidence, `other`, failed-tool, and policy-flagged emails to `human_approval`. Low-risk verified order and FAQ replies continue directly to send.
8. `human_approval` uses LangGraph `interrupt()` and the SQLite checkpointer. It persists an approval record with the draft, action summary, and risk reason. The UI offers approve, reject, and edit. Approve resumes the exact graph state with `Command(resume=...)`; reject marks the execution terminal without sending. For an approved meeting, Calendar creation occurs after approval and before reply delivery.
9. `send_email` replies in the Gmail thread and writes an immutable audit event with recipient, action, result, and timestamp. Retries are idempotent: a persisted send marker prevents a second Gmail delivery after a process retry.

## Console

The initial visual design is a three-column desktop-first workspace:

* Left: status-filtered inbox (`Needs attention`, `Awaiting approval`, `Completed`) and connection/sync status.
* Center: selected message, classification, verified business context, and editable proposed reply.
* Right: ordered graph timeline, tool results, confidence, policy decision, and approval actions.

An overview section exposes counts and recent actions, but the email workbench remains the primary route. Empty, loading, offline, and OAuth-not-connected states are explicit. The console is backed by FastAPI endpoints and persisted data only; no product behavior relies on browser storage or fake success transitions.

## Persistence

SQLite contains: integration settings/cursor, encrypted OAuth credential metadata, emails, agent executions, approvals, audit events, orders, products, price tiers, and knowledge articles. LangGraph checkpointer tables retain graph state separately. A demo seed provides only business data, never mock frontend state.

## API surface

* OAuth initiation/callback and integration status.
* Manual Gmail sync and inbox list/detail reads.
* Email execution/timeline reads.
* Approval list and decision mutation (`approve`, `reject`, `edit-and-approve`).
* Dashboard counts and activity reads.

All mutation responses return the persisted execution state required for a frontend refresh. The backend validates transitions so an already resolved approval cannot send a message again.

## Error handling and security

Provider failures surface as a failed execution with a human-action record; no outgoing email is attempted on an unresolved failure. The UI displays actionable configuration and retry guidance. OAuth refresh tokens are encrypted at rest with an application-supplied key. Secrets remain server-only. Message content is not logged in plaintext outside the intended database and Gmail audit metadata.

## Verification

Backend tests cover intent validation, policy decisions, tool input/output validation, state transitions, and approval idempotency using SQLite. Frontend tests cover data rendering and approval actions against a test API server. A browser smoke test exercises the persisted inbox → approval → completed transition. Build/typecheck runs for both applications. Gmail and Calendar functions are isolated behind provider interfaces so their real OAuth configuration can be tested manually without fabricating provider success in production code.
