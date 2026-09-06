from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from backend.app import app
from backend.db import session_scope
from backend.models import Document, DocumentStatus, DocType, ResumeProfile
from tests.conftest import requires_postgres
from tests.test_auth import _register, auth_headers

client = TestClient(app)


@requires_postgres
def test_skills_requires_auth():
    response = client.get("/v1/skills")
    assert response.status_code == 401


@requires_postgres
def test_skills_empty_for_new_user():
    token = _register()["access_token"]
    response = client.get("/v1/skills", headers=auth_headers(token))
    assert response.status_code == 200
    body = response.json()
    assert body["resume_count"] == 0
    assert body["total_skills"] == 0
    assert body["categories"] == []
    assert body["insights"] == []
    assert body["recent_activity"] == []
    assert "resume" in body["skill_summary"].lower()


@requires_postgres
def test_skills_merges_all_resumes():
    registered = _register()
    token = registered["access_token"]
    user_id = uuid.UUID(registered["user"]["id"])
    now = datetime.now(timezone.utc)

    with session_scope() as db:
        first_doc = Document(
            user_id=user_id,
            doc_type=DocType.resume,
            filename="Ada_Resume.pdf",
            storage_path="/tmp/ada-resume.pdf",
            status=DocumentStatus.processed,
            size=1200,
            created_at=now,
        )
        second_doc = Document(
            user_id=user_id,
            doc_type=DocType.resume,
            filename="Ada_Resume_v2.pdf",
            storage_path="/tmp/ada-resume-v2.pdf",
            status=DocumentStatus.processed,
            size=1400,
            created_at=now - timedelta(days=1),
        )
        job = Document(
            user_id=user_id,
            doc_type=DocType.job,
            filename="Staff_Engineer_JD.pdf",
            storage_path="/tmp/job.pdf",
            status=DocumentStatus.processed,
            size=800,
            created_at=now - timedelta(hours=2),
        )
        db.add(first_doc)
        db.add(second_doc)
        db.add(job)
        db.flush()
        db.add(
            ResumeProfile(
                document_id=first_doc.id,
                user_id=user_id,
                name="Ada",
                headline="Engineer",
                skills=[
                    {"name": "Python", "category": "Programming Languages", "proficiency": 4},
                    {"name": "AWS", "category": "Cloud & DevOps", "proficiency": 3},
                ],
                payload={
                    "skill_summary": "Backend-focused engineer with growing cloud skills.",
                    "insights": ["Strong Python experience", "Growing AWS skills"],
                    "skills": [
                        {"name": "Python", "category": "Programming Languages", "proficiency": 4},
                        {"name": "AWS", "category": "Cloud & DevOps", "proficiency": 3},
                    ],
                },
            )
        )
        db.add(
            ResumeProfile(
                document_id=second_doc.id,
                user_id=user_id,
                name="Ada Lovelace",
                skills=["Python", "FastAPI"],
                payload={
                    "insights": ["Strong Python experience", "Builds APIs with FastAPI"],
                    "skills": ["Python", "FastAPI"],
                },
            )
        )

    other = _register()
    other_id = uuid.UUID(other["user"]["id"])
    with session_scope() as db:
        other_doc = Document(
            user_id=other_id,
            doc_type=DocType.resume,
            filename="Other.pdf",
            storage_path="/tmp/other.pdf",
            status=DocumentStatus.processed,
            size=100,
        )
        db.add(other_doc)
        db.flush()
        db.add(
            ResumeProfile(
                document_id=other_doc.id,
                user_id=other_id,
                skills=[{"name": "Go", "category": "Programming Languages", "proficiency": 5}],
                payload={"skills": [{"name": "Go", "category": "Programming Languages", "proficiency": 5}]},
            )
        )

    response = client.get("/v1/skills", headers=auth_headers(token))
    assert response.status_code == 200
    body = response.json()
    assert body["resume_count"] == 2
    assert body["total_skills"] == 3
    assert body["skill_summary"] == "Backend-focused engineer with growing cloud skills."
    assert body["insights"] == ["Strong Python experience", "Growing AWS skills", "Builds APIs with FastAPI"]
    by_category = {row["name"]: row["skills"] for row in body["categories"]}
    python = next(item for item in by_category["Programming Languages"] if item["name"] == "Python")
    assert python["proficiency"] == 4
    fastapi = next(item for item in by_category["Other Skills"] if item["name"] == "FastAPI")
    assert fastapi["proficiency"] == 3
    assert by_category["Cloud & DevOps"][0]["name"] == "AWS"
    kinds = [row["kind"] for row in body["recent_activity"]]
    assert "resume_uploaded" in kinds
    assert "analysis_completed" in kinds
    assert "job_uploaded" in kinds
    assert body["recent_activity"][0]["detail"] == "Ada_Resume.pdf"
