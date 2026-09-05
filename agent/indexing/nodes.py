from __future__ import annotations

import logging
import uuid
from typing import Any, TypedDict

from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlmodel import select

from agent.indexing.loaders import extract_text
from agent.llm import get_chat_model, get_embeddings
from agent.schemas import DocumentClassification, JobProfile, ResumeProfile
from backend.db import session_scope
from backend.models import Document, DocumentStatus
from mcp.registry import tools

logger = logging.getLogger(__name__)

SPLITTER = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=120)


class IndexingState(TypedDict, total=False):
    document_id: str
    user_id: str
    raw_text: str
    filename: str
    doc_type: str
    profile: dict[str, Any]
    chunks: list[dict[str, Any]]
    error: str


def _ids(state: IndexingState) -> tuple[uuid.UUID, uuid.UUID]:
    return uuid.UUID(state["user_id"]), uuid.UUID(state["document_id"])


def load_document(state: IndexingState) -> dict[str, Any]:
    user_id, document_id = _ids(state)
    tools.invoke(
        "update_processing_status",
        user_id=user_id,
        document_id=document_id,
        status=DocumentStatus.processing,
    )
    with session_scope() as db:
        doc = db.exec(
            select(Document).where(Document.id == document_id, Document.user_id == user_id)
        ).first()
        if doc is None:
            return {"error": "document not found"}
        try:
            text = extract_text(doc.storage_path)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to load document %s", document_id)
            return {"error": str(exc), "filename": doc.filename}
        if not text.strip():
            return {"error": "no extractable text", "filename": doc.filename}
        return {"raw_text": text, "filename": doc.filename, "error": ""}


def route_document(state: IndexingState) -> dict[str, Any]:
    if state.get("error"):
        return {}
    user_id, document_id = _ids(state)
    with session_scope() as db:
        doc = db.exec(
            select(Document).where(Document.id == document_id, Document.user_id == user_id)
        ).one()
        hinted = doc.doc_type.value if doc.doc_type else None
    if hinted in {"resume", "job"}:
        tools.invoke(
            "update_processing_status",
            user_id=user_id,
            document_id=document_id,
            status=DocumentStatus.processing,
            doc_type=hinted,
        )
        return {"doc_type": hinted}

    llm = get_chat_model(role="router")
    structured = llm.with_structured_output(DocumentClassification)
    snippet = (state.get("raw_text") or "")[:4000]
    result: DocumentClassification = structured.invoke(
        [
            (
                "system",
                "Classify the document as either a resume/CV or a job description. "
                "Use the filename as a hint when the body is ambiguous.",
            ),
            (
                "human",
                f"Filename: {state.get('filename')}\n\nDocument:\n{snippet}",
            ),
        ]
    )
    tools.invoke(
        "update_processing_status",
        user_id=user_id,
        document_id=document_id,
        status=DocumentStatus.processing,
        doc_type=result.doc_type,
    )
    return {"doc_type": result.doc_type}


def process_resume(state: IndexingState) -> dict[str, Any]:
    if state.get("error"):
        return {}
    user_id, document_id = _ids(state)
    llm = get_chat_model(role="extraction")
    structured = llm.with_structured_output(ResumeProfile)
    profile: ResumeProfile = structured.invoke(
        [
            (
                "system",
                "Extract a structured resume profile. Use only facts present in the document. "
                "Leave fields empty rather than inventing them.",
            ),
            ("human", state.get("raw_text") or ""),
        ]
    )
    tools.invoke(
        "save_resume_profile",
        user_id=user_id,
        document_id=document_id,
        profile=profile,
    )
    return {"profile": profile.model_dump()}


def process_job(state: IndexingState) -> dict[str, Any]:
    if state.get("error"):
        return {}
    user_id, document_id = _ids(state)
    llm = get_chat_model(role="extraction")
    structured = llm.with_structured_output(JobProfile)
    profile: JobProfile = structured.invoke(
        [
            (
                "system",
                "Extract a structured job description profile. Use only facts present in the document.",
            ),
            ("human", state.get("raw_text") or ""),
        ]
    )
    tools.invoke(
        "save_job_profile",
        user_id=user_id,
        document_id=document_id,
        profile=profile,
    )
    tools.invoke("enrich_job_board", user_id=user_id, document_id=document_id)
    return {"profile": profile.model_dump()}


def chunk_and_embed(state: IndexingState) -> dict[str, Any]:
    if state.get("error"):
        return {"chunks": []}
    texts = SPLITTER.split_text(state.get("raw_text") or "")
    if not texts:
        return {"error": "no chunks produced", "chunks": []}
    embeddings = get_embeddings().embed_documents(texts)
    user_id, document_id = _ids(state)
    chunks = []
    for i, (content, vector) in enumerate(zip(texts, embeddings, strict=True)):
        chunks.append(
            {
                "content": content,
                "embedding": vector,
                "ordinal": i,
                "metadata": {
                    "user_id": str(user_id),
                    "document_id": str(document_id),
                    "doc_type": state.get("doc_type"),
                    "filename": state.get("filename"),
                },
            }
        )
    return {"chunks": chunks}


def persist_data(state: IndexingState) -> dict[str, Any]:
    user_id, document_id = _ids(state)
    if state.get("error"):
        tools.invoke(
            "update_processing_status",
            user_id=user_id,
            document_id=document_id,
            status=DocumentStatus.failed,
            error_message=state["error"],
        )
        return {}
    tools.invoke(
        "replace_document_chunks",
        user_id=user_id,
        document_id=document_id,
        chunks=state.get("chunks") or [],
    )
    tools.invoke(
        "update_processing_status",
        user_id=user_id,
        document_id=document_id,
        status=DocumentStatus.processed,
        error_message=None,
        doc_type=state.get("doc_type"),
    )
    return {}
