from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from backend.app import app
from backend.config import settings
from backend.db import session_scope
from backend.models import Document, DocumentStatus, DocType
from mcp.registry import tools
from tests.conftest import requires_postgres
from tests.test_auth import _register, auth_headers

client = TestClient(app)


@requires_postgres
def test_list_documents_empty():
    token = _register()["access_token"]
    response = client.get("/v1/documents", headers=auth_headers(token))
    assert response.status_code == 200
    assert response.json() == []


@requires_postgres
def test_list_documents_returns_user_files_newest_first():
    registered = _register()
    token = registered["access_token"]
    user_id = uuid.UUID(registered["user"]["id"])
    now = datetime.now(timezone.utc)

    with session_scope() as db:
        db.add(
            Document(
                user_id=user_id,
                doc_type=DocType.resume,
                filename="Ada_Resume.pdf",
                storage_path="/tmp/ada-resume.pdf",
                status=DocumentStatus.processed,
                size=245_760,
                created_at=now,
            )
        )
        db.add(
            Document(
                user_id=user_id,
                doc_type=DocType.job,
                filename="Staff_Engineer_JD.pdf",
                storage_path="/tmp/job.pdf",
                status=DocumentStatus.processing,
                size=800,
                created_at=now - timedelta(hours=2),
            )
        )

    other = _register()
    other_id = uuid.UUID(other["user"]["id"])
    with session_scope() as db:
        db.add(
            Document(
                user_id=other_id,
                doc_type=DocType.resume,
                filename="Other_Resume.pdf",
                storage_path="/tmp/other.pdf",
                status=DocumentStatus.processed,
                size=100,
            )
        )

    response = client.get("/v1/documents", headers=auth_headers(token))
    assert response.status_code == 200
    body = response.json()
    assert [row["filename"] for row in body] == ["Ada_Resume.pdf", "Staff_Engineer_JD.pdf"]
    assert body[0]["doc_type"] == "resume"
    assert body[0]["status"] == "processed"
    assert body[0]["created_at"]
    assert body[1]["doc_type"] == "job"
    assert body[1]["status"] == "processing"


@requires_postgres
def test_upload_document_then_list(monkeypatch, tmp_path: Path, sample_resume: Path):
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    monkeypatch.setattr("backend.routers.documents._run_indexing", lambda *_args, **_kwargs: None)
    token = _register()["access_token"]
    response = client.post(
        "/v1/documents",
        headers=auth_headers(token),
        files={"file": ("Ada_Resume.txt", sample_resume.read_bytes(), "text/plain")},
        data={"doc_type": "resume"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["filename"] == "Ada_Resume.txt"
    assert body["doc_type"] == "resume"
    assert body["status"] == "uploaded"

    listed = client.get("/v1/documents", headers=auth_headers(token))
    assert listed.status_code == 200
    assert listed.json()[0]["id"] == body["id"]


@requires_postgres
def test_document_status_websocket(monkeypatch, tmp_path: Path, sample_jd: Path):
    monkeypatch.setattr(settings, "data_dir", tmp_path)

    def fake_index(user_id: uuid.UUID, document_id: uuid.UUID) -> None:
        tools.invoke(
            "update_processing_status",
            user_id=user_id,
            document_id=document_id,
            status=DocumentStatus.processing,
        )
        tools.invoke(
            "update_processing_status",
            user_id=user_id,
            document_id=document_id,
            status=DocumentStatus.processed,
        )

    monkeypatch.setattr("backend.routers.documents._run_indexing", fake_index)

    with TestClient(app) as ws_client:
        token = ws_client.post(
            "/v1/auth/register",
            json={
                "full_name": "Ada Lovelace",
                "email": f"{uuid.uuid4()}@example.com",
                "password": "Passw0rd!",
            },
        ).json()["access_token"]
        with ws_client.websocket_connect(f"/v1/ws/documents?token={token}") as websocket:
            response = ws_client.post(
                "/v1/documents",
                headers=auth_headers(token),
                files={"file": ("job.txt", sample_jd.read_bytes(), "text/plain")},
                data={"doc_type": "job"},
            )
            assert response.status_code == 200, response.text
            statuses: list[str] = []
            while "processed" not in statuses:
                event = websocket.receive_json()
                assert event["type"] == "document.status"
                statuses.append(event["document"]["status"])
                assert len(statuses) <= 8
            assert statuses[0] == "uploaded"
            assert "processing" in statuses
            assert statuses[-1] == "processed"


@requires_postgres
def test_document_websocket_rejects_missing_token():
    with TestClient(app) as ws_client:
        try:
            with ws_client.websocket_connect("/v1/ws/documents") as websocket:
                websocket.receive_text()
            raise AssertionError("expected websocket to be rejected")
        except WebSocketDisconnect as exc:
            assert exc.code in {4401, 1008, 1006, 403}
        except Exception as exc:
            assert type(exc).__name__ in {"WebSocketDisconnect", "WebSocketDenialResponse"}


@requires_postgres
def test_delete_document_removes_file_and_row(monkeypatch, tmp_path: Path, sample_resume: Path):
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    monkeypatch.setattr("backend.routers.documents._run_indexing", lambda *_args, **_kwargs: None)
    token = _register()["access_token"]
    uploaded = client.post(
        "/v1/documents",
        headers=auth_headers(token),
        files={"file": ("Ada_Resume.txt", sample_resume.read_bytes(), "text/plain")},
        data={"doc_type": "resume"},
    )
    assert uploaded.status_code == 200, uploaded.text
    doc_id = uploaded.json()["id"]
    stored = tmp_path / "uploads"
    files = list(stored.rglob("*.txt"))
    assert files

    deleted = client.delete(f"/v1/documents/{doc_id}", headers=auth_headers(token))
    assert deleted.status_code == 204
    assert client.get("/v1/documents", headers=auth_headers(token)).json() == []
    assert not any(path.exists() for path in files)


@requires_postgres
def test_delete_job_document():
    registered = _register()
    token = registered["access_token"]
    user_id = uuid.UUID(registered["user"]["id"])
    doc_id = uuid.uuid4()
    with session_scope() as db:
        db.add(
            Document(
                id=doc_id,
                user_id=user_id,
                doc_type=DocType.job,
                filename="Staff_Engineer_JD.txt",
                storage_path="/tmp/missing-job.txt",
                status=DocumentStatus.processed,
                size=80,
            )
        )

    response = client.delete(f"/v1/documents/{doc_id}", headers=auth_headers(token))
    assert response.status_code == 204
    listed = client.get("/v1/documents", headers=auth_headers(token))
    assert listed.json() == []


@requires_postgres
def test_delete_document_hides_other_users_files():
    owner = _register()
    other = _register()
    owner_id = uuid.UUID(owner["user"]["id"])
    doc_id = uuid.uuid4()
    with session_scope() as db:
        db.add(
            Document(
                id=doc_id,
                user_id=owner_id,
                doc_type=DocType.resume,
                filename="Ada_Resume.pdf",
                storage_path="/tmp/ada-resume.pdf",
                status=DocumentStatus.processed,
                size=100,
            )
        )

    forbidden = client.delete(f"/v1/documents/{doc_id}", headers=auth_headers(other["access_token"]))
    assert forbidden.status_code == 404
    remaining = client.get("/v1/documents", headers=auth_headers(owner["access_token"]))
    assert [row["id"] for row in remaining.json()] == [str(doc_id)]


@requires_postgres
def test_delete_unknown_document_is_404():
    token = _register()["access_token"]
    response = client.delete(f"/v1/documents/{uuid.uuid4()}", headers=auth_headers(token))
    assert response.status_code == 404


@requires_postgres
def test_delete_document_requires_auth():
    response = client.delete(f"/v1/documents/{uuid.uuid4()}")
    assert response.status_code == 401


@requires_postgres
def test_delete_document_websocket_event(monkeypatch, tmp_path: Path, sample_jd: Path):
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    monkeypatch.setattr("backend.routers.documents._run_indexing", lambda *_args, **_kwargs: None)

    with TestClient(app) as ws_client:
        token = ws_client.post(
            "/v1/auth/register",
            json={
                "full_name": "Ada Lovelace",
                "email": f"{uuid.uuid4()}@example.com",
                "password": "Passw0rd!",
            },
        ).json()["access_token"]
        uploaded = ws_client.post(
            "/v1/documents",
            headers=auth_headers(token),
            files={"file": ("job.txt", sample_jd.read_bytes(), "text/plain")},
            data={"doc_type": "job"},
        )
        doc_id = uploaded.json()["id"]
        with ws_client.websocket_connect(f"/v1/ws/documents?token={token}") as websocket:
            deleted = ws_client.delete(f"/v1/documents/{doc_id}", headers=auth_headers(token))
            assert deleted.status_code == 204
            event = websocket.receive_json()
            assert event["type"] == "document.deleted"
            assert event["document_id"] == doc_id
