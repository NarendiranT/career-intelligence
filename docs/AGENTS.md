# Career Intelligence agents

The Vue app uses JWT auth. Home loads `GET /v1/home`. Upload posts each file to `POST /v1/documents`, then My Documents loads `GET /v1/documents` and listens on `WS /v1/ws/documents` for indexing status. Chat loads those documents, lists threads on `GET /v1/conversations`, and streams RAG answers on `WS /v1/ws/chat`. Interview topics live on `GET /v1/topics`; topic chat uses the same WebSocket with `channel=interview`.

## Stack

- FastAPI + SQLModel on port 8000
- PostgreSQL 16 + pgvector (Docker)
- Groq chat via LangChain `ChatGroq`: extraction/router `openai/gpt-oss-20b`, generation `openai/gpt-oss-120b`
- Hugging Face embeddings (`sentence-transformers/all-MiniLM-L6-v2`, 384-d) via `HuggingFaceEmbeddings`
- MCP-style tools in `mcp/` (in-process callables)
- Optional OpenTelemetry (OTLP to Collector → Jaeger traces, Prometheus metrics)

Chat roles (Groq): `EXTRACTION_MODEL` for resume/job structured extract, `ROUTER_MODEL` for document type and query intent, `GENERATION_MODEL` for answers. Groq on-demand gpt-oss models cap TPM at 8000 and count **prompt + declared max_tokens**; router/extraction always send a small `max_tokens`, generation caps at 1536, and RAG/indexing prompts are compacted so a single request stays under the limit. Structured LLM calls use Groq JSON schema mode (`strict=True`), not tool calling, because gpt-oss models often fail with `tool_use_failed`. Embeddings: any **sentence-transformers–compatible** Hugging Face model via `EMBEDDING_MODEL`; keep `EMBEDDING_DIM` in sync (MiniLM is 384).

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

## Observability

Ops telemetry is separate from product usage (`usage_events` / `GET /v1/usage`). Set `OTEL_ENABLED=true` and keep `OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318` (Collector HTTP). `docker compose up -d` starts Collector (4317/4318), Jaeger (http://localhost:16686), and Prometheus (http://localhost:9090). pytest and default `uvicorn` leave OTel off.

Exported signals: FastAPI + SQLAlchemy spans; `indexing.graph` / `rag.graph` parent spans; `llm.invoke` spans with `event_type`, model, and token counts; metrics `ci.llm.tokens`, `ci.llm.latency_ms`, `ci.indexing.duration_ms`, `ci.rag.duration_ms`, `ci.indexing.failures`. Do not put resume/JD text or chat questions on spans—IDs, models, event types, and token counts only.

## DeepEval goldenset

Opt-in live scores for indexing extract and RAG retrieve/generate, using [evals/goldensets/](../evals/goldensets/) against the sample resume and JD. Default `pytest` skips these tests.

```bash
pip install -e ".[eval]"
RUN_EVALS=1 pytest -m eval -q
```

Needs Postgres, `GROQ_API_KEY`, and the Hugging Face embedding model. The judge is the Groq router model. Thresholds are 0.5 (smoke eval, not a CI gate).

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
6. Faithfulness check (retry retrieval up to 2 times; skipped for interview topic chat)
7. Persist conversation + usage (one `usage_events` row per LLM call)

The graph starts at `identify_channel`. `channel=extract_topics` runs `extract_interview_topics` and exits. `channel=interview` loads the topic, then follows retrieve → generate → persist (no faithfulness). `channel=assistant` is the original path.

Chat REST/SSE and `chat.done` include `{ "tokens", "prompt_tokens", "completion_tokens" }` for that turn. Owner usage dashboard: `GET /v1/usage`. Conversations: `GET /v1/conversations` (recent **assistant** threads) and `GET /v1/conversations/<id>` (messages). Clear a thread with `DELETE /v1/conversations/<id>/messages` (keeps the conversation; interview `question_count` goes to 0). Interview topics: `GET /v1/topics` (`question_count` = user messages in that topic’s interview conversation).

```bash
curl -s -X POST http://localhost:8000/v1/chat \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"question":"What skills are on my resume?","resume_id":"<uuid>","job_ids":["<uuid>"],"stream":false,"temperature":0.7}'
```

SSE: `"stream": true` on `POST /v1/chat` yields `token` then `done` events.

WebSocket chat (`WS /v1/ws/chat?token=<jwt>`): send `{ "type": "chat.ask", "question": "...", "resume_id": "<uuid>", "job_ids": ["<uuid>"], "stream": true, "temperature": 0.7, "top_p": 1, "max_tokens": 1024, "system_prompt": "...", "model": "deep-research", "channel": "assistant" }`. Server replies `chat.status`, then `chat.token` chunks when `stream` is true, then `chat.done` (text, citations, strengths, gaps, conversation_id, usage). Errors are `{ "type": "chat.error", "detail": "..." }`. Generation uses Chat Settings: temperature, top-p, max tokens, and system instructions (plus the grounded-answer constraint).

`channel` is `assistant` (default), `interview`, or `extract_topics`:

- `extract_topics`: pass the assistant answer as `question`, plus `source_conversation_id` / `source_message_id`. Creates `topics` rows and interview conversations. `chat.done` includes `topics: [{ id, label, conversation_id }]`.
- `interview`: pass `topic_id` and the interview Chat Settings as `system_prompt`. Skips faithfulness retry. `chat.done` may include `table` and `code`.

Token tracking: each Groq structured call records prompt/completion tokens, model, and latency on `usage_events` (`indexing.route`, `indexing.extract_resume`, `indexing.extract_job`, `rag.query_understanding`, `rag.generate`, `rag.faithfulness`, `rag.extract_topics`). Each persist batch shares an `activity_id` and snapshots `feature` (`chat` | `interview` | `documents`) plus `details` (question text or `Processed resume (file.pdf)`) into `extra` so deleting a conversation or document does not change usage. Indexing also stores `document_id` / `filename` in `extra`.

Owner dashboard: `GET /v1/usage?range=30d` (`7d` | `30d` | `90d`). Response includes lifetime `total_tokens` / `by_event_type`, plus range `features`, `daily`, up to **5** `recent` activities, and `delta_percent` vs the previous window of the same length. Full activity table: `GET /v1/usage/activities?start=YYYY-MM-DD&end=YYYY-MM-DD`.

Skills profile: `GET /v1/skills` unions categorized skills from every owned `resume_profiles` row (max proficiency on name match). Legacy string skills map to Other Skills / proficiency 3. Also returns `skill_summary`, `insights`, and recent document activity.

```bash
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8000/v1/usage?range=30d"
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/v1/skills
```

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

RAG: `get_user_profile`, `fetch_document_metadata`, `fetch_structured_profiles`, `save_conversation_message`, `get_interview_topic`, `save_interview_topics`, `update_usage`.
