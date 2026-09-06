from __future__ import annotations

import re
import uuid
from collections.abc import Iterable
from uuid import UUID

from sqlalchemy import func
from sqlmodel import Session, select

from backend.api_schemas import TopicDetailOut, TopicOut
from backend.models import Conversation, ConversationKind, Message, MessageRole, Topic


_SLUG_RE = re.compile(r"[^a-z0-9]+")


def topic_slug(label: str) -> str:
    slug = _SLUG_RE.sub("-", label.strip().lower()).strip("-")
    return slug[:80] or "topic"


def unique_slug(db: Session, user_id: UUID, label: str) -> str:
    base = topic_slug(label)
    slug = base
    n = 2
    while db.exec(select(Topic).where(Topic.user_id == user_id, Topic.slug == slug)).first() is not None:
        slug = f"{base}-{n}"
        n += 1
    return slug


def conversation_for_topic(db: Session, topic_id: UUID) -> Conversation | None:
    return db.exec(select(Conversation).where(Conversation.topic_id == topic_id)).first()


def get_owned_topic(db: Session, user_id: UUID, topic_id: UUID) -> Topic | None:
    return db.exec(select(Topic).where(Topic.id == topic_id, Topic.user_id == user_id)).first()


def question_counts_by_conversation(db: Session, conversation_ids: Iterable[UUID]) -> dict[UUID, int]:
    ids = list(conversation_ids)
    if not ids:
        return {}
    rows = db.exec(
        select(Message.conversation_id, func.count())
        .where(Message.conversation_id.in_(ids), Message.role == MessageRole.user)
        .group_by(Message.conversation_id)
    ).all()
    return {conversation_id: int(count) for conversation_id, count in rows}


def topic_to_out(topic: Topic, conversation_id: UUID | None, question_count: int = 0) -> TopicOut:
    return TopicOut(
        id=topic.id,
        label=topic.label,
        slug=topic.slug,
        conversation_id=conversation_id,
        created_at=topic.created_at,
        question_count=question_count,
    )


def topic_to_detail(topic: Topic, conversation: Conversation | None, question_count: int = 0) -> TopicDetailOut:
    context = topic.context if isinstance(topic.context, dict) else {}
    return TopicDetailOut(
        id=topic.id,
        label=topic.label,
        slug=topic.slug,
        conversation_id=conversation.id if conversation else None,
        created_at=topic.created_at,
        question_count=question_count,
        context=context or None,
        resume_id=_as_uuid(context.get("resume_id")) if context else None,
        job_ids=_uuid_list(context.get("job_ids")) if context else [],
    )


def _as_uuid(value: object) -> UUID | None:
    if value is None or value == "":
        return None
    try:
        return UUID(str(value))
    except (TypeError, ValueError):
        return None


def _uuid_list(value: object) -> list[UUID]:
    if not isinstance(value, list):
        return []
    items: list[UUID] = []
    for item in value:
        parsed = _as_uuid(item)
        if parsed is not None:
            items.append(parsed)
    return items


def list_user_topics(db: Session, user_id: UUID) -> list[TopicOut]:
    topics = db.exec(select(Topic).where(Topic.user_id == user_id).order_by(Topic.created_at.desc())).all()
    conversations = {
        row.topic_id: row.id
        for row in db.exec(
            select(Conversation).where(
                Conversation.user_id == user_id,
                Conversation.kind == ConversationKind.interview,
                Conversation.topic_id.is_not(None),
            )
        ).all()
        if row.topic_id is not None
    }
    counts = question_counts_by_conversation(db, conversations.values())
    return [
        topic_to_out(
            topic,
            conversations.get(topic.id),
            counts.get(conversations[topic.id], 0) if topic.id in conversations else 0,
        )
        for topic in topics
    ]


def topic_payloads(db: Session, topics: list[Topic]) -> list[dict]:
    convos = {topic.id: conversation_for_topic(db, topic.id) for topic in topics}
    counts = question_counts_by_conversation(
        db, [convo.id for convo in convos.values() if convo is not None]
    )
    payload: list[dict] = []
    for topic in topics:
        convo = convos.get(topic.id)
        conversation_id = convo.id if convo else None
        payload.append(
            topic_to_out(
                topic,
                conversation_id,
                counts.get(conversation_id, 0) if conversation_id else 0,
            ).model_dump(mode="json")
        )
    return payload


def topics_for_source_message(db: Session, user_id: UUID, source_message_id: UUID | None) -> list[Topic]:
    if source_message_id is None:
        return []
    return list(
        db.exec(
            select(Topic)
            .where(Topic.user_id == user_id, Topic.source_message_id == source_message_id)
            .order_by(Topic.created_at.asc(), Topic.label.asc())
        ).all()
    )


def stamp_source_message_topics(db: Session, user_id: UUID, source_message_id: UUID | None, topics: list[Topic]) -> None:
    if source_message_id is None or not topics:
        return
    message = db.exec(
        select(Message).where(Message.id == source_message_id, Message.user_id == user_id)
    ).first()
    if message is None:
        return
    extra = dict(message.extra or {})
    extra["topics"] = topic_payloads(db, topics)
    message.extra = extra
    db.add(message)


def create_topics_from_labels(
    db: Session,
    *,
    user_id: UUID,
    labels: list[str],
    source_conversation_id: UUID | None,
    source_message_id: UUID | None,
    context: dict,
) -> list[Topic]:
    existing = topics_for_source_message(db, user_id, source_message_id)
    if existing:
        return existing

    created: list[Topic] = []
    seen: set[str] = set()
    for raw in labels:
        label = " ".join(raw.split()).strip()
        if not label:
            continue
        key = label.lower()
        if key in seen:
            continue
        seen.add(key)
        topic = Topic(
            id=uuid.uuid4(),
            user_id=user_id,
            label=label[:256],
            slug=unique_slug(db, user_id, label),
            source_conversation_id=source_conversation_id,
            source_message_id=source_message_id,
            context=context,
        )
        db.add(topic)
        db.flush()
        convo = Conversation(
            user_id=user_id,
            kind=ConversationKind.interview,
            topic_id=topic.id,
        )
        db.add(convo)
        db.flush()
        created.append(topic)
    stamp_source_message_topics(db, user_id, source_message_id, created)
    return created
