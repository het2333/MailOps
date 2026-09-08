# MailOps Agent

> Enterprise Email Execution Agent built with LangGraph

MailOps Agent turns a connected Gmail inbox into an execution surface. It classifies an inbound customer email, uses verified business data or Google Calendar, applies a risk policy, pauses high-risk work for human review, and sends the Gmail thread reply after approval.

## What the first release does

| Email type | Verified action | Send policy |
| --- | --- | --- |
| Order status | Looks up an order in SQLite | Sends automatically at high confidence |
| Product quotation | Looks up a persisted product price and calculates the total | Requires approval |
| Meeting request | Checks Google Calendar availability; creates the event after approval | Requires approval |
| FAQ | Searches the persisted knowledge base | Sends automatically at high confidence |
| Unknown, spam, low-confidence, or failed tool request | Does not invent a result | Requires human attention |

The workflow is a LangGraph state machine: `triage_email → execute_tool → draft_reply → risk_check → human_approval? → send_email`. The approval node calls LangGraph `interrupt()` and uses a SQLite checkpointer, so approval resumes the original execution rather than beginning a new one. A durable send marker prevents duplicate delivery during retries.

## Architecture

```text
Gmail incremental sync ─┐
                       ├─ FastAPI ─ LangGraph ─ DeepSeek (OpenAI-compatible)
Google OAuth / Calendar ┘      │
                               ├─ SQLite: emails, executions, approvals, audit, business data
React three-column console ────┘
```

The browser does not receive Google credentials or `OPENAI_API_KEY`. Google refresh credentials are encrypted before being stored in SQLite.

## Prerequisites

- Python 3.12+ and [uv](https://docs.astral.sh/uv/)
- Node.js 20+
- A Google Cloud OAuth **Web application** and a Gmail account you are authorized to connect
- A DeepSeek API key, exposed as `OPENAI_API_KEY`

## Configure Google Cloud

1. Create a Google Cloud project and enable **Gmail API** and **Google Calendar API**.
2. Configure the OAuth consent screen for the company account(s) that may connect MailOps.
3. Create OAuth credentials of type **Web application**.
4. Add this authorized redirect URI exactly:

   `http://localhost:8000/api/integrations/google/callback`

5. MailOps requests only these scopes: Gmail modify, Gmail send, and Calendar access. This is needed to read the inbox, send an approved reply, and create an approved meeting event.

## Run locally

```bash
cp .env.example backend/.env
```

Edit `backend/.env` and set:

```dotenv
OPENAI_API_KEY=your-deepseek-key
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/integrations/google/callback
TOKEN_ENCRYPTION_KEY=your-fernet-key
DATABASE_URL=sqlite:///./mailops.db
AUTO_SYNC_SECONDS=0
```

Generate the Fernet value with:

```bash
cd backend
uv run python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Start the API and console in separate terminals:

```bash
cd backend && uv sync --group dev && uv run uvicorn app.main:app --reload --port 8000
cd frontend && npm install && npm run dev
```

Open `http://127.0.0.1:5173`. Click **Connect Gmail**, complete Google OAuth, and select **Sync now**. Use a non-production test message for the first end-to-end check. An approved quote or meeting will send a real Gmail reply; a meeting approval also creates a real Calendar event.

Set `AUTO_SYNC_SECONDS=60` in a deployment to poll incremental Gmail history every minute. Keep it `0` while developing and use **Sync now**.

## Tests

```bash
cd backend && uv run pytest -v
cd frontend && npm run test -- --run && npm run build
```

Backend tests cover Gmail-message deduplication, risk escalation, price verification, encrypted OAuth credentials, LangGraph interruption, checkpoint resume, and single-send behavior. Frontend tests cover API-rendered email context and approve-and-send interaction.

## Data and safety notes

- The seeded SQLite orders, products, and knowledge article are demonstration business data; replace them with an ERP/knowledge integration before production use.
- The agent never estimates a price, order state, policy, or calendar availability when its verification tool fails.
- OAuth tokens, `OPENAI_API_KEY`, local SQLite databases, build output, and the visual-brainstorm artifacts are ignored by version control.
- This release is intentionally single-account. Multi-tenant authorization, Gmail push notifications, role-based approvals, and ERP connectors are next-stage work.
