from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlmodel import Session

from backend.api_schemas import TopicDetailOut, TopicOut
from backend.db import get_db
from backend.deps import get_user_id
from backend.topic_service import (
    conversation_for_topic,
    get_owned_topic,
    list_user_topics,
    question_counts_by_conversation,
    topic_to_detail,
)

router = APIRouter(prefix="/v1/topics", tags=["topics"])


@router.get("", response_model=list[TopicOut])
def list_topics(
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_user_id),
) -> list[TopicOut]:
    return list_user_topics(db, user_id)


@router.get("/{topic_id}", response_model=TopicDetailOut)
def get_topic(
    topic_id: UUID,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_user_id),
) -> TopicDetailOut:
    topic = get_owned_topic(db, user_id, topic_id)
    if topic is None:
        raise HTTPException(status_code=404, detail="topic not found")
    conversation = conversation_for_topic(db, topic.id)
    question_count = 0
    if conversation is not None:
        question_count = question_counts_by_conversation(db, [conversation.id]).get(conversation.id, 0)
    return topic_to_detail(topic, conversation, question_count)


@router.delete("/{topic_id}", status_code=204)
def delete_topic(
    topic_id: UUID,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_user_id),
) -> Response:
    topic = get_owned_topic(db, user_id, topic_id)
    if topic is None:
        raise HTTPException(status_code=404, detail="topic not found")
    db.delete(topic)
    db.commit()
    return Response(status_code=204)
