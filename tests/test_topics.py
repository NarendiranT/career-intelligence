from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from backend.app import app
from backend.db import session_scope
from backend.models import Conversation, ConversationKind, Message, MessageRole, Topic
from tests.conftest import requires_postgres
from tests.test_auth import _register, auth_headers

client = TestClient(app)


@requires_postgres
def test_topics_require_auth():
    assert client.get("/v1/topics").status_code == 401


@requires_postgres
def test_topics_empty_for_new_user():
    token = _register()["access_token"]
    response = client.get("/v1/topics", headers=auth_headers(token))
    assert response.status_code == 200
    assert response.json() == []


@requires_postgres
def test_list_get_and_delete_topics_are_owner_scoped():
    registered = _register()
    token = registered["access_token"]
    user_id = uuid.UUID(registered["user"]["id"])
    other = _register()["access_token"]

    with session_scope() as db:
        topic = Topic(user_id=user_id, label="Python", slug="python", context={"resume_id": None, "job_ids": []})
        db.add(topic)
        db.flush()
        convo = Conversation(user_id=user_id, kind=ConversationKind.interview, topic_id=topic.id)
        db.add(convo)
        db.flush()
        topic_id = topic.id
        convo_id = convo.id

    listed = client.get("/v1/topics", headers=auth_headers(token))
    assert listed.status_code == 200
    body = listed.json()
    assert len(body) == 1
    assert body[0]["label"] == "Python"
    assert body[0]["conversation_id"] == str(convo_id)
    assert body[0]["question_count"] == 0

    detail = client.get(f"/v1/topics/{topic_id}", headers=auth_headers(token))
    assert detail.status_code == 200
    assert detail.json()["conversation_id"] == str(convo_id)

    assert client.get(f"/v1/topics/{topic_id}", headers=auth_headers(other)).status_code == 404
    assert client.delete(f"/v1/topics/{topic_id}", headers=auth_headers(other)).status_code == 404

    removed = client.delete(f"/v1/topics/{topic_id}", headers=auth_headers(token))
    assert removed.status_code == 204
    assert client.get("/v1/topics", headers=auth_headers(token)).json() == []


@requires_postgres
def test_assistant_conversation_list_excludes_interview_kind():
    registered = _register()
    token = registered["access_token"]
    user_id = uuid.UUID(registered["user"]["id"])

    with session_scope() as db:
        assistant = Conversation(user_id=user_id, kind=ConversationKind.assistant)
        db.add(assistant)
        db.flush()
        db.add(
            Message(
                conversation_id=assistant.id,
                user_id=user_id,
                role=MessageRole.user,
                content="What skills am I missing?",
            )
        )
        topic = Topic(user_id=user_id, label="SQL", slug="sql")
        db.add(topic)
        db.flush()
        interview = Conversation(user_id=user_id, kind=ConversationKind.interview, topic_id=topic.id)
        db.add(interview)
        db.flush()
        db.add(
            Message(
                conversation_id=interview.id,
                user_id=user_id,
                role=MessageRole.user,
                content="Explain indexes",
            )
        )
        assistant_id = assistant.id

    listed = client.get("/v1/conversations", headers=auth_headers(token))
    assert listed.status_code == 200
    ids = [row["id"] for row in listed.json()]
    assert ids == [str(assistant_id)]


@requires_postgres
def test_topic_question_count_is_user_messages():
    registered = _register()
    token = registered["access_token"]
    user_id = uuid.UUID(registered["user"]["id"])

    with session_scope() as db:
        topic = Topic(user_id=user_id, label="System Design", slug="system-design")
        db.add(topic)
        db.flush()
        convo = Conversation(user_id=user_id, kind=ConversationKind.interview, topic_id=topic.id)
        db.add(convo)
        db.flush()
        for content in ("What is CAP?", "Explain sharding", "Walk through rate limiting"):
            db.add(
                Message(
                    conversation_id=convo.id,
                    user_id=user_id,
                    role=MessageRole.user,
                    content=content,
                )
            )
        db.add(
            Message(
                conversation_id=convo.id,
                user_id=user_id,
                role=MessageRole.assistant,
                content="CAP is consistency, availability, partition tolerance.",
            )
        )
        topic_id = topic.id

    listed = client.get("/v1/topics", headers=auth_headers(token))
    assert listed.status_code == 200
    assert listed.json()[0]["question_count"] == 3

    detail = client.get(f"/v1/topics/{topic_id}", headers=auth_headers(token))
    assert detail.status_code == 200
    assert detail.json()["question_count"] == 3

    listed_ids = listed.json()
    convo_id = listed_ids[0]["conversation_id"]
    cleared = client.delete(f"/v1/conversations/{convo_id}/messages", headers=auth_headers(token))
    assert cleared.status_code == 204
    assert client.get("/v1/topics", headers=auth_headers(token)).json()[0]["question_count"] == 0
