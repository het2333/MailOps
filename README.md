# MailOps Agent

MailOps turns customer email into verified business action. It classifies a message, queries trusted order, pricing, knowledge, or Calendar data, applies a risk policy, pauses sensitive work for human approval, and replies in the original Gmail thread.

[**Open the live safe demo**](https://novagent.work/mailops/)

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/het2333/MailOps)

## Try the safe demo

The public demo uses the complete FastAPI → SQLite → LangGraph → approval → audit path. Only the external DeepSeek, Gmail, and Google Calendar calls are replaced with deterministic local adapters, so recruiters can approve and “send” a quotation without contacting anyone.

```bash
docker build -t mailops-demo .
docker run --rm -p 8000:8000 mailops-demo
```

Open `http://127.0.0.1:8000`, choose a scenario, and inspect the persisted execution. The quotation and meeting scenarios pause for approval. The order scenario completes automatically. The injection scenario is escalated instead of exposing unrelated data.

For development without Docker:

```bash
cd backend
DEMO_MODE=true DATABASE_URL=sqlite:///./mailops-demo.db uv run uvicorn app.main:app --reload --port 8000

# In another terminal
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`.

## Evidence

The committed public benchmark contains 12 synthetic business emails across all supported intents, failed lookups, unknown requests, and prompt injection.

| Metric | Deterministic public benchmark |
| --- | ---: |
| Intent accuracy | 100% |
| Argument exact match | 100% |
| Human-review recall | 100% |
| Unsafe auto-sends | 0 |

Reproduce the report:

```bash
cd backend
uv run python evals/run_evaluation.py --provider demo
```

The generated [evaluation report](docs/evaluation-report.md) includes latency and limitations. To evaluate the configured real model against the same data, use `--provider deepseek`.

Reliability tests cover four failure classes:

- a LangGraph approval resumes from a file-backed SQLite checkpoint after the service and graph are reconstructed;
- duplicate Gmail messages and duplicate demo launches create one execution;
- successful delivery replay returns the original message ID without sending again;
- an ambiguous send marker blocks retry and requires human review.

## Architecture

```text
Gmail incremental sync ─┐
Demo scenario catalog ──┼─ FastAPI ─ LangGraph ─ risk policy ─ approval ─ Gmail reply
Google Calendar ────────┘      │                         │
                               ├─ SQLite business data   └─ durable checkpoint
React operations console ──────┴─ session-scoped API and audit evidence
```

| Layer | Technology |
| --- | --- |
| Web console | React 18, TypeScript, Vite |
| API | Python 3.12, FastAPI, Pydantic |
| Agent workflow | LangGraph with SQLite checkpoints |
| Model | DeepSeek via the OpenAI-compatible client |
| Persistence | SQLAlchemy and SQLite |
| Integrations | Gmail API, Google Calendar API, Google OAuth |
| Verification | pytest, Vitest, Playwright, Docker |

The browser never receives Google credentials or the model API key. OAuth refresh credentials are encrypted before storage. Demo mode cannot initialize external providers even when credentials are present.

## Run with real Gmail and Calendar

Requirements: Python 3.12+, Node.js 22.12+, `uv`, a Google OAuth Web application, and a DeepSeek API key.

```bash
cp .env.example backend/.env
cd backend
uv sync --group dev
uv run python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Set these values in `backend/.env`:

```dotenv
DEMO_MODE=false
OPENAI_API_KEY=your-deepseek-key
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/integrations/google/callback
TOKEN_ENCRYPTION_KEY=your-generated-fernet-key
DATABASE_URL=sqlite:///./mailops.db
AUTO_SYNC_SECONDS=0
```

Enable Gmail API and Google Calendar API, then register the redirect URI exactly as shown above. Start the API and frontend using the development commands, click **Connect Gmail**, complete OAuth, and select **Sync now**. Use a test account: approving a real quotation sends a Gmail reply, and approving a meeting also creates a Calendar event.

## Verify

```bash
cd backend && uv run pytest -q
cd frontend && npm run test -- --run && npm run build
docker build -t mailops-demo .

# Verify a path-mounted public deployment
cd frontend
PLAYWRIGHT_BASE_URL=https://novagent.work \
PLAYWRIGHT_APP_PATH=/mailops/ \
npm run test:e2e
```

The repository includes `render.yaml` for a safe demo deployment. Its filesystem is intentionally ephemeral; each browser session can recreate catalog scenarios with one click.

## Scope

This release is single-account in live mode. Orders, products, and knowledge articles are seeded demonstration business data. Production use would replace them with authenticated ERP and knowledge connectors, add organization-level authorization, and move SQLite to a managed database.
