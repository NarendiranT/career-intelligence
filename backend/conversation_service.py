from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from uuid import UUID

from sqlmodel import Session, select

from backend.api_schemas import ConversationMessageOut, ConversationOut, CitationOut
from backend.models import Conversation, Message, MessageRole

TITLE_MAX_LEN = 80
RECENT_CONVERSATION_LIMIT = 5
SIDEBAR_CONVERSATION_LIMIT = 20


def conversation_title(text: str) -> str:
    first_line = text.strip().splitlines()[0] if text.strip() else "Conversation"
    if len(first_line) <= TITLE_MAX_LEN:
        return first_line
    return first_line[: TITLE_MAX_LEN - 1].rstrip() + "…"


def _messages_by_conversation(db: Session, conversation_ids: list[UUID]) -> dict[UUID, list[Message]]:
    grouped: dict[UUID, list[Message]] = defaultdict(list)
    if not conversation_ids:
        return grouped
    for message in db.exec(
        select(Message).where(Message.conversation_id.in_(conversation_ids)).order_by(Message.created_at.asc())
    ).all():
        grouped[message.conversation_id].append(message)
    return grouped


def _as_uuid(value: object) -> UUID | None:
    if value is None or value == "":
        return None
    try:
        return UUID(str(value))
    except (TypeError, ValueError):
        return None


def conversation_document_context(messages: list[Message]) -> tuple[UUID | None, list[UUID]]:
    for message in reversed(messages):
        if message.role != MessageRole.user:
            continue
        extra = message.extra or {}
        resume_id = _as_uuid(extra.get("resume_id"))
        job_ids: list[UUID] = []
        raw_jobs = extra.get("job_ids") or []
        if isinstance(raw_jobs, list):
            for item in raw_jobs:
                parsed = _as_uuid(item)
                if parsed is not None:
                    job_ids.append(parsed)
        if resume_id is not None or job_ids:
            return resume_id, job_ids
    return None, []


def conversation_to_out(convo: Conversation, messages: list[Message]) -> ConversationOut:
    first_user = next((m for m in messages if m.role == MessageRole.user), None)
    last_msg = messages[-1] if messages else None
    return ConversationOut(
        id=convo.id,
        title=conversation_title(first_user.content if first_user else ""),
        updated_at=(last_msg.created_at if last_msg else convo.created_at),
    )


def list_user_conversations(db: Session, user_id: UUID, *, limit: int) -> list[ConversationOut]:
    conversations = db.exec(select(Conversation).where(Conversation.user_id == user_id)).all()
    grouped = _messages_by_conversation(db, [row.id for row in conversations])
    items = [conversation_to_out(row, grouped.get(row.id, [])) for row in conversations]
    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)

    def sort_key(item: ConversationOut) -> datetime:
        stamp = item.updated_at
        if stamp is None:
            return epoch
        if stamp.tzinfo is None:
            return stamp.replace(tzinfo=timezone.utc)
        return stamp

    items.sort(key=sort_key, reverse=True)
    return items[:limit]


def get_owned_conversation(db: Session, user_id: UUID, conversation_id: UUID) -> Conversation | None:
    return db.exec(
        select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == user_id)
    ).first()


def message_to_out(message: Message) -> ConversationMessageOut:
    citations: list[CitationOut] = []
    for item in message.citations or []:
        if not isinstance(item, dict):
            continue
        citations.append(CitationOut(id=str(item.get("id") or ""), label=str(item.get("label") or "")))
    return ConversationMessageOut(
        id=message.id,
        role=message.role.value,
        content=message.content,
        citations=citations,
        extra=message.extra,
        created_at=message.created_at,
    )
