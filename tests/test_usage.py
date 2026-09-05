from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from backend.app import app
from backend.db import session_scope
from backend.models import UsageEvent
from tests.conftest import requires_postgres
from tests.test_auth import _register, auth_headers

client = TestClient(app)


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
                extra={"input_tokens": 20, "output_tokens": 10},
            )
        )
        db.add(
            UsageEvent(
                user_id=user_id,
                event_type="indexing.extract_resume",
                model="openai/gpt-oss-20b",
                tokens=12,
                extra={"input_tokens": 8, "output_tokens": 4},
            )
        )

    empty = client.get("/v1/usage", headers=auth_headers(_register()["access_token"]))
    assert empty.status_code == 200
    assert empty.json()["total_tokens"] == 0

    response = client.get("/v1/usage", headers=auth_headers(token))
    assert response.status_code == 200
    body = response.json()
    assert body["total_tokens"] == 42
    assert body["prompt_tokens"] == 28
    assert body["completion_tokens"] == 14
    assert body["event_count"] == 2
    by_type = {row["event_type"]: row for row in body["by_event_type"]}
    assert by_type["rag.generate"] == {"event_type": "rag.generate", "tokens": 30, "count": 1}
    assert by_type["indexing.extract_resume"]["tokens"] == 12
