# Career Intelligence

AI-powered career assistant. Upload a resume, add job descriptions, and get skill-gap analysis, job matching, and interview prep.

## Layout

```text
career-intelligence/
├── frontend/   Vue 3 app (JWT session; upload + documents live)
├── backend/    FastAPI + SQLModel (documents + chat)
├── agent/      LangGraph indexing and RAG graphs
├── mcp/        MCP-style tools
├── alembic/    Postgres migrations
├── otel/       Collector and Prometheus config
├── data/       Local uploads
├── docs/       Design and architecture notes
└── run.py      Starts FastAPI + Vite together
```

## Run frontend and backend together

After Postgres is up, migrations are applied, and `frontend/` has `npm install` (see Backend below):

```bash
source .venv/bin/activate
python run.py
```

- API: http://localhost:8000 (`/health`, `/docs`)
- UI: http://localhost:5173

Ctrl+C stops both. You can still run them separately (`uvicorn` + `npm run dev`).

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

## Backend

Requires **Python 3.12+**, **Docker** (Postgres 16 + pgvector; optional Jaeger + Prometheus), and a **Groq API key** for chat. Embeddings run locally from a Hugging Face sentence-transformers model.

1. Copy env and fill secrets (repo root):

```bash
cp .env.example .env
```

Set at least:

- `GROQ_API_KEY` — required for indexing and RAG chat
- `JWT_SECRET` — change from the example value; used to sign login tokens

Optional: `HF_TOKEN` for gated Hugging Face embedding models. `EMBEDDING_MODEL` defaults to `sentence-transformers/all-MiniLM-L6-v2`. If you change the embedding model, set `EMBEDDING_DIM` to that model's vector size and re-run migrations/re-index.

`DATABASE_URL` already matches Docker Compose (`career` / `career` / `career_intelligence` on port **5432**).

2. Start Postgres (and the observability stack), then install and migrate:

```bash
docker compose up -d
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
```

Wait until Postgres is healthy (`docker compose ps`) before `alembic upgrade head`. Compose also starts an OpenTelemetry Collector, Jaeger, and Prometheus. Tracing is off until you set `OTEL_ENABLED=true` in `.env`.

3. Run the API (or skip this and use `python run.py` from the repo root to start API + Vite):

```bash
uvicorn backend.app:app --reload --port 8000
```

- Health: http://localhost:8000/health  
- Docs: http://localhost:8000/docs  
- Jaeger UI: http://localhost:16686  
- Prometheus: http://localhost:9090  

To export traces and metrics from the API, set `OTEL_ENABLED=true` (endpoint defaults to `http://localhost:4318`). Product token usage stays on `GET /v1/usage`; OTel is ops telemetry only.

Register or login (`POST /v1/auth/register` or `/v1/auth/login`) and send `Authorization: Bearer <token>` on `/v1/documents` and `/v1/chat`. In local dev the Vue app should leave `VITE_API_BASE_URL` empty so Vite proxies `/v1` to this API (see `frontend/.env.example`).

See [docs/AGENTS.md](docs/AGENTS.md) for graphs, tools, and curl examples. Frontend agent notes: [docs/FRONTEND_CONTEXT.md](docs/FRONTEND_CONTEXT.md). Architecture Word document: [docs/Career_Intelligence_Architecture_and_System_Design.docx](docs/Career_Intelligence_Architecture_and_System_Design.docx).

## Status

- Frontend: signup/signin JWT session, guarded dashboard, upload → My Documents with live indexing status, chat RAG over WebSocket, usage dashboard
- Backend: email/password JWT, indexing + RAG agents, Postgres/pgvector, FastAPI upload, document WebSocket, chat WebSocket + REST/SSE, LLM token usage on `usage_events` / `GET /v1/usage`, optional OpenTelemetry traces/metrics

## What we'd add next

Not everything that belongs in a production career assistant is in this repo yet. Indexing and RAG currently run **in-process**: `POST /v1/documents` schedules FastAPI `BackgroundTasks`, and chat invokes the LangGraph RAG graph on the same API worker. That is fine for a single-node demo. These are the next pieces we would implement.

### Scalable indexing and RAG (SQS or Kafka)

Move document indexing and heavy RAG work off the API process onto a queue plus workers.

- **Queue:** AWS SQS (simpler ops, at-least-once, good with a later ECS/Lambda worker) or Kafka (higher throughput, replay, multiple consumer groups for indexing vs RAG vs usage). Start with **SQS** unless we already need Kafka-style replay.
- **Producers:** API only persists the `documents` row (`uploaded`) and enqueues `{ document_id, user_id, doc_type }`. Chat `chat.ask` could enqueue long jobs and stream status, or keep short questions on the API while batch/extract-topics jobs go to the queue.
- **Consumers:** dedicated workers run `indexing_graph` / `rag_graph`, then write status, chunks, and `usage_events` as they do today. Status still fans out on `WS /v1/ws/documents` (and chat frames) so the Vue app does not change.
- **Why:** uploads and Groq/embedding work no longer block or crash with the API; we can scale workers independently, retry failed indexing, and avoid losing jobs on process restart.
- **Out of scope for v1 of this change:** replacing Postgres/pgvector; Redis is optional later for WebSocket fan-out across multiple API instances.

### Rate limits

Protect Groq TPM, the API, and noisy clients.

- Per-user and per-IP limits on `POST /v1/documents`, `POST /v1/chat`, and `WS /v1/ws/chat` asks (e.g. N uploads/hour, M questions/minute).
- Return **429** with `Retry-After`; on the WebSocket send `chat.error` with a clear quota message.
- Vue: disable send/upload briefly and toast the limit (no silent failures).

### Token limits and subscriptions (future billing)

`GET /v1/usage` already **records** prompt/completion tokens. It does not **enforce** a plan.

- **Hard token caps** per user per billing period (daily/monthly) for chat, interview, and indexing separately or as a shared pool.
- Reject or degrade when the cap is hit (block new asks; still allow viewing documents and past chats).
- **Subscriptions:** Free / Pro / Team tiers with included token allotments, overage rules, and a Settings page to see remaining quota. Stripe (or similar) for checkout and webhooks that update `users.plan` and period reset dates.
- Usage UI already has the charts; next step is remaining-quota + upgrade CTA, not a new dashboard from scratch.

### LLM-as-judge after each reply

Assistant chat already runs a **faithfulness** check in the RAG graph (retry retrieval up to twice). Interview topic chat skips that. Opt-in **DeepEval** goldensets live under `evals/` (`RUN_EVALS=1 pytest -m eval`) and are not wired into production traffic.

Next: after `chat.done`, run an **LLM-as-judge** pass (same Groq router/judge pattern as DeepEval) on the grounded answer:

- Scores: faithfulness / groundedness, helpfulness, safety, and (interview) relevance to the topic.
- Persist `eval_events` (message_id, channel `assistant` | `interview`, scores, rationale, judge model, latency) so product can trend quality without re-running pytest.
- Do this **async** (queue worker) so the user still sees the streamed reply first; optionally show a small “validated” badge when the judge agrees (the UI already has `validated` from faithfulness).
- Sample or rate-limit judge calls so they do not double Groq TPM on every turn.

### Human feedback in chat

Thumbs up/down on assistant replies are **local only** (`localStorage` `ci.chatFeedback`). They never hit the API.

Next:

- `POST /v1/messages/{id}/feedback` with `{ rating: "up" | "down", comment?: string }` (JWT, owner-only). Same control on interview answers.
- Store `message_feedback` (user_id, message_id, rating, optional comment, created_at) and join it to judge scores.
- Vue: send the thumb immediately, toast on failure, keep the current icons.

### Product admin panel (not the user dashboard)

`GET /v1/usage` is **per signed-in user**. There is no operator view.

Add a **separate admin app or `/admin` routes** (staff JWT / role `admin`, not the career dashboard):

| Metric | Source (once built) |
| --- | --- |
| Users created | `users` count, signups over time |
| Chats asked | `usage_events` / conversation messages with `feature=chat` or `interview` |
| Token usage (all users) | sum of `usage_events` by day, user, feature, model |
| Human feedback | thumbs up/down rates, comments, worst messages |
| LLM-as-judge eval | mean scores, fail rate, by channel (assistant vs interview) |

Filters: date range, user, channel. Export CSV. No resume/JD body text in the admin UI—IDs, scores, and truncated questions only.

### Fine-tuned models from eval + feedback

If judge scores and human thumbs accumulate enough labeled turns:

- Export a training set: prompt + retrieved context + assistant/interview reply, labeled from **human thumbs** (primary) and **judge scores** (filter out low-faithfulness rows). Split by `channel` so **Chat with Assistant** and **Interview prep** can be separate adapters.
- Fine-tune a smaller chat model (LoRA on an open model, or a provider fine-tune) and expose it as an extra Chat Settings model once quality beats the current Groq generation model on a held-out eval set.
- Keep Groq gpt-oss as the default until the fine-tune wins on faithfulness + thumbs; never train on raw resume PII without redaction.

This depends on the feedback API and judge pipeline above; it is not a first milestone.

### Other follow-ups (smaller)

- Forgot-password and refresh-token rotation
- Password-reset and billing Settings routes (sidebar Settings is a label only)
- Multi-instance WebSocket pub/sub if the API is replicated
- Frontend tests / ESLint; topic delete UI
