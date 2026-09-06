from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlmodel import Session, select

from backend.api_schemas import HomeStatsOut, HomeSummaryOut
from backend.conversation_service import RECENT_CONVERSATION_LIMIT, list_user_conversations
from backend.db import get_db
from backend.deps import get_user_id
from backend.models import Conversation, Document, DocType, Message, MessageRole
from backend.serializers import document_to_out

router = APIRouter(prefix="/v1/home", tags=["home"])

RECENT_DOCUMENT_LIMIT = 4


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
    saved_result_count = db.exec(
        select(func.count())
        .select_from(Conversation)
        .where(Conversation.user_id == user_id, Conversation.bookmarked.is_(True))
    ).one()

    return HomeSummaryOut(
        documents=[document_to_out(row) for row in documents[:RECENT_DOCUMENT_LIMIT]],
        stats=HomeStatsOut(
            resume_count=resume_count,
            job_count=job_count,
            insight_count=int(insight_count or 0),
            saved_result_count=int(saved_result_count or 0),
        ),
        conversations=list_user_conversations(db, user_id, limit=RECENT_CONVERSATION_LIMIT),
        saved_results=list_user_conversations(
            db, user_id, limit=RECENT_CONVERSATION_LIMIT, bookmarked=True
        ),
    )
