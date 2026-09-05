from __future__ import annotations

import uuid
from pathlib import Path

from agent.indexing.graph import indexing_graph
from agent.rag.graph import rag_graph
from agent.schemas import FaithfulnessResult, GeneratedAnswer, QueryPlan, ResumeProfile
from backend.db import session_scope
from backend.models import Document, DocumentStatus, DocType, UsageEvent
from sqlmodel import select
from tests.conftest import requires_postgres
from tests.test_indexing_graph import _FakeChat, _FakeEmbeddings


@requires_postgres
def test_rag_graph_grounded_answer(monkeypatch, sample_resume: Path, db_user, tmp_path: Path):
    from agent.indexing import nodes as indexing_nodes
    from agent.rag import nodes as rag_nodes

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
        lambda **kwargs: _FakeChat(ResumeProfile(name="Jane Candidate", skills=["Python"])),
    )
    monkeypatch.setattr(indexing_nodes, "get_embeddings", lambda: _FakeEmbeddings())
    indexing_graph.invoke({"user_id": str(db_user), "document_id": str(document_id)})

    def chat_for_schema(**kwargs):
        class Router:
            def with_structured_output(self, schema, **_kwargs):
                if schema is QueryPlan:
                    return _FakeChat(
                        QueryPlan(intent="resume", rewritten_query="Jane Candidate skills Python")
                    ).with_structured_output(schema)
                if schema is GeneratedAnswer:
                    return _FakeChat(
                        GeneratedAnswer(
                            text="Jane lists Python and FastAPI.",
                            citations=[{"id": str(document_id), "label": "resume.txt"}],
                            strengths=["Python"],
                            gaps=[],
                        )
                    ).with_structured_output(schema)
                if schema is FaithfulnessResult:
                    return _FakeChat(
                        FaithfulnessResult(grounded=True, reason="cited chunks")
                    ).with_structured_output(schema)
                raise AssertionError(schema)

        return Router()

    monkeypatch.setattr(rag_nodes, "get_chat_model", chat_for_schema)
    monkeypatch.setattr(rag_nodes, "get_embeddings", lambda: _FakeEmbeddings())

    result = rag_graph.invoke(
        {
            "user_id": str(db_user),
            "question": "What skills are on my resume?",
            "resume_id": str(document_id),
            "job_ids": [],
        }
    )
    assert result.get("ok") is True
    assert "Python" in (result.get("answer") or {}).get("text", "")
    assert result.get("conversation_id")
    assert result.get("usage") == {"tokens": 0, "prompt_tokens": 0, "completion_tokens": 0}

    with session_scope() as db:
        types = sorted(
            event.event_type
            for event in db.exec(select(UsageEvent).where(UsageEvent.user_id == db_user)).all()
            if event.event_type.startswith("rag.")
        )
    assert types == ["rag.faithfulness", "rag.generate", "rag.query_understanding"]
