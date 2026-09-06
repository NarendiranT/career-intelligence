from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone

from fastapi.testclient import TestClient

from agent.usage import document_usage_details, feature_for_event, question_usage_details
from backend.app import app
from backend.db import session_scope
from backend.models import Conversation, Document, DocumentStatus, DocType, UsageEvent
from backend.usage_service import list_usage_activities, summarize_usage_events
from tests.conftest import requires_postgres
from tests.test_auth import _register, auth_headers

client = TestClient(app)


def test_feature_mapping_and_details():
    assert feature_for_event(event_type="indexing.extract_resume") == "documents"
    assert feature_for_event(event_type="rag.extract_topics") == "interview"
    assert feature_for_event(event_type="rag.generate", channel="interview") == "interview"
    assert feature_for_event(event_type="rag.generate") == "chat"
    assert document_usage_details("resume", "Narendiran_Resume.pdf") == "Processed resume (Narendiran_Resume.pdf)"
    assert question_usage_details("What skills are on my resume?") == "Asked about What skills are on my resume?"
    assert question_usage_details(None, extract_topics=True) == "Extracted interview topics"


def test_summarize_usage_groups_activities_and_range():
    now = datetime(2026, 9, 6, 12, tzinfo=timezone.utc)
    user_id = uuid.uuid4()
    events = [
        UsageEvent(
            user_id=user_id,
            event_type="rag.query_understanding",
            tokens=40,
            extra={
                "feature": "chat",
                "activity_id": "act-chat",
                "details": "Asked about system design",
                "input_tokens": 30,
                "output_tokens": 10,
            },
            created_at=now - timedelta(days=2),
        ),
        UsageEvent(
            user_id=user_id,
            event_type="rag.generate",
            tokens=280,
            extra={
                "feature": "chat",
                "activity_id": "act-chat",
                "details": "Asked about system design",
                "input_tokens": 200,
                "output_tokens": 80,
            },
            created_at=now - timedelta(days=2),
        ),
        UsageEvent(
            user_id=user_id,
            event_type="indexing.extract_resume",
            tokens=1200,
            extra={
                "feature": "documents",
                "activity_id": "act-doc",
                "details": "Processed resume (Narendiran_Resume.pdf)",
                "input_tokens": 1000,
                "output_tokens": 200,
            },
            created_at=now - timedelta(days=1),
        ),
        UsageEvent(
            user_id=user_id,
            event_type="rag.generate",
            tokens=50,
            extra={"feature": "interview", "activity_id": "act-old", "details": "Asked about Python"},
            created_at=now - timedelta(days=40),
        ),
    ]
    body = summarize_usage_events(events, range_key="30d", now=now)
    assert body.total_tokens == 1570
    assert body.range_tokens == 1520
    assert body.previous_range_tokens == 50
    assert body.delta_percent == 2940
    by_id = {row.id: row for row in body.features}
    assert by_id["chat"].tokens == 320
    assert by_id["chat"].activity_count == 1
    assert by_id["documents"].tokens == 1200
    assert by_id["documents"].activity_count == 1
    assert by_id["interview"].tokens == 0
    assert body.recent[0].details == "Processed resume (Narendiran_Resume.pdf)"
    assert body.recent[1].tokens == 320
    assert len(body.daily) == 30


def test_recent_usage_is_limited_to_five():
    now = datetime(2026, 9, 6, 12, tzinfo=timezone.utc)
    user_id = uuid.uuid4()
    events = [
        UsageEvent(
            user_id=user_id,
            event_type="rag.generate",
            tokens=10 + index,
            extra={"feature": "chat", "activity_id": f"act-{index}", "details": f"Asked {index}"},
            created_at=now - timedelta(days=index),
        )
        for index in range(8)
    ]
    body = summarize_usage_events(events, range_key="30d", now=now)
    assert len(body.recent) == 5
    assert [row.details for row in body.recent] == ["Asked 0", "Asked 1", "Asked 2", "Asked 3", "Asked 4"]


def test_list_usage_activities_filters_by_date():
    now = datetime(2026, 9, 6, 12, tzinfo=timezone.utc)
    user_id = uuid.uuid4()
    events = [
        UsageEvent(
            user_id=user_id,
            event_type="rag.generate",
            tokens=10,
            extra={"feature": "chat", "activity_id": "in-range", "details": "Asked in range"},
            created_at=now - timedelta(days=2),
        ),
        UsageEvent(
            user_id=user_id,
            event_type="rag.generate",
            tokens=20,
            extra={"feature": "chat", "activity_id": "out-range", "details": "Asked earlier"},
            created_at=now - timedelta(days=20),
        ),
    ]
    rows = list_usage_activities(
        events,
        start=date(2026, 9, 1),
        end=date(2026, 9, 6),
        now=now,
    )
    assert [row.details for row in rows] == ["Asked in range"]


@requires_postgres
def test_usage_summary_requires_auth():
    response = client.get("/v1/usage")
    assert response.status_code == 401


@requires_postgres
def test_usage_summary_aggregates_events():
    registered = _register()
    token = registered["access_token"]
    user_id = uuid.UUID(registered["user"]["id"])
    with session_scope() as db:
        db.add(
            UsageEvent(
                user_id=user_id,
                event_type="rag.generate",
                model="openai/gpt-oss-120b",
                tokens=30,
                extra={"input_tokens": 20, "output_tokens": 10, "feature": "chat", "activity_id": "a1", "details": "Asked about Python"},
            )
        )
        db.add(
            UsageEvent(
                user_id=user_id,
                event_type="indexing.extract_resume",
                model="openai/gpt-oss-20b",
                tokens=12,
                extra={"input_tokens": 8, "output_tokens": 4, "feature": "documents", "activity_id": "a2", "details": "Processed resume (resume.txt)"},
            )
        )

    empty = client.get("/v1/usage", headers=auth_headers(_register()["access_token"]))
    assert empty.status_code == 200
    assert empty.json()["total_tokens"] == 0
    assert empty.json()["range"] == "30d"

    response = client.get("/v1/usage?range=7d", headers=auth_headers(token))
    assert response.status_code == 200
    body = response.json()
    assert body["total_tokens"] == 42
    assert body["prompt_tokens"] == 28
    assert body["completion_tokens"] == 14
    assert body["event_count"] == 2
    assert body["range_tokens"] == 42
    by_type = {row["event_type"]: row for row in body["by_event_type"]}
    assert by_type["rag.generate"] == {"event_type": "rag.generate", "tokens": 30, "count": 1}
    assert by_type["indexing.extract_resume"]["tokens"] == 12
    features = {row["id"]: row for row in body["features"]}
    assert features["chat"]["tokens"] == 30
    assert features["documents"]["activity_count"] == 1
    assert len(body["recent"]) == 2


@requires_postgres
def test_usage_survives_document_and_conversation_delete():
    registered = _register()
    token = registered["access_token"]
    user_id = uuid.UUID(registered["user"]["id"])
    doc_id = uuid.uuid4()
    convo_id = uuid.uuid4()
    with session_scope() as db:
        db.add(
            Document(
                id=doc_id,
                user_id=user_id,
                doc_type=DocType.resume,
                filename="Narendiran_Resume.pdf",
                storage_path="/tmp/missing-resume.pdf",
                status=DocumentStatus.processed,
                size=100,
            )
        )
        db.add(Conversation(id=convo_id, user_id=user_id))
        db.add(
            UsageEvent(
                user_id=user_id,
                conversation_id=convo_id,
                event_type="rag.generate",
                tokens=320,
                extra={
                    "feature": "chat",
                    "activity_id": "keep-chat",
                    "details": "Asked about system design",
                    "input_tokens": 200,
                    "output_tokens": 120,
                },
            )
        )
        db.add(
            UsageEvent(
                user_id=user_id,
                event_type="indexing.extract_resume",
                tokens=1200,
                extra={
                    "document_id": str(doc_id),
                    "filename": "Narendiran_Resume.pdf",
                    "doc_type": "resume",
                    "feature": "documents",
                    "activity_id": "keep-doc",
                    "details": "Processed resume (Narendiran_Resume.pdf)",
                    "input_tokens": 1000,
                    "output_tokens": 200,
                },
            )
        )

    before = client.get("/v1/usage", headers=auth_headers(token))
    assert before.status_code == 200
    payload = before.json()
    assert payload["range_tokens"] == 1520
    details = {row["details"] for row in payload["recent"]}
    assert "Asked about system design" in details
    assert "Processed resume (Narendiran_Resume.pdf)" in details

    deleted_doc = client.delete(f"/v1/documents/{doc_id}", headers=auth_headers(token))
    assert deleted_doc.status_code == 204
    deleted_chat = client.delete(f"/v1/conversations/{convo_id}", headers=auth_headers(token))
    assert deleted_chat.status_code == 204

    after = client.get("/v1/usage", headers=auth_headers(token))
    assert after.status_code == 200
    assert after.json()["range_tokens"] == 1520
    assert after.json()["total_tokens"] == 1520
    remaining_details = {row["details"] for row in after.json()["recent"]}
    assert remaining_details == details


@requires_postgres
def test_usage_activities_endpoint_filters_and_requires_auth():
    assert client.get("/v1/usage/activities").status_code == 401
    registered = _register()
    token = registered["access_token"]
    user_id = uuid.UUID(registered["user"]["id"])
    with session_scope() as db:
        db.add(
            UsageEvent(
                user_id=user_id,
                event_type="rag.generate",
                tokens=40,
                extra={"feature": "chat", "activity_id": "keep", "details": "Asked about Python"},
            )
        )
    today = date.today().isoformat()
    response = client.get(f"/v1/usage/activities?start={today}&end={today}", headers=auth_headers(token))
    assert response.status_code == 200
    body = response.json()
    assert body["start"] == today
    assert body["end"] == today
    assert len(body["activities"]) == 1
    assert body["activities"][0]["details"] == "Asked about Python"
