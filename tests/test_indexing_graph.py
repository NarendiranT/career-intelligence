from __future__ import annotations

import uuid
from pathlib import Path

from agent.indexing.graph import indexing_graph
from agent.schemas import ResumeProfile
from backend.config import settings
from backend.models import Document, DocumentStatus, DocType, UsageEvent
from backend.db import session_scope
from mcp.registry import tools
from sqlmodel import select
from tests.conftest import requires_postgres


class _Structured:
    def __init__(self, payload):
        self.payload = payload

    def invoke(self, _messages):
        return self.payload


class _FakeChat:
    def __init__(self, payload):
        self.payload = payload

    def with_structured_output(self, _schema, **_kwargs):
        return _Structured(self.payload)


class _FakeEmbeddings:
    def embed_documents(self, texts):
        return [[0.01] * settings.embedding_dim for _ in texts]

    def embed_query(self, _text):
        return [0.01] * settings.embedding_dim


@requires_postgres
def test_indexing_graph_txt_resume(monkeypatch, sample_resume: Path, db_user, tmp_path: Path):
    from agent.indexing import nodes as indexing_nodes

    dest = tmp_path / "resume.txt"
    dest.write_text(sample_resume.read_text(encoding="utf-8"), encoding="utf-8")
    document_id = uuid.uuid4()
    with session_scope() as db:
        db.add(
            Document(
                id=document_id,
                user_id=db_user,
                doc_type=DocType.resume,
                filename="resume.txt",
                storage_path=str(dest),
                status=DocumentStatus.uploaded,
                mime="text/plain",
                size=dest.stat().st_size,
            )
        )

    monkeypatch.setattr(
        indexing_nodes,
        "get_chat_model",
        lambda **kwargs: _FakeChat(ResumeProfile(name="Jane Candidate", skills=["Python", "FastAPI"])),
    )
    monkeypatch.setattr(indexing_nodes, "get_embeddings", lambda: _FakeEmbeddings())

    result = indexing_graph.invoke({"user_id": str(db_user), "document_id": str(document_id)})
    assert not result.get("error")
    meta = tools.invoke("fetch_document_metadata", user_id=db_user, document_ids=[document_id])
    assert meta[0]["status"] == "processed"

    with session_scope() as db:
        events = db.exec(select(UsageEvent).where(UsageEvent.user_id == db_user)).all()
        types = [event.event_type for event in events]
        document_ids = [event.extra.get("document_id") if event.extra else None for event in events]
    assert types == ["indexing.extract_resume"]
    assert document_ids == [str(document_id)]
