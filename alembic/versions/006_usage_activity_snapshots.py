"""snapshot usage activity feature and details

Revision ID: 006_usage_activity_snapshots
Revises: 005_interview_topics
Create Date: 2026-09-06
"""

from __future__ import annotations

import json
import uuid
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "006_usage_activity_snapshots"
down_revision: Union[str, Sequence[str], None] = "005_interview_topics"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

CLUSTER_SECONDS = 2


def _aware(value: datetime | None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return dict(parsed) if isinstance(parsed, dict) else {}
    return {}


def _feature(event_type: str, extra: dict[str, Any], conversation_kind: str | None) -> str:
    if extra.get("feature") in {"chat", "interview", "documents"}:
        return str(extra["feature"])
    if (event_type or "").startswith("indexing."):
        return "documents"
    channel = extra.get("channel")
    if channel in {"interview", "extract_topics"} or event_type == "rag.extract_topics":
        return "interview"
    if conversation_kind == "interview":
        return "interview"
    return "chat"


def _default_details(feature: str) -> str:
    if feature == "interview":
        return "Interview Preparation"
    if feature == "documents":
        return "Document processing"
    return "Chat with Assistant"


def _cluster_key(row: dict[str, Any]) -> tuple[Any, ...]:
    extra = row["extra"]
    document_id = extra.get("document_id")
    if document_id:
        return ("document", row["user_id"], str(document_id))
    if row["conversation_id"] is not None:
        return ("conversation", row["user_id"], str(row["conversation_id"]))
    return ("event", row["user_id"], str(row["id"]))


def _clusters(rows: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[_cluster_key(row)].append(row)
    clusters: list[list[dict[str, Any]]] = []
    for key, items in grouped.items():
        ordered = sorted(items, key=lambda item: item["created_at"])
        if key[0] == "event":
            for item in ordered:
                clusters.append([item])
            continue
        current: list[dict[str, Any]] = []
        for item in ordered:
            if not current:
                current = [item]
                continue
            delta = (item["created_at"] - current[-1]["created_at"]).total_seconds()
            if delta <= CLUSTER_SECONDS:
                current.append(item)
            else:
                clusters.append(current)
                current = [item]
        if current:
            clusters.append(current)
    return clusters


def upgrade() -> None:
    conn = op.get_bind()
    events = conn.execute(
        sa.text(
            """
            SELECT e.id, e.user_id, e.conversation_id, e.event_type, e.model, e.tokens,
                   e.latency_ms, e.extra, e.created_at, c.kind AS conversation_kind
            FROM usage_events e
            LEFT JOIN conversations c ON c.id = e.conversation_id
            ORDER BY e.created_at
            """
        )
    ).mappings()
    rows: list[dict[str, Any]] = []
    for item in events:
        extra = _as_dict(item["extra"])
        created_at = _aware(item["created_at"])
        rows.append(
            {
                "id": item["id"],
                "user_id": item["user_id"],
                "conversation_id": item["conversation_id"],
                "event_type": item["event_type"],
                "extra": extra,
                "created_at": created_at,
                "conversation_kind": item["conversation_kind"],
            }
        )

    documents = {
        str(item["id"]): item
        for item in conn.execute(sa.text("SELECT id, filename, doc_type FROM documents")).mappings()
    }
    questions: dict[str, list[tuple[datetime, str]]] = defaultdict(list)
    for item in conn.execute(
        sa.text(
            """
            SELECT conversation_id, content, created_at
            FROM messages
            WHERE role = 'user'
            ORDER BY created_at
            """
        )
    ).mappings():
        questions[str(item["conversation_id"])].append((_aware(item["created_at"]), item["content"] or ""))

    updates: list[dict[str, Any]] = []
    for cluster in _clusters(rows):
        activity_id = None
        for item in cluster:
            existing = item["extra"].get("activity_id")
            if existing:
                activity_id = str(existing)
                break
        activity_id = activity_id or str(uuid.uuid4())
        sample = cluster[-1]
        extra = dict(sample["extra"])
        feature = _feature(sample["event_type"], extra, sample.get("conversation_kind"))
        details = str(extra.get("details") or "").strip()
        document_id = extra.get("document_id")
        if not details and document_id and str(document_id) in documents:
            doc = documents[str(document_id)]
            extra["filename"] = extra.get("filename") or doc["filename"]
            extra["doc_type"] = extra.get("doc_type") or doc["doc_type"]
            kind = "resume" if doc["doc_type"] == "resume" else "job description" if doc["doc_type"] == "job" else "document"
            filename = doc["filename"] or extra.get("filename")
            details = f"Processed {kind} ({filename})" if filename else f"Processed {kind}"
        if not details and sample["conversation_id"] is not None:
            convo_questions = questions.get(str(sample["conversation_id"])) or []
            stamp = sample["created_at"]
            nearest = ""
            for created_at, content in convo_questions:
                if created_at <= stamp + timedelta(seconds=2):
                    nearest = content
                else:
                    break
            if nearest.strip():
                details = "Asked about " + " ".join(nearest.split())
                if len(details) > 160:
                    details = details[:159].rstrip() + "…"
            elif feature == "interview" or extra.get("channel") == "extract_topics" or sample["event_type"] == "rag.extract_topics":
                details = "Extracted interview topics" if extra.get("channel") == "extract_topics" or sample["event_type"] == "rag.extract_topics" else _default_details(feature)
        if not details:
            details = _default_details(feature)
        for item in cluster:
            payload = dict(item["extra"])
            payload["activity_id"] = activity_id
            payload["feature"] = feature
            payload["details"] = details
            if extra.get("filename"):
                payload.setdefault("filename", extra["filename"])
            if extra.get("doc_type"):
                payload.setdefault("doc_type", extra["doc_type"])
            updates.append({"id": item["id"], "extra": json.dumps(payload)})

    for payload in updates:
        conn.execute(
            sa.text("UPDATE usage_events SET extra = CAST(:extra AS jsonb) WHERE id = :id"),
            payload,
        )

    existing_conversations = {
        str(item["conversation_id"])
        for item in conn.execute(
            sa.text("SELECT DISTINCT conversation_id FROM usage_events WHERE conversation_id IS NOT NULL")
        ).mappings()
        if item["conversation_id"] is not None
    }
    assistants = conn.execute(
        sa.text(
            """
            SELECT m.id, m.user_id, m.conversation_id, m.extra, m.created_at, c.kind
            FROM messages m
            JOIN conversations c ON c.id = m.conversation_id
            WHERE m.role = 'assistant'
            """
        )
    ).mappings()
    user_by_convo: dict[str, list[tuple[datetime, str]]] = questions
    inserts: list[dict[str, Any]] = []
    for item in assistants:
        convo_id = str(item["conversation_id"])
        if convo_id in existing_conversations:
            continue
        extra = _as_dict(item["extra"])
        usage = extra.get("usage") if isinstance(extra.get("usage"), dict) else {}
        tokens = int(usage.get("tokens") or 0)
        if tokens <= 0:
            continue
        created_at = _aware(item["created_at"])
        feature = "interview" if item["kind"] == "interview" else "chat"
        details = _default_details(feature)
        for stamp, content in user_by_convo.get(convo_id, []):
            if stamp <= created_at:
                text = " ".join((content or "").split())
                if text:
                    details = "Asked about " + text
                    if len(details) > 160:
                        details = details[:159].rstrip() + "…"
        activity_id = str(uuid.uuid4())
        inserts.append(
            {
                "id": str(uuid.uuid4()),
                "user_id": str(item["user_id"]),
                "conversation_id": convo_id,
                "event_type": "rag.generate",
                "tokens": tokens,
                "extra": json.dumps(
                    {
                        "input_tokens": int(usage.get("prompt_tokens") or 0),
                        "output_tokens": int(usage.get("completion_tokens") or 0),
                        "activity_id": activity_id,
                        "feature": feature,
                        "details": details,
                        "channel": feature,
                    }
                ),
                "created_at": created_at,
            }
        )
    for payload in inserts:
        conn.execute(
            sa.text(
                """
                INSERT INTO usage_events (id, user_id, conversation_id, event_type, tokens, extra, created_at)
                VALUES (CAST(:id AS uuid), CAST(:user_id AS uuid), CAST(:conversation_id AS uuid),
                        :event_type, :tokens, CAST(:extra AS jsonb), :created_at)
                """
            ),
            payload,
        )


def downgrade() -> None:
    return
