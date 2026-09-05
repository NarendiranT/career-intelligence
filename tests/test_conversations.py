from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from backend.app import app
from backend.db import session_scope
from backend.models import Conversation, Message, MessageRole
from tests.conftest import requires_postgres
from tests.test_auth import _register, auth_headers

client = TestClient(app)


@requires_postgres
def test_conversations_require_auth():
    assert client.get("/v1/conversations").status_code == 401


@requires_postgres
def test_conversations_empty_for_new_user():
    token = _register()["access_token"]
    response = client.get("/v1/conversations", headers=auth_headers(token))
    assert response.status_code == 200
    assert response.json() == []


@requires_postgres
def test_conversations_list_and_detail():
    registered = _register()
    token = registered["access_token"]
    user_id = uuid.UUID(registered["user"]["id"])
    now = datetime.now(timezone.utc)
    other = _register()
    other_id = uuid.UUID(other["user"]["id"])

    with session_scope() as db:
        older = Conversation(user_id=user_id)
        newer = Conversation(user_id=user_id)
        foreign = Conversation(user_id=other_id)
        db.add(older)
        db.add(newer)
        db.add(foreign)
        db.flush()
        db.add(
            Message(
                conversation_id=older.id,
                user_id=user_id,
                role=MessageRole.user,
                content="Older question about Python",
                created_at=now - timedelta(hours=2),
            )
        )
        db.add(
            Message(
                conversation_id=newer.id,
                user_id=user_id,
                role=MessageRole.user,
                content="What skills am I missing?",
                extra={"resume_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", "job_ids": ["bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"]},
                created_at=now - timedelta(minutes=5),
            )
        )
        db.add(
            Message(
                conversation_id=newer.id,
                user_id=user_id,
                role=MessageRole.assistant,
                content="You should add Kubernetes.",
                citations=[{"id": "doc-1", "label": "resume.txt"}],
                extra={"strengths": ["Python"], "gaps": ["Kubernetes"]},
                created_at=now,
            )
        )
        db.add(
            Message(
                conversation_id=foreign.id,
                user_id=other_id,
                role=MessageRole.user,
                content="Secret thread",
            )
        )
        older_id = older.id
        newer_id = newer.id
        foreign_id = foreign.id

    listed = client.get("/v1/conversations", headers=auth_headers(token))
    assert listed.status_code == 200
    body = listed.json()
    assert [row["title"] for row in body] == ["What skills am I missing?", "Older question about Python"]
    assert body[0]["id"] == str(newer_id)

    detail = client.get(f"/v1/conversations/{newer_id}", headers=auth_headers(token))
    assert detail.status_code == 200
    payload = detail.json()
    assert payload["title"] == "What skills am I missing?"
    assert payload["resume_id"] == "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    assert payload["job_ids"] == ["bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"]
    assert [item["role"] for item in payload["messages"]] == ["user", "assistant"]
    assert payload["messages"][1]["content"] == "You should add Kubernetes."
    assert payload["messages"][1]["citations"][0]["label"] == "resume.txt"
    assert payload["messages"][1]["extra"]["strengths"] == ["Python"]

    missing = client.get(f"/v1/conversations/{foreign_id}", headers=auth_headers(token))
    assert missing.status_code == 404
    unknown = client.get(f"/v1/conversations/{uuid.uuid4()}", headers=auth_headers(token))
    assert unknown.status_code == 404
    assert client.get(f"/v1/conversations/{older_id}", headers=auth_headers(other["access_token"])).status_code == 404
