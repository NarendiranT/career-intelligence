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
├── data/       Local uploads
└── docs/       Design and architecture notes
```

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

## Backend

Requires **Python 3.12+**, **Docker** (Postgres 16 + pgvector), and a **Groq API key** for chat. Embeddings run locally from a Hugging Face sentence-transformers model.

1. Copy env and fill secrets (repo root):

```bash
cp .env.example .env
```

Set at least:

- `GROQ_API_KEY` — required for indexing and RAG chat
- `JWT_SECRET` — change from the example value; used to sign login tokens

Optional: `HF_TOKEN` for gated Hugging Face embedding models. `EMBEDDING_MODEL` defaults to `sentence-transformers/all-MiniLM-L6-v2`. If you change the embedding model, set `EMBEDDING_DIM` to that model's vector size and re-run migrations/re-index.

`DATABASE_URL` already matches Docker Compose (`career` / `career` / `career_intelligence` on port **5432**).

2. Start Postgres, then install and migrate:

```bash
docker compose up -d
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
```

Wait until Postgres is healthy (`docker compose ps`) before `alembic upgrade head`.

3. Run the API:

```bash
uvicorn backend.app:app --reload --port 8000
```

- Health: http://localhost:8000/health  
- Docs: http://localhost:8000/docs  

Register or login (`POST /v1/auth/register` or `/v1/auth/login`) and send `Authorization: Bearer <token>` on `/v1/documents` and `/v1/chat`. In local dev the Vue app should leave `VITE_API_BASE_URL` empty so Vite proxies `/v1` to this API (see `frontend/.env.example`).

See [docs/AGENTS.md](docs/AGENTS.md) for graphs, tools, and curl examples.

## Status

- Frontend: signup/signin JWT session, guarded dashboard, upload → My Documents with live indexing status
- Backend: email/password JWT, indexing + RAG agents, Postgres/pgvector, FastAPI upload, document WebSocket, chat/SSE
