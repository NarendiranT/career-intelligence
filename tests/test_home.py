from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from backend.app import app
from backend.db import session_scope
from backend.models import Conversation, Document, DocumentStatus, DocType, Message, MessageRole
from tests.conftest import requires_postgres
from tests.test_auth import _register, auth_headers

client = TestClient(app)


@requires_postgres
def test_home_requires_auth():
    response = client.get("/v1/home")
    assert response.status_code == 401


@requires_postgres
def test_home_empty_for_new_user():
    token = _register()["access_token"]
    response = client.get("/v1/home", headers=auth_headers(token))
    assert response.status_code == 200
    body = response.json()
    assert body["documents"] == []
    assert body["conversations"] == []
    assert body["stats"] == {
        "resume_count": 0,
        "job_count": 0,
        "insight_count": 0,
        "saved_result_count": 0,
    }


@requires_postgres
def test_home_summary_from_user_data():
    registered = _register()
    token = registered["access_token"]
    user_id = uuid.UUID(registered["user"]["id"])
    now = datetime.now(timezone.utc)

    with session_scope() as db:
        resume = Document(
            user_id=user_id,
            doc_type=DocType.resume,
            filename="Ada_Resume.pdf",
            storage_path="/tmp/ada-resume.pdf",
            status=DocumentStatus.processed,
            size=1200,
            created_at=now,
        )
        job = Document(
            user_id=user_id,
            doc_type=DocType.job,
            filename="Staff_Engineer_JD.pdf",
            storage_path="/tmp/job.pdf",
            status=DocumentStatus.processing,
            size=800,
            created_at=now - timedelta(hours=2),
        )
        extra_job = Document(
            user_id=user_id,
            doc_type=DocType.job,
            filename="Older_JD.pdf",
            storage_path="/tmp/old.pdf",
            status=DocumentStatus.processed,
            size=400,
            created_at=now - timedelta(days=3),
        )
        db.add(resume)
        db.add(job)
        db.add(extra_job)
        convo = Conversation(user_id=user_id, bookmarked=True)
        db.add(convo)
        db.flush()
        db.add(
            Message(
                conversation_id=convo.id,
                user_id=user_id,
                role=MessageRole.user,
                content="How well do I fit the Staff Engineer role?",
            )
        )
        db.add(
            Message(
                conversation_id=convo.id,
                user_id=user_id,
                role=MessageRole.assistant,
                content="You match several of the core requirements.",
            )
        )

    response = client.get("/v1/home", headers=auth_headers(token))
    assert response.status_code == 200
    body = response.json()
    assert body["stats"]["resume_count"] == 1
    assert body["stats"]["job_count"] == 2
    assert body["stats"]["insight_count"] == 1
    assert body["stats"]["saved_result_count"] == 1
    assert body["saved_results"][0]["title"] == "How well do I fit the Staff Engineer role?"
    assert body["saved_results"][0]["bookmarked"] is True
    assert [doc["filename"] for doc in body["documents"]] == [
        "Ada_Resume.pdf",
        "Staff_Engineer_JD.pdf",
        "Older_JD.pdf",
    ]
    assert body["documents"][0]["doc_type"] == "resume"
    assert body["documents"][0]["status"] == "processed"
    assert len(body["conversations"]) == 1
    assert body["conversations"][0]["title"] == "How well do I fit the Staff Engineer role?"
