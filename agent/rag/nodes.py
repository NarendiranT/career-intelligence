from __future__ import annotations

import logging
import re
import uuid
from typing import Any, TypedDict

from sqlmodel import select

from agent.llm import get_chat_model, get_embeddings
from agent.schemas import FaithfulnessResult, GeneratedAnswer, QueryPlan, RetrievedChunk
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
    return {"blocked": False, "error": "", "retries": 0, "k": 8, "broaden": False}


def query_understanding(state: RagState) -> dict[str, Any]:
    llm = get_chat_model()
    structured = llm.with_structured_output(QueryPlan)
    plan: QueryPlan = structured.invoke(
        [
            (
                "system",
                "Classify the user intent as resume, job, comparison, or general. "
                "Rewrite the query for vector retrieval. Do not invent document IDs.",
            ),
            ("human", state["question"]),
        ]
    )
    return {"intent": plan.intent, "rewritten_query": plan.rewritten_query}


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
    llm = get_chat_model(temperature=0.2)
    structured = llm.with_structured_output(GeneratedAnswer)
    chunk_block = "\n\n".join(
        f"[{item['filename']}]\n{item['content']}" for item in (state.get("chunks") or [])
    )
    answer: GeneratedAnswer = structured.invoke(
        [
            ("system", SYSTEM_PROMPT),
            (
                "human",
                (
                    f"Intent: {state.get('intent')}\n"
                    f"Question: {state['question']}\n\n"
                    f"Structured profiles JSON:\n{state.get('profiles')}\n\n"
                    f"Retrieved chunks:\n{chunk_block or '(none)'}"
                ),
            ),
        ]
    )
    if not answer.citations:
        from agent.schemas import Citation

        seen: dict[str, str] = {}
        for item in state.get("chunks") or []:
            seen[item["document_id"]] = item["filename"]
        answer.citations = [Citation(id=did, label=name) for did, name in seen.items()]
    return {"draft": answer.model_dump()}


def validate_answer(state: RagState) -> dict[str, Any]:
    llm = get_chat_model()
    structured = llm.with_structured_output(FaithfulnessResult)
    result: FaithfulnessResult = structured.invoke(
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
        ]
    )
    retries = int(state.get("retries") or 0)
    if result.grounded or not (state.get("chunks") or state.get("profiles")):
        return {"ok": True, "answer": state.get("draft")}
    if retries >= 2:
        return {"ok": True, "answer": state.get("draft")}
    return {"ok": False}


def retry_retrieval(state: RagState) -> dict[str, Any]:
    retries = int(state.get("retries") or 0) + 1
    k = int(state.get("k") or 8) + 8
    return {"retries": retries, "k": k, "broaden": retries >= 2}


def stream_and_persist(state: RagState) -> dict[str, Any]:
    if state.get("blocked"):
        return {"answer": {"text": state.get("error") or "blocked", "citations": [], "strengths": [], "gaps": []}}
    user_id = _user(state)
    conversation_id = uuid.UUID(state["conversation_id"]) if state.get("conversation_id") else None
    answer = state.get("answer") or state.get("draft") or {"text": "", "citations": [], "strengths": [], "gaps": []}
    saved_user = tools.invoke(
        "save_conversation_message",
        user_id=user_id,
        conversation_id=conversation_id,
        role="user",
        content=state["question"],
    )
    convo_id = uuid.UUID(saved_user["conversation_id"])
    tools.invoke(
        "save_conversation_message",
        user_id=user_id,
        conversation_id=convo_id,
        role="assistant",
        content=answer.get("text") or "",
        citations=answer.get("citations"),
        extra={"strengths": answer.get("strengths"), "gaps": answer.get("gaps")},
    )
    tools.invoke(
        "update_usage",
        user_id=user_id,
        conversation_id=convo_id,
        event_type="chat",
        model=settings.chat_model,
    )
    tools.invoke("web_search", query=state["question"], enabled=False)
    return {"conversation_id": str(convo_id), "answer": answer}
