# Career Intelligence agents

The Vue app uses JWT auth. Home loads `GET /v1/home`. Upload posts each file to `POST /v1/documents`, then My Documents loads `GET /v1/documents` and listens on `WS /v1/ws/documents` for indexing status. Chat UI is not wired yet.

## Stack

- FastAPI + SQLModel on port 8000
- PostgreSQL 16 + pgvector (Docker)
- Groq chat via LangChain `ChatGroq`: extraction/router `openai/gpt-oss-20b`, generation `openai/gpt-oss-120b`
- Hugging Face embeddings (`sentence-transformers/all-MiniLM-L6-v2`, 384-d) via `HuggingFaceEmbeddings`
- MCP-style tools in `mcp/` (in-process callables)

Chat roles (Groq): `EXTRACTION_MODEL` for resume/job structured extract, `ROUTER_MODEL` for document type and query intent, `GENERATION_MODEL` for answers. Embeddings: any **sentence-transformers–compatible** Hugging Face model via `EMBEDDING_MODEL`; keep `EMBEDDING_DIM` in sync (MiniLM is 384).

## Setup

```bash
cp .env.example .env
# set GROQ_API_KEY in .env (optional HF_TOKEN for gated embedding models)

docker compose up -d
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn backend.app:app --reload --port 8000
```

Identity: send `Authorization: Bearer <jwt>` from `POST /v1/auth/register` or `/v1/auth/login`. Documents and chat reject missing or invalid tokens with 401.

## Indexing graph

`agent/indexing/graph.py`

1. Load document (PDF / DOCX / TXT)
2. Route `resume` vs `job` (form hint or LLM)
3. Structured extract (Pydantic)
4. Chunk + embed
5. Persist chunks and status

Upload:

```bash
TOKEN=<jwt>
curl -s -F "file=@resume.txt;type=text/plain" -F "doc_type=resume" \
  -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/v1/documents
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/v1/documents
```

Each upload inserts a `documents` row, then runs `indexing_graph` in a FastAPI background task. Status changes (`uploaded` → `processing` → `processed` / `failed`) are pushed on `WS /v1/ws/documents?token=<jwt>` as `{ "type": "document.status", "document": { ...DocumentOut } }`. Delete with `DELETE /v1/documents/<id>` (owner only); clients also receive `{ "type": "document.deleted", "document_id": "<uuid>" }`.

## RAG graph

`agent/rag/graph.py`

1. Input guardrail
2. Query rewrite
3. Metadata-filtered pgvector search
4. Build prompt
5. Generate answer
6. Faithfulness check (retry retrieval up to 2 times)
7. Persist conversation + usage

```bash
curl -s -X POST http://localhost:8000/v1/chat \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"question":"What skills are on my resume?","resume_id":"<uuid>","stream":false}'
```

SSE: `"stream": true` yields `token` then `done` events.

Auth:

```bash
curl -s -X POST http://localhost:8000/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"full_name":"Ada Lovelace","email":"ada@example.com","password":"Passw0rd!"}'
curl -s http://localhost:8000/v1/auth/me -H "Authorization: Bearer <token>"
```

Protected document/chat calls need the same `Authorization` header.

## Tools

Indexing: `create_or_update_user`, `save_resume_profile`, `save_job_profile`, `update_processing_status`, `replace_document_chunks`, `enrich_job_board` (stub).

RAG: `get_user_profile`, `fetch_document_metadata`, `fetch_structured_profiles`, `save_conversation_message`, `update_usage`, `web_search` (stub).
