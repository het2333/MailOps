# MailOps Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Build a single-Gmail-account enterprise email execution product with a LangGraph workflow, persisted approvals, and a three-column web operations console.

**Architecture:** A FastAPI service owns persistence, encrypted Google OAuth credentials, DeepSeek-powered LangGraph execution, Gmail and Calendar provider calls, and a REST API. A Vite React client renders persisted inbox/execution/approval data and performs approval mutations. SQLite holds business data and agent records; LangGraph uses a SQLite checkpointer with `thread_id` equal to the MailOps email ID.

**Tech Stack:** Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy, LangGraph, LangChain OpenAI client, Google API client, Fernet, pytest; React 18, TypeScript, Vite, Vitest, Playwright, CSS.

**Spec:** `docs/superpowers/specs/2026-09-08-mailops-agent-design.md`

## Global Constraints

* The product is single-tenant: only one connected Google account is supported.
* The LLM uses `OPENAI_API_KEY` against `LLM_BASE_URL`, defaulting to `https://api.deepseek.com/v1`, with `LLM_MODEL=deepseek-chat`.
* Only FastAPI may access Google tokens and LLM credentials.
* Gmail messages must be deduplicated by Gmail message ID and outgoing sends must be idempotent.
* Quotes, meetings, low-confidence, `other`, failed-tool, and policy-flagged emails require approval. Verified, high-confidence order and FAQ emails may send automatically.
* Approval must persist and resume the same LangGraph execution; it cannot create a fresh workflow.
* Business fixtures seed SQLite only; the frontend has no mock product data.
* The directory is not a Git repository. Do not create commits until a repository is explicitly initialized.

---

## File structure

```text
backend/
  app/
    api/{approvals,dashboard,emails,integrations}.py
    core/{config,security}.py
    db/{base,models,seed,session}.py
    domain/{schemas,policy}.py
    providers/{calendar,gmail,llm}.py
    services/{email_service,execution_service,sync_service}.py
    workflow/{graph,nodes,state}.py
    main.py
  tests/{api,domain,services,workflow}/...
  pyproject.toml
frontend/
  src/{api,components,hooks,pages,types}/...
  src/{main.tsx,styles.css}
  tests/...
  package.json
README.md
.env.example
.gitignore
```

### Task 1: Establish runnable application shells and secure configuration

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/app/core/config.py`
- Create: `backend/app/main.py`
- Create: `backend/tests/test_health.py`
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tsconfig.json`
- Create: `frontend/index.html`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/styles.css`
- Create: `.env.example`
- Create: `.gitignore`

**Interfaces:**
- Produces `Settings` with `database_url`, `llm_base_url`, `llm_model`, Google OAuth settings, and `token_encryption_key`.
- Produces `GET /api/health` returning `{"status": "ok", "configuration": {"google": bool, "llm": bool}}` without returning secrets.

- [x] **Step 1: Write the failing health/configuration test**

```python
# backend/tests/test_health.py
from fastapi.testclient import TestClient
from app.main import create_app

def test_health_never_exposes_secret_values(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "private-value")
    response = TestClient(create_app()).get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["configuration"]["llm"] is True
    assert "private-value" not in response.text
```

- [x] **Step 2: Run the test to verify it fails**

Run: `cd backend && uv run pytest tests/test_health.py -v`

Expected: FAIL because the FastAPI application does not exist.

- [x] **Step 3: Implement the minimal backend shell**

```python
# backend/app/main.py
from fastapi import FastAPI
from app.core.config import get_settings

def create_app() -> FastAPI:
    app = FastAPI(title="MailOps Agent")
    @app.get("/api/health")
    def health() -> dict[str, object]:
        settings = get_settings()
        return {"status": "ok", "configuration": {
            "google": settings.google_configured,
            "llm": settings.llm_configured,
        }}
    return app

app = create_app()
```

Use Pydantic settings with safe boolean computed properties; add the project dependencies and pytest configuration. Add Vite’s `dev`, `build`, `test`, and `test:e2e` scripts; render a minimal `MailOps Agent` application root.

- [x] **Step 4: Run backend test and both build checks**

Run: `cd backend && uv run pytest tests/test_health.py -v && cd ../frontend && npm run build`

Expected: the health test passes and Vite produces `dist/`.

### Task 2: Create persisted domain data and read API

**Files:**
- Create: `backend/app/db/base.py`
- Create: `backend/app/db/models.py`
- Create: `backend/app/db/session.py`
- Create: `backend/app/db/seed.py`
- Create: `backend/app/domain/schemas.py`
- Create: `backend/app/services/email_service.py`
- Create: `backend/app/api/emails.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/services/test_email_service.py`
- Test: `backend/tests/api/test_emails.py`

**Interfaces:**
- Produces SQLAlchemy `Email`, `Execution`, `Approval`, `AuditEvent`, `Order`, `Product`, `KnowledgeArticle`, and `IntegrationState` models.
- Produces `EmailService.list_emails(status: EmailStatus | None) -> list[EmailSummary]` and `EmailService.get_email(email_id: UUID) -> EmailDetail`.
- Produces `GET /api/emails?status=needs_attention` and `GET /api/emails/{email_id}`.

- [x] **Step 1: Write failing deduplication and detail tests**

```python
def test_ingesting_the_same_gmail_message_twice_returns_one_email(session):
    service = EmailService(session)
    first = service.ingest(InboundMessage(gmail_message_id="g-001", thread_id="t-1", sender="buyer@example.com", subject="Status?", body="PO-001"))
    second = service.ingest(InboundMessage(gmail_message_id="g-001", thread_id="t-1", sender="buyer@example.com", subject="Status?", body="PO-001"))
    assert first.id == second.id
    assert service.count_emails() == 1
```

```python
def test_email_detail_endpoint_returns_persisted_message_and_execution(client, seeded_email):
    response = client.get(f"/api/emails/{seeded_email.id}")
    assert response.status_code == 200
    assert response.json()["subject"] == seeded_email.subject
    assert response.json()["execution"] is not None
```

- [x] **Step 2: Run the targeted tests to verify they fail**

Run: `cd backend && uv run pytest tests/services/test_email_service.py tests/api/test_emails.py -v`

Expected: FAIL because models, service, and endpoints are missing.

- [x] **Step 3: Implement models, SQLite setup, and read contracts**

```python
class Email(Base):
    __tablename__ = "emails"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    gmail_message_id: Mapped[str] = mapped_column(unique=True, index=True)
    gmail_thread_id: Mapped[str]
    sender: Mapped[str]
    subject: Mapped[str]
    body: Mapped[str]
    status: Mapped[EmailStatus] = mapped_column(default=EmailStatus.NEEDS_ATTENTION)
```

Create all tables on startup for this SQLite MVP and insert deterministic order/product/knowledge fixtures only when their tables are empty. Return Pydantic response types, return 404 for an unknown ID, and never fabricate an execution object.

- [x] **Step 4: Run the persistence/API suite**

Run: `cd backend && uv run pytest tests/services/test_email_service.py tests/api/test_emails.py -v`

Expected: PASS with the same Gmail message stored only once.

### Task 3: Build business tools and the risk policy

**Files:**
- Create: `backend/app/domain/policy.py`
- Create: `backend/app/services/business_tools.py`
- Test: `backend/tests/domain/test_policy.py`
- Test: `backend/tests/services/test_business_tools.py`

**Interfaces:**
- Produces `RiskDecision(requires_approval: bool, reasons: list[str])`.
- Produces `BusinessTools.get_order(po_number)`, `get_quote(model, quantity)`, `search_knowledge(query)`, `find_calendar_slots(request)` and `create_calendar_event(request)`.
- `find_calendar_slots` and `create_calendar_event` delegate to a provider interface; production calls Google Calendar while tests use an in-memory provider.

- [x] **Step 1: Write failing policy and verified-data tests**

```python
@pytest.mark.parametrize("intent,confidence,tool_ok,expected", [
    (Intent.ORDER_STATUS, 0.95, True, False),
    (Intent.FAQ, 0.95, True, False),
    (Intent.QUOTATION, 0.99, True, True),
    (Intent.MEETING, 0.99, True, True),
    (Intent.ORDER_STATUS, 0.51, True, True),
    (Intent.FAQ, 0.99, False, True),
])
def test_risk_policy_selects_required_human_review(intent, confidence, tool_ok, expected):
    assert evaluate_risk(intent, confidence, tool_ok).requires_approval is expected

def test_quote_is_calculated_from_persisted_product_price(session):
    quote = BusinessTools(session, calendar=FakeCalendar()).get_quote("MODEL-X", 100)
    assert quote.total == Decimal("8900.00")
```

- [x] **Step 2: Run the tests to verify they fail**

Run: `cd backend && uv run pytest tests/domain/test_policy.py tests/services/test_business_tools.py -v`

Expected: FAIL because the policy and tool interfaces are missing.

- [x] **Step 3: Implement deterministic tools and policy**

Use typed Pydantic tool result models. Extract order identifiers and quote quantities only in the LLM routing layer; business tools accept already validated arguments. Search knowledge with normalized keyword scoring and return only stored article snippets. `get_quote` must return a failure result for unknown products rather than estimating a price. Add a calendar protocol with `list_free_slots` and `create_event` methods.

- [x] **Step 4: Run the tool/policy test suite**

Run: `cd backend && uv run pytest tests/domain/test_policy.py tests/services/test_business_tools.py -v`

Expected: PASS, including policy escalation for every unsafe state.

### Task 4: Implement the persisted LangGraph workflow and approval resume

**Files:**
- Create: `backend/app/workflow/state.py`
- Create: `backend/app/workflow/nodes.py`
- Create: `backend/app/workflow/graph.py`
- Create: `backend/app/services/execution_service.py`
- Create: `backend/app/providers/llm.py`
- Test: `backend/tests/workflow/test_graph.py`
- Test: `backend/tests/services/test_execution_service.py`
- Test: `backend/tests/providers/test_llm.py`

**Interfaces:**
- Produces `MailOpsState` with email ID, intent, confidence, tool result, draft reply, risk decision, approval ID, and send outcome.
- Produces `build_graph(dependencies) -> CompiledStateGraph` and `ExecutionService.start(email_id) -> ExecutionView`.
- Produces `ExecutionService.resume(approval_id, decision: ApprovalDecision, edited_reply: str | None) -> ExecutionView`.

- [x] **Step 1: Write failing workflow tests**

```python
def test_quotation_interrupts_and_persists_approval(graph, checkpoint_config):
    result = graph.invoke(quotation_state(), checkpoint_config)
    assert "__interrupt__" in result
    assert approval_from_db().status == ApprovalStatus.PENDING

def test_approval_resume_sends_once_and_marks_completed(graph, checkpoint_config, fake_gmail):
    graph.invoke(quotation_state(), checkpoint_config)
    result = graph.invoke(Command(resume={"decision": "approve"}), checkpoint_config)
    assert result["send_outcome"].sent is True
    assert fake_gmail.sent_count == 1
```

- [x] **Step 2: Run workflow tests to verify they fail**

Run: `cd backend && uv run pytest tests/workflow/test_graph.py tests/services/test_execution_service.py -v`

Expected: FAIL because graph compilation and checkpoint recovery do not exist.

- [x] **Step 3: Implement graph nodes and state recovery**

```python
builder = StateGraph(MailOpsState)
builder.add_node("triage_email", triage_email)
builder.add_node("execute_tool", execute_tool)
builder.add_node("draft_reply", draft_reply)
builder.add_node("risk_check", risk_check)
builder.add_node("human_approval", human_approval)
builder.add_node("send_email", send_email)
builder.add_edge(START, "triage_email")
builder.add_conditional_edges("triage_email", route_intent)
builder.add_conditional_edges("risk_check", route_risk)
```

`human_approval` must create the DB approval once then call `interrupt(payload)`. Its resumed branch validates an unresolved approval, accepts only `approve`, `reject`, and `edit_and_approve`, and applies an edited draft only to that state. `send_email` writes a durable send marker before returning, and checks it before calling the Gmail provider. Low-risk order and FAQ messages continue directly to `send_email`. Add `DeepSeekTriageClient`, constructed with `ChatOpenAI(base_url=settings.llm_base_url, api_key=settings.openai_api_key, model=settings.llm_model)`, that validates structured output against the intent schema. When the service is not configured, it must mark the execution failed for human action instead of pretending to classify the mail.

- [x] **Step 4: Run graph tests and full backend suite**

Run: `cd backend && uv run pytest -v`

Expected: PASS; approval tests prove a repeated resume cannot produce a second send.

### Task 5: Add real Google OAuth, Gmail sync/send, Calendar providers, and REST mutations

**Files:**
- Create: `backend/app/core/security.py`
- Create: `backend/app/providers/gmail.py`
- Create: `backend/app/providers/calendar.py`
- Create: `backend/app/services/sync_service.py`
- Create: `backend/app/api/integrations.py`
- Create: `backend/app/api/approvals.py`
- Create: `backend/app/api/dashboard.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/api/test_approvals.py`
- Test: `backend/tests/api/test_integrations.py`

**Interfaces:**
- Produces `GoogleCredentialStore.save/restore` encrypting refresh-token payloads with Fernet.
- Produces `GmailProvider.sync_since(cursor) -> SyncResult`, `send_reply(message) -> SendResult`, and `CalendarProvider` implementing the Task 3 protocol.
- Produces `SyncService.run_once() -> SyncResult` and an optional `AUTO_SYNC_SECONDS` scheduler that invokes it serially after startup.
- Produces `POST /api/integrations/google/connect`, `GET /api/integrations/google/callback`, `GET /api/integrations/status`, `POST /api/integrations/sync`, `GET /api/approvals`, and `POST /api/approvals/{approval_id}/decision`.

- [x] **Step 1: Write failing endpoint and encryption tests**

```python
def test_deciding_an_approval_returns_persisted_completed_execution(client, pending_approval):
    response = client.post(f"/api/approvals/{pending_approval.id}/decision", json={"decision": "approve"})
    assert response.status_code == 200
    assert response.json()["status"] == "completed"

def test_stored_google_credentials_do_not_contain_refresh_token_plaintext(tmp_path):
    store = GoogleCredentialStore(key=Fernet.generate_key())
    blob = store.encrypt({"refresh_token": "secret-refresh-token"})
    assert b"secret-refresh-token" not in blob
```

- [x] **Step 2: Run provider/API tests to verify they fail**

Run: `cd backend && uv run pytest tests/api/test_approvals.py tests/api/test_integrations.py -v`

Expected: FAIL because endpoints and providers are absent.

- [x] **Step 3: Implement provider adapters and API routes**

Use Google’s installed/web OAuth flow only through the callback, request Gmail read/modify/send and Calendar event/free-busy scopes, encrypt credentials before storage, and expose connection state without exposing tokens. Gmail sync uses the stored history cursor or a first-run inbox listing; it invokes `ExecutionService.start` for each deduplicated inbound message. `SyncService` commits the cursor only after an item is persisted and schedules no overlapping run. `send_reply` supplies Gmail `threadId` and RFC 2822 reply headers, retries transient 429/5xx failures with bounded exponential backoff, and never retries an already marked send. Approval mutations call `ExecutionService.resume` and reject terminal approvals with HTTP 409.

- [x] **Step 4: Run all backend tests and service startup**

Run: `cd backend && uv run pytest -v && uv run uvicorn app.main:app --port 8000`

Expected: tests PASS and `GET /api/health` reports a non-secret configuration diagnostic. Stop the server after the smoke check.

### Task 6: Build the persisted MailOps three-column console

**Files:**
- Create: `frontend/src/types/api.ts`
- Create: `frontend/src/api/client.ts`
- Create: `frontend/src/hooks/useMailOps.ts`
- Create: `frontend/src/components/InboxList.tsx`
- Create: `frontend/src/components/EmailDetail.tsx`
- Create: `frontend/src/components/ExecutionTimeline.tsx`
- Create: `frontend/src/components/ApprovalPanel.tsx`
- Create: `frontend/src/components/ConnectionBanner.tsx`
- Create: `frontend/src/pages/WorkbenchPage.tsx`
- Modify: `frontend/src/main.tsx`
- Modify: `frontend/src/styles.css`
- Test: `frontend/src/components/ApprovalPanel.test.tsx`
- Test: `frontend/src/pages/WorkbenchPage.test.tsx`

**Interfaces:**
- Consumes the exact FastAPI schemas from Tasks 2 and 5 through `mailOpsApi`.
- Produces a `WorkbenchPage` that takes no mock data and refetches persisted email/detail data after an approval decision.

- [x] **Step 1: Write failing UI tests**

```tsx
it("approves a pending quote and refreshes the completed execution", async () => {
  server.use(http.post("/api/approvals/ap-1/decision", () => HttpResponse.json(completedExecution)))
  render(<ApprovalPanel approval={pendingApproval} onResolved={onResolved} />)
  await userEvent.click(screen.getByRole("button", { name: "Approve & send" }))
  await waitFor(() => expect(onResolved).toHaveBeenCalledWith(completedExecution))
})
```

- [x] **Step 2: Run UI tests to verify they fail**

Run: `cd frontend && npm run test -- --run src/components/ApprovalPanel.test.tsx src/pages/WorkbenchPage.test.tsx`

Expected: FAIL because the components and API client do not exist.

- [x] **Step 3: Implement the workbench against real API calls**

Create typed `fetch` methods with non-2xx error parsing. Render connection setup and a Sync now action from `/api/integrations/status`; fetch inbox filters and selected email from FastAPI; display only API-returned classifications, business facts, draft, timeline, and approval status. The approval panel supports a draft edit textarea and calls the decision endpoint with `edit_and_approve` only when edited. Show specific loading, empty, mutation-in-progress, and provider-failure states. Use the selected A layout: 280px inbox, flexible message center, 340px execution rail, collapsing to one column on narrow screens.

- [x] **Step 4: Run frontend unit tests and production build**

Run: `cd frontend && npm run test -- --run && npm run build`

Expected: PASS and a successful Vite production build.

### Task 7: Document setup and verify a real persisted end-to-end flow

**Files:**
- Create: `frontend/e2e/approval-flow.spec.ts`
- Create: `README.md`
- Modify: `.env.example`
- Modify: `.gitignore`

**Interfaces:**
- Produces setup documentation for DeepSeek, Google Cloud OAuth consent/redirect URI, Gmail scopes, Calendar scopes, and starting both applications.
- Produces an end-to-end test that proves inbox data comes from the backend and an approval updates persisted state.

- [x] **Step 1: Write the failing browser flow**

```ts
test("operator approves a quotation from the inbox and sees it complete", async ({ page }) => {
  await page.goto("/")
  await page.getByText("100 units of MODEL-X").click()
  await page.getByRole("button", { name: "Approve & send" }).click()
  await expect(page.getByText("Sent via Gmail")).toBeVisible()
})
```

- [x] **Step 2: Run the browser test to verify its initial failure**

Run: `cd frontend && npm run test:e2e -- approval-flow.spec.ts`

Expected: FAIL until backend startup, seed orchestration, and UI behavior are wired together.

- [x] **Step 3: Add the test harness and operational documentation**

Start an isolated SQLite-backed FastAPI test server and Vite server for Playwright. The harness must use the same HTTP routes and persistence layer as the application; it may seed a pending quotation directly through the backend test database. Document the Google Cloud configuration steps, environment settings, local startup, manual OAuth connection, manual sync, data policy, automatic-send risk rules, and the limitation that an actual Gmail/Calendar send requires the operator’s own OAuth credentials. Ignore `.superpowers/`, `.env`, SQLite databases, build output, Python cache, node modules, and Playwright artifacts.

- [x] **Step 4: Run final verification commands**

Run: `cd backend && uv run pytest -v && cd ../frontend && npm run test -- --run && npm run build && npm run test:e2e`

Expected: all backend tests, frontend tests, production build, and Playwright flow pass. Then manually connect the Google account, invoke Sync now, approve a non-production test email, and confirm the Gmail thread and audit record show exactly one reply.
