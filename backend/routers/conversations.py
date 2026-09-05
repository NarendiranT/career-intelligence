from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from backend.api_schemas import ConversationDetailOut, ConversationOut
from backend.conversation_service import (
    SIDEBAR_CONVERSATION_LIMIT,
    conversation_document_context,
    conversation_to_out,
    get_owned_conversation,
    list_user_conversations,
    message_to_out,
)
from backend.db import get_db
from backend.deps import get_user_id
from backend.models import Message

router = APIRouter(prefix="/v1/conversations", tags=["conversations"])


@router.get("", response_model=list[ConversationOut])
def list_conversations(
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_user_id),
) -> list[ConversationOut]:
    return list_user_conversations(db, user_id, limit=SIDEBAR_CONVERSATION_LIMIT)


@router.get("/{conversation_id}", response_model=ConversationDetailOut)
def get_conversation(
    conversation_id: UUID,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_user_id),
) -> ConversationDetailOut:
    convo = get_owned_conversation(db, user_id, conversation_id)
    if convo is None:
        raise HTTPException(status_code=404, detail="conversation not found")
    messages = db.exec(
        select(Message).where(Message.conversation_id == convo.id).order_by(Message.created_at.asc())
    ).all()
    rows = list(messages)
    summary = conversation_to_out(convo, rows)
    resume_id, job_ids = conversation_document_context(rows)
    return ConversationDetailOut(
        id=summary.id,
        title=summary.title,
        updated_at=summary.updated_at,
        resume_id=resume_id,
        job_ids=job_ids,
        messages=[message_to_out(row) for row in rows],
    )
