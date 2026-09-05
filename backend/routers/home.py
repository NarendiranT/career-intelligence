from __future__ import annotations

from collections import defaultdict
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlmodel import Session, select

from backend.api_schemas import HomeConversationOut, HomeStatsOut, HomeSummaryOut
from backend.db import get_db
from backend.deps import get_user_id
from backend.models import Conversation, Document, DocType, Message, MessageRole
from backend.serializers import document_to_out

router = APIRouter(prefix="/v1/home", tags=["home"])

RECENT_DOCUMENT_LIMIT = 4
RECENT_CONVERSATION_LIMIT = 5
TITLE_MAX_LEN = 80


def _conversation_title(text: str) -> str:
    first_line = text.strip().splitlines()[0] if text.strip() else "Conversation"
    if len(first_line) <= TITLE_MAX_LEN:
        return first_line
    return first_line[: TITLE_MAX_LEN - 1].rstrip() + "…"


@router.get("", response_model=HomeSummaryOut)
def home_summary(
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_user_id),
) -> HomeSummaryOut:
    documents = db.exec(
        select(Document).where(Document.user_id == user_id).order_by(Document.created_at.desc())
    ).all()
    resume_count = sum(1 for row in documents if row.doc_type == DocType.resume)
    job_count = sum(1 for row in documents if row.doc_type == DocType.job)
    insight_count = db.exec(
        select(func.count())
        .select_from(Message)
        .where(Message.user_id == user_id, Message.role == MessageRole.assistant)
    ).one()

    conversations = db.exec(
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .order_by(Conversation.created_at.desc())
        .limit(RECENT_CONVERSATION_LIMIT)
    ).all()
    conversation_ids = [row.id for row in conversations]
    messages_by_convo: dict[UUID, list[Message]] = defaultdict(list)
    if conversation_ids:
        for message in db.exec(
            select(Message)
            .where(Message.conversation_id.in_(conversation_ids))
            .order_by(Message.created_at.asc())
        ).all():
            messages_by_convo[message.conversation_id].append(message)

    conversation_out: list[HomeConversationOut] = []
    for convo in conversations:
        msgs = messages_by_convo.get(convo.id, [])
        first_user = next((m for m in msgs if m.role == MessageRole.user), None)
        last_msg = msgs[-1] if msgs else None
        title = _conversation_title(first_user.content if first_user else "")
        conversation_out.append(
            HomeConversationOut(
                id=convo.id,
                title=title,
                updated_at=(last_msg.created_at if last_msg else convo.created_at),
            )
        )

    return HomeSummaryOut(
        documents=[document_to_out(row) for row in documents[:RECENT_DOCUMENT_LIMIT]],
        stats=HomeStatsOut(
            resume_count=resume_count,
            job_count=job_count,
            insight_count=int(insight_count or 0),
            saved_result_count=0,
        ),
        conversations=conversation_out,
    )
