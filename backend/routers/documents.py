from __future__ import annotations

import logging
import uuid
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Response, UploadFile
from fastapi.responses import FileResponse
from sqlmodel import Session, select

from agent.indexing.graph import indexing_graph
from backend.api_schemas import DocumentOut
from backend.config import settings
from backend.db import get_db
from backend.deps import get_user_id
from backend.errors import MissingLLMConfigError
from backend.models import Document, DocumentStatus, DocType
from backend.realtime import publish_document_deleted, publish_document_status
from backend.serializers import document_to_out
from mcp.registry import tools

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/documents", tags=["documents"])

ALLOWED_SUFFIXES = {".pdf", ".docx", ".txt", ".doc"}


def _run_indexing(user_id: UUID, document_id: UUID) -> None:
    try:
        indexing_graph.invoke({"user_id": str(user_id), "document_id": str(document_id)})
    except MissingLLMConfigError as exc:
        tools.invoke(
            "update_processing_status",
            user_id=user_id,
            document_id=document_id,
            status=DocumentStatus.failed,
            error_message=str(exc),
        )
    except Exception:
        logger.exception("Indexing failed for %s", document_id)
        tools.invoke(
            "update_processing_status",
            user_id=user_id,
            document_id=document_id,
            status=DocumentStatus.failed,
            error_message="indexing failed",
        )


@router.post("", response_model=DocumentOut)
async def upload_document(
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_user_id),
    file: UploadFile = File(...),
    doc_type: str | None = Form(default=None),
) -> DocumentOut:
    filename = file.filename or "upload.bin"
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(status_code=400, detail="unsupported file type")
    data = await file.read()
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(status_code=400, detail="file exceeds 10 MB")
    parsed_type: DocType | None = None
    if doc_type:
        if doc_type not in {DocType.resume.value, DocType.job.value}:
            raise HTTPException(status_code=400, detail="doc_type must be resume or job")
        parsed_type = DocType(doc_type)

    dest_dir = settings.uploads_dir / str(user_id)
    dest_dir.mkdir(parents=True, exist_ok=True)
    document_id = uuid.uuid4()
    dest = dest_dir / f"{document_id}{suffix}"
    dest.write_bytes(data)

    doc = Document(
        id=document_id,
        user_id=user_id,
        doc_type=parsed_type,
        filename=filename,
        storage_path=str(dest),
        status=DocumentStatus.uploaded,
        mime=file.content_type,
        size=len(data),
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    out = document_to_out(doc)
    publish_document_status(user_id, out.model_dump(mode="json"))
    background.add_task(_run_indexing, user_id, document_id)
    return out


@router.get("", response_model=list[DocumentOut])
def list_documents(
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_user_id),
) -> list[DocumentOut]:
    rows = db.exec(
        select(Document).where(Document.user_id == user_id).order_by(Document.created_at.desc())
    ).all()
    return [document_to_out(row) for row in rows]


def _unlink_storage(storage_path: str) -> None:
    path = Path(storage_path)
    try:
        path.unlink(missing_ok=True)
    except OSError:
        logger.warning("Could not remove stored file %s", path, exc_info=True)


@router.get("/{document_id}/file")
def get_document_file(
    document_id: UUID,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_user_id),
) -> FileResponse:
    doc = db.exec(
        select(Document).where(Document.id == document_id, Document.user_id == user_id)
    ).first()
    if doc is None:
        raise HTTPException(status_code=404, detail="document not found")
    path = Path(doc.storage_path)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="file not found")
    return FileResponse(
        path,
        media_type=doc.mime or "application/octet-stream",
        filename=doc.filename,
        content_disposition_type="inline",
    )


@router.delete("/{document_id}", status_code=204)
def delete_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_user_id),
) -> Response:
    doc = db.exec(
        select(Document).where(Document.id == document_id, Document.user_id == user_id)
    ).first()
    if doc is None:
        raise HTTPException(status_code=404, detail="document not found")
    storage_path = doc.storage_path
    db.delete(doc)
    db.commit()
    _unlink_storage(storage_path)
    publish_document_deleted(user_id, document_id)
    return Response(status_code=204)
