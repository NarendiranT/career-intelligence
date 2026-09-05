from __future__ import annotations

from fastapi.testclient import TestClient
import pytest

from backend.app import app
from tests.conftest import postgres_available, requires_postgres
from tests.test_auth import _register, auth_headers

client = TestClient(app)


@requires_postgres
def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_chat_rejects_empty_question():
    if not postgres_available():
        pytest.skip("postgres is not running")
    token = _register()["access_token"]
    response = client.post(
        "/v1/chat",
        json={"question": " ", "stream": False},
        headers=auth_headers(token),
    )
    assert response.status_code == 400


def test_openapi_includes_agent_routes():
    paths = client.app.openapi()["paths"]
    assert "/v1/documents/{document_id}" in paths
    assert "/v1/documents/{document_id}/file" in paths
    assert "/v1/chat" in paths
    assert "/v1/auth/register" in paths
    assert "/v1/auth/login" in paths
    assert "/v1/auth/me" in paths
    assert "/v1/home" in paths
    assert "/health" in paths

