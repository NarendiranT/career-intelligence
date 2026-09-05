from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlmodel import select

from agent.schemas import JobProfile, ResumeProfile
from backend.db import session_scope
from backend.models import Chunk, Document, DocumentStatus, DocType, JobProfile as JobProfileRow
from backend.models import ResumeProfile as ResumeProfileRow
from backend.models import User

logger = logging.getLogger(__name__)


def create_or_update_user(
    *,
    user_id: uuid.UUID,
    email: str | None = None,
    full_name: str | None = None,
) -> dict[str, Any]:
    with session_scope() as db:
        user = db.get(User, user_id)
        resolved_email = (email or "").strip().lower() or f"user-{user_id}@local.invalid"
        if user is None:
            user = User(id=user_id, email=resolved_email, full_name=full_name or "")
            db.add(user)
            db.flush()
        else:
            if email:
                user.email = email.strip().lower()
            if full_name is not None:
                user.full_name = full_name
        return {"id": str(user.id), "email": user.email, "full_name": user.full_name}


def save_resume_profile(*, user_id: uuid.UUID, document_id: uuid.UUID, profile: ResumeProfile | dict[str, Any]) -> dict[str, Any]:
    parsed = profile if isinstance(profile, ResumeProfile) else ResumeProfile.model_validate(profile)
    payload = parsed.model_dump()
    with session_scope() as db:
        doc = db.exec(
            select(Document).where(Document.id == document_id, Document.user_id == user_id)
        ).first()
        if doc is None:
            raise ValueError("document not found for user")
        row = db.exec(
            select(ResumeProfileRow).where(ResumeProfileRow.document_id == document_id)
        ).first()
        if row is None:
            row = ResumeProfileRow(document_id=document_id, user_id=user_id)
            db.add(row)
        row.name = parsed.name
        row.headline = parsed.headline
        row.skills = parsed.skills
        row.payload = payload
        db.flush()
        return {"id": str(row.id), "document_id": str(document_id)}


def save_job_profile(*, user_id: uuid.UUID, document_id: uuid.UUID, profile: JobProfile | dict[str, Any]) -> dict[str, Any]:
    parsed = profile if isinstance(profile, JobProfile) else JobProfile.model_validate(profile)
    payload = parsed.model_dump()
    with session_scope() as db:
        doc = db.exec(
            select(Document).where(Document.id == document_id, Document.user_id == user_id)
        ).first()
        if doc is None:
            raise ValueError("document not found for user")
        row = db.exec(
            select(JobProfileRow).where(JobProfileRow.document_id == document_id)
        ).first()
        if row is None:
            row = JobProfileRow(document_id=document_id, user_id=user_id)
            db.add(row)
        row.title = parsed.title
        row.company = parsed.company
        row.skills = parsed.skills
        row.payload = payload
        db.flush()
        return {"id": str(row.id), "document_id": str(document_id)}


def update_processing_status(
    *,
    user_id: uuid.UUID,
    document_id: uuid.UUID,
    status: DocumentStatus | str,
    error_message: str | None = None,
    doc_type: DocType | str | None = None,
) -> dict[str, Any]:
    status_val = DocumentStatus(status)
    with session_scope() as db:
        doc = db.exec(
            select(Document).where(Document.id == document_id, Document.user_id == user_id)
        ).first()
        if doc is None:
            raise ValueError("document not found for user")
        doc.status = status_val
        doc.error_message = error_message
        if doc_type is not None:
            doc.doc_type = DocType(doc_type)
        return {"id": str(doc.id), "status": doc.status.value}


def replace_document_chunks(
    *,
    user_id: uuid.UUID,
    document_id: uuid.UUID,
    chunks: list[dict[str, Any]],
) -> dict[str, Any]:
    with session_scope() as db:
        doc = db.exec(
            select(Document).where(Document.id == document_id, Document.user_id == user_id)
        ).first()
        if doc is None:
            raise ValueError("document not found for user")
        existing = db.exec(select(Chunk).where(Chunk.document_id == document_id)).all()
        for row in existing:
            db.delete(row)
        db.flush()
        for item in chunks:
            db.add(
                Chunk(
                    document_id=document_id,
                    user_id=user_id,
                    content=item["content"],
                    embedding=item["embedding"],
                    chunk_metadata=item.get("metadata") or {},
                    ordinal=item.get("ordinal", 0),
                )
            )
        return {"count": len(chunks)}


def enrich_job_board(*, user_id: uuid.UUID, document_id: uuid.UUID) -> dict[str, Any]:
    logger.info("enrich_job_board stub skipped user=%s document=%s", user_id, document_id)
    return {"enriched": False, "source": None}
