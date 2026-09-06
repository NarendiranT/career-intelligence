from __future__ import annotations

import uuid
from typing import Any

from sqlmodel import select

from backend.db import session_scope
from backend.models import Conversation, Document, JobProfile, Message, MessageRole, ResumeProfile, UsageEvent, User


def get_user_profile(*, user_id: uuid.UUID) -> dict[str, Any] | None:
    with session_scope() as db:
        user = db.get(User, user_id)
        if user is None:
            return None
        resume_count = db.exec(select(ResumeProfile).where(ResumeProfile.user_id == user_id)).all()
        job_count = db.exec(select(JobProfile).where(JobProfile.user_id == user_id)).all()
        return {
            "id": str(user.id),
            "email": user.email,
            "resume_count": len(resume_count),
            "job_count": len(job_count),
        }


def fetch_structured_profiles(*, user_id: uuid.UUID, document_ids: list[uuid.UUID]) -> dict[str, Any]:
    with session_scope() as db:
        filenames = {
            d.id: d.filename
            for d in db.exec(
                select(Document).where(Document.user_id == user_id, Document.id.in_(document_ids))
            ).all()
        }
        resumes = db.exec(
            select(ResumeProfile).where(
                ResumeProfile.user_id == user_id,
                ResumeProfile.document_id.in_(document_ids),
            )
        ).all()
        jobs = db.exec(
            select(JobProfile).where(
                JobProfile.user_id == user_id,
                JobProfile.document_id.in_(document_ids),
            )
        ).all()
        return {
            "resumes": [
                {
                    "document_id": str(r.document_id),
                    **(r.payload or {}),
                    "filename": filenames.get(r.document_id) or "",
                }
                for r in resumes
            ],
            "jobs": [
                {
                    "document_id": str(j.document_id),
                    **(j.payload or {}),
                    "filename": filenames.get(j.document_id) or "",
                }
                for j in jobs
            ],
        }


def fetch_document_metadata(*, user_id: uuid.UUID, document_ids: list[uuid.UUID] | None = None) -> list[dict[str, Any]]:
    with session_scope() as db:
        stmt = select(Document).where(Document.user_id == user_id)
        if document_ids:
            stmt = stmt.where(Document.id.in_(document_ids))
        docs = db.exec(stmt).all()
        return [
            {
                "id": str(d.id),
                "filename": d.filename,
                "doc_type": d.doc_type.value if d.doc_type else None,
                "status": d.status.value,
                "size": d.size,
            }
            for d in docs
        ]


def save_conversation_message(
    *,
    user_id: uuid.UUID,
    conversation_id: uuid.UUID | None,
    role: str,
    content: str,
    citations: list[dict[str, Any]] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    with session_scope() as db:
        convo = None
        if conversation_id is not None:
            convo = db.exec(
                select(Conversation).where(
                    Conversation.id == conversation_id,
                    Conversation.user_id == user_id,
                )
            ).first()
        if convo is None:
            convo = Conversation(id=conversation_id or uuid.uuid4(), user_id=user_id)
            db.add(convo)
            db.flush()
        msg = Message(
            conversation_id=convo.id,
            user_id=user_id,
            role=MessageRole(role),
            content=content,
            citations=citations,
            extra=extra,
        )
        db.add(msg)
        db.flush()
        return {
            "conversation_id": str(convo.id),
            "message_id": str(msg.id),
        }


def update_usage(
    *,
    user_id: uuid.UUID,
    conversation_id: uuid.UUID | None = None,
    event_type: str = "chat",
    model: str | None = None,
    tokens: int | None = None,
    latency_ms: float | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    with session_scope() as db:
        event = UsageEvent(
            user_id=user_id,
            conversation_id=conversation_id,
            event_type=event_type,
            model=model,
            tokens=tokens,
            latency_ms=latency_ms,
            extra=extra,
        )
        db.add(event)
        db.flush()
        return {"id": str(event.id)}


def get_interview_topic(*, user_id: uuid.UUID, topic_id: uuid.UUID) -> dict[str, Any] | None:
    from backend.topic_service import (
        conversation_for_topic,
        get_owned_topic,
        question_counts_by_conversation,
        topic_to_detail,
    )

    with session_scope() as db:
        topic = get_owned_topic(db, user_id, topic_id)
        if topic is None:
            return None
        conversation = conversation_for_topic(db, topic.id)
        question_count = 0
        if conversation is not None:
            question_count = question_counts_by_conversation(db, [conversation.id]).get(conversation.id, 0)
        detail = topic_to_detail(topic, conversation, question_count)
        return detail.model_dump(mode="json")


def list_interview_topics_for_source(
    *,
    user_id: uuid.UUID,
    source_message_id: uuid.UUID | None = None,
) -> list[dict[str, Any]]:
    from backend.topic_service import topic_payloads, topics_for_source_message

    with session_scope() as db:
        topics = topics_for_source_message(db, user_id, source_message_id)
        return topic_payloads(db, topics)


def save_interview_topics(
    *,
    user_id: uuid.UUID,
    labels: list[str],
    source_conversation_id: uuid.UUID | None = None,
    source_message_id: uuid.UUID | None = None,
    context: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    from backend.topic_service import create_topics_from_labels, topic_payloads

    with session_scope() as db:
        topics = create_topics_from_labels(
            db,
            user_id=user_id,
            labels=labels,
            source_conversation_id=source_conversation_id,
            source_message_id=source_message_id,
            context=context or {},
        )
        return topic_payloads(db, topics)
