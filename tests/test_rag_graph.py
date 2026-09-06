from __future__ import annotations

import uuid
from pathlib import Path

from agent.indexing.graph import indexing_graph
from agent.rag.graph import rag_graph
from agent.schemas import FaithfulnessResult, GeneratedAnswer, InterviewTopicCandidate, InterviewTopicPlan, QueryPlan, ResumeProfile
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
    assert result.get("validated") is True
    assert result.get("message_id")
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


@requires_postgres
def test_identify_channel_blocks_interview_without_topic(db_user):
    result = rag_graph.invoke(
        {
            "user_id": str(db_user),
            "question": "Explain list vs tuple",
            "channel": "interview",
        }
    )
    assert result.get("blocked") is True
    assert "topic_id" in (result.get("error") or "")


@requires_postgres
def test_extract_interview_topics_persists_topics(monkeypatch, db_user):
    from agent.rag import nodes as rag_nodes

    def chat_for_schema(**kwargs):
        class Router:
            def with_structured_output(self, schema, **_kwargs):
                if schema is InterviewTopicPlan:
                    return _FakeChat(
                        InterviewTopicPlan(
                            topics=[
                                InterviewTopicCandidate(label="Python"),
                                InterviewTopicCandidate(label="FastAPI"),
                                InterviewTopicCandidate(label="SQL"),
                            ]
                        )
                    ).with_structured_output(schema)
                raise AssertionError(schema)

        return Router()

    monkeypatch.setattr(rag_nodes, "get_chat_model", chat_for_schema)
    result = rag_graph.invoke(
        {
            "user_id": str(db_user),
            "question": "You are strong in Python and FastAPI; add SQL practice.",
            "channel": "extract_topics",
            "resume_id": None,
            "job_ids": [],
        }
    )
    assert result.get("blocked") is False
    topics = result.get("topics") or []
    assert [item["label"] for item in topics] == ["Python", "FastAPI", "SQL"]
    assert all(item.get("conversation_id") for item in topics)

    from backend.models import Conversation, ConversationKind, Topic

    with session_scope() as db:
        rows = db.exec(select(Topic).where(Topic.user_id == db_user)).all()
        assert sorted(row.label for row in rows) == ["FastAPI", "Python", "SQL"]
        interviews = db.exec(
            select(Conversation).where(Conversation.user_id == db_user, Conversation.kind == ConversationKind.interview)
        ).all()
        assert len(interviews) == 3


@requires_postgres
def test_extract_interview_topics_reuses_existing_for_source_message(monkeypatch, db_user):
    from agent.rag import nodes as rag_nodes
    from backend.models import Conversation, ConversationKind, Message, MessageRole, Topic

    with session_scope() as db:
        convo = Conversation(user_id=db_user)
        db.add(convo)
        db.flush()
        message = Message(
            conversation_id=convo.id,
            user_id=db_user,
            role=MessageRole.assistant,
            content="Python and FastAPI are strengths; add SQL.",
            extra={"validated": True},
        )
        db.add(message)
        db.flush()
        source_message_id = str(message.id)
        source_conversation_id = str(convo.id)

    def chat_for_schema(**kwargs):
        class Router:
            def with_structured_output(self, schema, **_kwargs):
                if schema is InterviewTopicPlan:
                    return _FakeChat(
                        InterviewTopicPlan(
                            topics=[
                                InterviewTopicCandidate(label="Python"),
                                InterviewTopicCandidate(label="FastAPI"),
                            ]
                        )
                    ).with_structured_output(schema)
                raise AssertionError(schema)

        return Router()

    monkeypatch.setattr(rag_nodes, "get_chat_model", chat_for_schema)
    payload = {
        "user_id": str(db_user),
        "question": "Python and FastAPI are strengths; add SQL.",
        "channel": "extract_topics",
        "resume_id": None,
        "job_ids": [],
        "source_conversation_id": source_conversation_id,
        "source_message_id": source_message_id,
    }
    first = rag_graph.invoke(payload)
    assert first.get("topics_existing") is False
    assert {item["label"] for item in first.get("topics") or []} == {"Python", "FastAPI"}

    monkeypatch.setattr(
        rag_nodes,
        "get_chat_model",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("should not extract topics again")),
    )
    second = rag_graph.invoke(payload)
    assert second.get("topics_existing") is True
    assert {item["label"] for item in second.get("topics") or []} == {"Python", "FastAPI"}

    with session_scope() as db:
        rows = db.exec(select(Topic).where(Topic.user_id == db_user, Topic.source_message_id == uuid.UUID(source_message_id))).all()
        assert len(rows) == 2
        interviews = db.exec(
            select(Conversation).where(Conversation.user_id == db_user, Conversation.kind == ConversationKind.interview)
        ).all()
        assert len(interviews) == 2
        source = db.get(Message, uuid.UUID(source_message_id))
        assert source is not None
        stamped = (source.extra or {}).get("topics") or []
        assert {item["label"] for item in stamped} == {"Python", "FastAPI"}


@requires_postgres
def test_interview_channel_skips_faithfulness(monkeypatch, db_user):
    from agent.rag import nodes as rag_nodes
    from mcp.registry import tools

    created = tools.invoke(
        "save_interview_topics",
        user_id=db_user,
        labels=["Python"],
        context={"answer": "Python is a strength", "job_ids": []},
    )
    topic_id = created[0]["id"]

    def chat_for_schema(**kwargs):
        class Router:
            def with_structured_output(self, schema, **_kwargs):
                if schema is QueryPlan:
                    return _FakeChat(
                        QueryPlan(intent="general", rewritten_query="python list vs tuple")
                    ).with_structured_output(schema)
                if schema is GeneratedAnswer:
                    return _FakeChat(
                        GeneratedAnswer(text="Lists are mutable; tuples are not.", citations=[], strengths=[], gaps=[])
                    ).with_structured_output(schema)
                if schema is FaithfulnessResult:
                    raise AssertionError("interview path should skip faithfulness")
                raise AssertionError(schema)

        return Router()

    monkeypatch.setattr(rag_nodes, "get_chat_model", chat_for_schema)
    monkeypatch.setattr(rag_nodes, "get_embeddings", lambda: _FakeEmbeddings())
    result = rag_graph.invoke(
        {
            "user_id": str(db_user),
            "question": "Explain list vs tuple",
            "channel": "interview",
            "topic_id": topic_id,
            "system_prompt": "You are a practice coach for Python at medium difficulty.",
        }
    )
    assert result.get("blocked") is not True
    assert "mutable" in (result.get("answer") or result.get("draft") or {}).get("text", "")
    assert result.get("conversation_id")

