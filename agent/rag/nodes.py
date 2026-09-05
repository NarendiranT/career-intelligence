from __future__ import annotations

import logging
import re
import uuid
from typing import Any, TypedDict

from sqlmodel import select

from agent.llm import get_chat_model, get_embeddings, invoke_structured_tracked
from agent.schemas import FaithfulnessResult, GeneratedAnswer, QueryPlan, RetrievedChunk
from agent.usage import append_usage, persist_usage_events, summarize_usage
from backend.config import settings
from backend.db import session_scope
from backend.models import Chunk, Document
from mcp.registry import tools

logger = logging.getLogger(__name__)

INJECTION_PATTERNS = (
    re.compile(r"ignore (all )?(previous|prior|above) instructions", re.I),
    re.compile(r"system prompt", re.I),
    re.compile(r"you are now", re.I),
    re.compile(r"override (your|the) (rules|guardrails)", re.I),
)

SYSTEM_PROMPT = (
    "You are a career intelligence assistant. Answer only from the provided resume, "
    "job profiles, and retrieved document chunks. Cite document filenames. "
    "Do not invent employers, skills, or requirements that are not in the context. "
    "When comparing a resume to a job, populate strengths and gaps."
)


class RagState(TypedDict, total=False):
    user_id: str
    question: str
    resume_id: str | None
    job_ids: list[str]
    conversation_id: str | None
    rewritten_query: str
    intent: str
    chunks: list[dict[str, Any]]
    profiles: dict[str, Any]
    draft: dict[str, Any]
    retries: int
    k: int
    broaden: bool
    ok: bool
    error: str
    blocked: bool
    answer: dict[str, Any]
    temperature: float
    top_p: float
    max_tokens: int
    system_prompt: str
    web_search: bool
    model: str
    usage_events: list[dict[str, Any]]
    usage: dict[str, int]


def _user(state: RagState) -> uuid.UUID:
    return uuid.UUID(state["user_id"])


def _selected_ids(state: RagState) -> list[uuid.UUID]:
    ids: list[uuid.UUID] = []
    if state.get("resume_id"):
        ids.append(uuid.UUID(state["resume_id"]))
    for job_id in state.get("job_ids") or []:
        ids.append(uuid.UUID(job_id))
    return ids


def input_guardrail(state: RagState) -> dict[str, Any]:
    question = (state.get("question") or "").strip()
    if not question:
        return {"blocked": True, "error": "question is required", "ok": False}
    if len(question) > settings.max_question_chars:
        return {"blocked": True, "error": "question is too long", "ok": False}
    for pattern in INJECTION_PATTERNS:
        if pattern.search(question):
            return {"blocked": True, "error": "query rejected by safety guardrail", "ok": False}

    user_id = _user(state)
    selected = _selected_ids(state)
    if selected:
        owned = tools.invoke("fetch_document_metadata", user_id=user_id, document_ids=selected)
        owned_ids = {item["id"] for item in owned}
        missing = [str(i) for i in selected if str(i) not in owned_ids]
        if missing:
            return {"blocked": True, "error": f"unknown document ids: {', '.join(missing)}", "ok": False}
        not_ready = [item["id"] for item in owned if item.get("status") != "processed"]
        if not_ready:
            return {
                "blocked": True,
                "error": "selected documents are still processing; wait until they are processed",
                "ok": False,
            }
    return {"blocked": False, "error": "", "retries": 0, "k": 8, "broaden": False}


def query_understanding(state: RagState) -> dict[str, Any]:
    llm = get_chat_model(role="router")
    plan, usage = invoke_structured_tracked(
        llm,
        QueryPlan,
        [
            (
                "system",
                "Classify the user intent as resume, job, comparison, or general. "
                "Rewrite the query for vector retrieval. Do not invent document IDs.",
            ),
            ("human", state["question"]),
        ],
        event_type="rag.query_understanding",
    )
    return {
        "intent": plan.intent,
        "rewritten_query": plan.rewritten_query,
        "usage_events": append_usage(state, usage),
    }


def retrieve_context(state: RagState) -> dict[str, Any]:
    user_id = _user(state)
    query = state.get("rewritten_query") or state["question"]
    vector = get_embeddings().embed_query(query)
    k = int(state.get("k") or 8)
    selected = _selected_ids(state)
    with session_scope() as db:
        distance = Chunk.embedding.cosine_distance(vector)
        stmt = (
            select(Chunk, Document.filename, distance.label("dist"))
            .join(Document, Document.id == Chunk.document_id)
            .where(Chunk.user_id == user_id)
            .order_by(distance)
            .limit(k)
        )
        if selected and not state.get("broaden"):
            stmt = stmt.where(Chunk.document_id.in_(selected))
        rows = db.exec(stmt).all()
        retrieved: list[RetrievedChunk] = []
        for chunk, filename, dist in rows:
            retrieved.append(
                RetrievedChunk(
                    document_id=str(chunk.document_id),
                    filename=filename,
                    content=chunk.content,
                    distance=float(dist),
                )
            )
    profile_ids = selected or [uuid.UUID(c.document_id) for c in retrieved]
    profiles = {"resumes": [], "jobs": []}
    if profile_ids:
        profiles = tools.invoke("fetch_structured_profiles", user_id=user_id, document_ids=profile_ids)
    return {
        "chunks": [c.model_dump() for c in retrieved],
        "profiles": profiles,
    }


def build_prompt(state: RagState) -> dict[str, Any]:
    # Prompt is assembled at generate time from state; keep node for graph fidelity.
    return {}


def generate_answer(state: RagState) -> dict[str, Any]:
    temperature = float(state.get("temperature") if state.get("temperature") is not None else 0.2)
    max_tokens = int(state["max_tokens"]) if state.get("max_tokens") else None
    top_p = float(state["top_p"]) if state.get("top_p") is not None else None
    llm = get_chat_model(
        role="generation",
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=top_p,
    )
    chunk_block = "\n\n".join(
        f"[{item['filename']}]\n{item['content']}" for item in (state.get("chunks") or [])
    )
    system = (state.get("system_prompt") or "").strip() or SYSTEM_PROMPT
    if system != SYSTEM_PROMPT:
        system = f"{system}\n\n{SYSTEM_PROMPT}"
    answer, usage = invoke_structured_tracked(
        llm,
        GeneratedAnswer,
        [
            ("system", system),
            (
                "human",
                (
                    f"Intent: {state.get('intent')}\n"
                    f"Question: {state['question']}\n\n"
                    f"Structured profiles JSON:\n{state.get('profiles')}\n\n"
                    f"Retrieved chunks:\n{chunk_block or '(none)'}"
                ),
            ),
        ],
        event_type="rag.generate",
    )
    if not answer.citations:
        from agent.schemas import Citation

        seen: dict[str, str] = {}
        for item in state.get("chunks") or []:
            seen[item["document_id"]] = item["filename"]
        answer.citations = [Citation(id=did, label=name) for did, name in seen.items()]
    return {"draft": answer.model_dump(), "usage_events": append_usage(state, usage)}


def validate_answer(state: RagState) -> dict[str, Any]:
    llm = get_chat_model(role="router")
    result, usage = invoke_structured_tracked(
        llm,
        FaithfulnessResult,
        [
            (
                "system",
                "Decide if the draft answer is grounded in the provided profiles and chunks. "
                "Ungrounded means it asserts facts not present in the context.",
            ),
            (
                "human",
                f"Draft: {state.get('draft')}\n\nContext chunks: {state.get('chunks')}\nProfiles: {state.get('profiles')}",
            ),
        ],
        event_type="rag.faithfulness",
    )
    retries = int(state.get("retries") or 0)
    usage_events = append_usage(state, usage)
    if result.grounded or not (state.get("chunks") or state.get("profiles")):
        return {"ok": True, "answer": state.get("draft"), "usage_events": usage_events}
    if retries >= 2:
        return {"ok": True, "answer": state.get("draft"), "usage_events": usage_events}
    return {"ok": False, "usage_events": usage_events}


def retry_retrieval(state: RagState) -> dict[str, Any]:
    retries = int(state.get("retries") or 0) + 1
    k = int(state.get("k") or 8) + 8
    return {"retries": retries, "k": k, "broaden": retries >= 2}


def stream_and_persist(state: RagState) -> dict[str, Any]:
    if state.get("blocked"):
        return {
            "answer": {"text": state.get("error") or "blocked", "citations": [], "strengths": [], "gaps": []},
            "usage": summarize_usage(state.get("usage_events")),
        }
    user_id = _user(state)
    conversation_id = uuid.UUID(state["conversation_id"]) if state.get("conversation_id") else None
    answer = state.get("answer") or state.get("draft") or {"text": "", "citations": [], "strengths": [], "gaps": []}
    saved_user = tools.invoke(
        "save_conversation_message",
        user_id=user_id,
        conversation_id=conversation_id,
        role="user",
        content=state["question"],
        extra={
            "resume_id": state.get("resume_id"),
            "job_ids": list(state.get("job_ids") or []),
        },
    )
    convo_id = uuid.UUID(saved_user["conversation_id"])
    usage = summarize_usage(state.get("usage_events"))
    tools.invoke(
        "save_conversation_message",
        user_id=user_id,
        conversation_id=convo_id,
        role="assistant",
        content=answer.get("text") or "",
        citations=answer.get("citations"),
        extra={"strengths": answer.get("strengths"), "gaps": answer.get("gaps"), "usage": usage},
    )
    persist_usage_events(
        user_id=user_id,
        conversation_id=convo_id,
        events=state.get("usage_events") or [],
        extra={"web_search": bool(state.get("web_search")), "ui_model": state.get("model")},
    )
    tools.invoke("web_search", query=state["question"], enabled=bool(state.get("web_search")))
    return {
        "conversation_id": str(convo_id),
        "answer": answer,
        "usage": usage,
    }
