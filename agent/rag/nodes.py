from __future__ import annotations

import logging
import re
import uuid
from typing import Any, TypedDict

from sqlmodel import select

from agent.context_budget import (
    TOPIC_ANSWER_CHARS,
    compact_chunks,
    compact_draft,
    compact_profiles,
    compact_topic_context,
    truncate_text,
)
from agent.llm import get_chat_model, get_embeddings, invoke_structured_tracked
from agent.schemas import FaithfulnessResult, GeneratedAnswer, InterviewTopicPlan, QueryPlan, RetrievedChunk
from agent.usage import append_usage, persist_usage_events, question_usage_details, summarize_usage
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
    "job profiles, and retrieved document chunks. Put sources in the citations list "
    "using each document's id and filename. Do not put filenames, brackets, or "
    "citation markers such as 【file.pdf】 in the answer text, strengths, or gaps. "
    "Do not invent employers, skills, or requirements that are not in the context. "
    "When comparing a resume to a job, populate strengths and gaps."
)

INTERVIEW_GROUNDING = (
    "Stay on the selected interview topic. Use the candidate resume and job context when it is present. "
    "Keep `text` as prose. Put comparison grids in `table` and snippets in `code` — never markdown tables "
    "or fenced code inside `text`. Do not invent employers or skills that are not in the context, "
    "but you may teach general interview concepts for this topic."
)

CHANNELS = frozenset({"assistant", "interview", "extract_topics"})


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
    model: str
    channel: str
    topic_id: str | None
    topic_label: str
    topic_context: dict[str, Any]
    source_conversation_id: str | None
    source_message_id: str | None
    topics: list[dict[str, Any]]
    usage_events: list[dict[str, Any]]
    usage: dict[str, int]
    document_names: dict[str, str]
    grounded: bool
    validated: bool
    message_id: str | None
    topics_existing: bool


def _user(state: RagState) -> uuid.UUID:
    return uuid.UUID(state["user_id"])


def _selected_ids(state: RagState) -> list[uuid.UUID]:
    ids: list[uuid.UUID] = []
    if state.get("resume_id"):
        ids.append(uuid.UUID(state["resume_id"]))
    for job_id in state.get("job_ids") or []:
        ids.append(uuid.UUID(job_id))
    return ids


def identify_channel(state: RagState) -> dict[str, Any]:
    raw = str(state.get("channel") or "assistant").strip().lower()
    channel = raw if raw in CHANNELS else "assistant"
    if channel == "extract_topics":
        if not (state.get("question") or "").strip():
            return {
                "channel": channel,
                "blocked": True,
                "error": "answer text is required to create interview topics",
                "ok": False,
            }
        return {"channel": channel, "blocked": False, "error": ""}
    if channel == "interview":
        topic_id = state.get("topic_id")
        if not topic_id:
            return {"channel": channel, "blocked": True, "error": "topic_id is required", "ok": False}
        topic = tools.invoke("get_interview_topic", user_id=_user(state), topic_id=uuid.UUID(str(topic_id)))
        if not topic:
            return {"channel": channel, "blocked": True, "error": "topic not found", "ok": False}
        context = topic.get("context") if isinstance(topic.get("context"), dict) else {}
        resume_id = topic.get("resume_id") or context.get("resume_id") or state.get("resume_id")
        raw_jobs = topic.get("job_ids") or context.get("job_ids") or state.get("job_ids") or []
        conversation_id = topic.get("conversation_id") or state.get("conversation_id")
        return {
            "channel": channel,
            "blocked": False,
            "error": "",
            "topic_label": topic.get("label") or "",
            "topic_context": context,
            "resume_id": str(resume_id) if resume_id else None,
            "job_ids": [str(item) for item in raw_jobs if item],
            "conversation_id": str(conversation_id) if conversation_id else None,
        }
    return {"channel": "assistant", "blocked": False, "error": ""}


def _source_uuid(value: object) -> uuid.UUID | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        return uuid.UUID(raw)
    except ValueError:
        return None


def extract_interview_topics(state: RagState) -> dict[str, Any]:
    source_conversation_id = state.get("source_conversation_id")
    source_message_id = _source_uuid(state.get("source_message_id"))
    existing = tools.invoke(
        "list_interview_topics_for_source",
        user_id=_user(state),
        source_message_id=source_message_id,
    )
    if existing:
        names = [item.get("label") or "" for item in existing if isinstance(item, dict)]
        text = "Interview topics already created: " + ", ".join(name for name in names if name)
        return {
            "topics": existing,
            "topics_existing": True,
            "usage": summarize_usage(state.get("usage_events")),
            "answer": {"text": text, "citations": [], "strengths": [], "gaps": []},
            "conversation_id": source_conversation_id,
            "channel": "extract_topics",
            "ok": True,
            "blocked": False,
            "error": "",
        }

    llm = get_chat_model(role="router")
    plan, usage = invoke_structured_tracked(
        llm,
        InterviewTopicPlan,
        [
            (
                "system",
                "Extract 3 to 8 interview practice topics from the career assistant answer. "
                "Each topic should be a short skill or subject label a candidate can drill on. "
                "Prefer concrete skills, gaps, and technologies over vague themes.",
            ),
            (
                "human",
                (
                    f"Answer:\n{truncate_text(state['question'], TOPIC_ANSWER_CHARS)}\n\n"
                    f"Source conversation: {state.get('source_conversation_id') or '(none)'}"
                ),
            ),
        ],
        event_type="rag.extract_topics",
    )
    usage_events = append_usage(state, usage)
    labels = [item.label.strip() for item in plan.topics if item.label and item.label.strip()][:8]
    if not labels:
        return {
            "blocked": True,
            "error": "could not extract interview topics",
            "ok": False,
            "usage_events": usage_events,
        }
    topics = tools.invoke(
        "save_interview_topics",
        user_id=_user(state),
        labels=labels,
        source_conversation_id=uuid.UUID(str(source_conversation_id)) if source_conversation_id else None,
        source_message_id=source_message_id,
        context={
            "answer": state.get("question") or "",
            "resume_id": state.get("resume_id"),
            "job_ids": list(state.get("job_ids") or []),
        },
    )
    persist_usage_events(
        user_id=_user(state),
        conversation_id=uuid.UUID(str(source_conversation_id)) if source_conversation_id else None,
        events=usage_events,
        extra={
            "channel": "extract_topics",
            "feature": "interview",
            "details": question_usage_details(None, extract_topics=True),
        },
    )
    names = [item.get("label") or "" for item in topics if isinstance(item, dict)]
    text = "Created interview topics: " + ", ".join(name for name in names if name)
    return {
        "topics": topics,
        "topics_existing": False,
        "usage_events": usage_events,
        "usage": summarize_usage(usage_events),
        "answer": {"text": text, "citations": [], "strengths": [], "gaps": []},
        "conversation_id": source_conversation_id,
        "channel": "extract_topics",
        "ok": True,
        "blocked": False,
        "error": "",
    }


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
        return {
            "blocked": False,
            "error": "",
            "retries": 0,
            "k": 8,
            "broaden": False,
            "document_names": {item["id"]: item["filename"] for item in owned if item.get("filename")},
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
    chunk_block = compact_chunks(state.get("chunks"))
    system = (state.get("system_prompt") or "").strip() or SYSTEM_PROMPT
    channel = state.get("channel") or "assistant"
    if channel == "interview":
        base = (state.get("system_prompt") or "").strip() or (
            f"You are a practice coach for {state.get('topic_label') or 'this topic'}."
        )
        system = f"{base}\n\n{INTERVIEW_GROUNDING}"
    elif system != SYSTEM_PROMPT:
        system = f"{system}\n\n{SYSTEM_PROMPT}"
    topic_block = ""
    if channel == "interview":
        topic_block = (
            f"Interview topic: {state.get('topic_label') or ''}\n"
            f"{compact_topic_context(state.get('topic_context'))}\n\n"
        )
    answer, usage = invoke_structured_tracked(
        llm,
        GeneratedAnswer,
        [
            ("system", system),
            (
                "human",
                (
                    f"{topic_block}"
                    f"Intent: {state.get('intent')}\n"
                    f"Question: {state['question']}\n\n"
                    f"Structured profiles:\n{compact_profiles(state.get('profiles'))}\n\n"
                    f"Retrieved chunks:\n{chunk_block}"
                ),
            ),
        ],
        event_type="rag.generate",
    )
    _apply_filename_citations(answer, state)
    return {"draft": answer.model_dump(), "usage_events": append_usage(state, usage)}


_RESUME_ALIASES = frozenset({"resume", "resume profile", "cv"})
_JOB_ALIASES = frozenset({"job", "jd", "job profile", "job description"})
_CORNER_CITE_RE = re.compile(r"【([^】]*)】")
_SQUARE_CITE_RE = re.compile(r"\[([^\[\]]+)\]")
_FILE_SUFFIX_RE = re.compile(r"\.(pdf|docx?|txt)$", re.I)


def _basename(value: str) -> str:
    return value.replace("\\", "/").split("/")[-1].strip()


def _normalize_doc_id(value: str) -> str:
    raw = (value or "").strip()
    if not raw:
        return ""
    try:
        return str(uuid.UUID(raw))
    except ValueError:
        return raw


def _document_names(state: RagState) -> dict[str, str]:
    names = dict(state.get("document_names") or {})
    for item in state.get("chunks") or []:
        document_id = item.get("document_id")
        filename = item.get("filename")
        if document_id and filename:
            names[str(document_id)] = str(filename)
    profiles = state.get("profiles") or {}
    for group in ("resumes", "jobs"):
        for profile in profiles.get(group) or []:
            document_id = profile.get("document_id")
            filename = profile.get("filename")
            if document_id and filename:
                names[str(document_id)] = str(filename)
    return {_normalize_doc_id(did) or did: name for did, name in names.items()}


def _filename_index(names: dict[str, str]) -> dict[str, str]:
    index: dict[str, str] = {}
    for did, filename in names.items():
        index[_basename(filename).lower()] = did
        index[filename.strip().lower()] = did
    return index


def _looks_like_source_ref(inner: str, filenames: set[str]) -> bool:
    value = inner.strip()
    if not value:
        return False
    lower = _basename(value).lower()
    if lower in _RESUME_ALIASES or lower in _JOB_ALIASES:
        return True
    if _FILE_SUFFIX_RE.search(lower):
        return True
    return lower in filenames or value.strip().lower() in filenames


def _strip_inline_citations(text: str, names: dict[str, str] | None = None) -> tuple[str, list[str]]:
    if not text:
        return "", []
    filenames = {_basename(name).lower() for name in (names or {}).values()}
    found: list[str] = []

    def keep_corner(match: re.Match[str]) -> str:
        inner = match.group(1).strip()
        if inner:
            found.append(inner)
        return ""

    def keep_square(match: re.Match[str]) -> str:
        inner = match.group(1).strip()
        if _looks_like_source_ref(inner, filenames):
            found.append(inner)
            return ""
        return match.group(0)

    cleaned = _CORNER_CITE_RE.sub(keep_corner, text)
    cleaned = _SQUARE_CITE_RE.sub(keep_square, cleaned)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    cleaned = re.sub(r" +([,.;:])", r"\1", cleaned)
    return cleaned.strip(), found


def _resolve_document_ids(
    token: str,
    names: dict[str, str],
    resume_id: str | None,
    job_ids: list[str],
    by_filename: dict[str, str],
) -> list[str]:
    raw = (token or "").strip()
    if not raw:
        return []
    cid = _normalize_doc_id(raw)
    if cid in names:
        return [cid]
    lower = _basename(raw).lower()
    if lower in by_filename:
        return [by_filename[lower]]
    if raw.strip().lower() in by_filename:
        return [by_filename[raw.strip().lower()]]
    if lower in _RESUME_ALIASES and resume_id and resume_id in names:
        return [resume_id]
    if lower in _JOB_ALIASES:
        return [jid for jid in job_ids if jid in names]
    return []


def _selected_citations(names: dict[str, str], resume_id: str | None, job_ids: list[str]) -> list[Any]:
    from agent.schemas import Citation

    ordered: list[Citation] = []
    seen: set[str] = set()
    for did in [resume_id, *job_ids]:
        if not did or did in seen or did not in names:
            continue
        seen.add(did)
        ordered.append(Citation(id=did, label=names[did]))
    if not ordered:
        for did, filename in names.items():
            ordered.append(Citation(id=did, label=filename))
    return ordered


def _apply_filename_citations(answer: GeneratedAnswer, state: RagState) -> None:
    from agent.schemas import Citation

    names = _document_names(state)
    mentioned: list[str] = []
    answer.text, found = _strip_inline_citations(answer.text, names)
    mentioned.extend(found)
    cleaned_strengths: list[str] = []
    for item in answer.strengths:
        text, found = _strip_inline_citations(item, names)
        mentioned.extend(found)
        if text:
            cleaned_strengths.append(text)
    answer.strengths = cleaned_strengths
    cleaned_gaps: list[str] = []
    for item in answer.gaps:
        text, found = _strip_inline_citations(item, names)
        mentioned.extend(found)
        if text:
            cleaned_gaps.append(text)
    answer.gaps = cleaned_gaps

    resume_id = _normalize_doc_id(str(state.get("resume_id") or "")) or None
    job_ids = [_normalize_doc_id(jid) for jid in (state.get("job_ids") or []) if jid]
    by_filename = _filename_index(names)

    resolved: list[Citation] = []
    seen: set[str] = set()

    def add_ids(ids: list[str]) -> None:
        for did in ids:
            if not did or did in seen or did not in names:
                continue
            seen.add(did)
            resolved.append(Citation(id=did, label=names[did]))

    for citation in answer.citations:
        add_ids(_resolve_document_ids(citation.id, names, resume_id, job_ids, by_filename))
        add_ids(_resolve_document_ids(citation.label, names, resume_id, job_ids, by_filename))
    for token in mentioned:
        add_ids(_resolve_document_ids(token, names, resume_id, job_ids, by_filename))

    if not resolved:
        resolved = _selected_citations(names, resume_id, job_ids)
    answer.citations = resolved


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
                (
                    f"Draft:\n{compact_draft(state.get('draft'))}\n\n"
                    f"Context chunks:\n{compact_chunks(state.get('chunks'))}\n\n"
                    f"Profiles:\n{compact_profiles(state.get('profiles'))}"
                ),
            ),
        ],
        event_type="rag.faithfulness",
    )
    retries = int(state.get("retries") or 0)
    usage_events = append_usage(state, usage)
    grounded = bool(result.grounded)
    if grounded:
        return {"ok": True, "grounded": True, "answer": state.get("draft"), "usage_events": usage_events}
    if retries >= 2 or not (state.get("chunks") or state.get("profiles")):
        return {"ok": True, "grounded": False, "answer": state.get("draft"), "usage_events": usage_events}
    return {"ok": False, "grounded": False, "usage_events": usage_events}


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
    validated = bool(state.get("grounded"))
    extra: dict[str, Any] = {
        "strengths": answer.get("strengths"),
        "gaps": answer.get("gaps"),
        "usage": usage,
        "validated": validated,
    }
    if answer.get("table"):
        extra["table"] = answer.get("table")
    if answer.get("code"):
        extra["code"] = answer.get("code")
    saved_assistant = tools.invoke(
        "save_conversation_message",
        user_id=user_id,
        conversation_id=convo_id,
        role="assistant",
        content=answer.get("text") or "",
        citations=answer.get("citations"),
        extra=extra,
    )
    channel = str(state.get("channel") or "assistant")
    persist_usage_events(
        user_id=user_id,
        conversation_id=convo_id,
        events=state.get("usage_events") or [],
        extra={
            "ui_model": state.get("model"),
            "channel": channel,
            "feature": "interview" if channel in {"interview", "extract_topics"} else "chat",
            "details": question_usage_details(state.get("question"), extract_topics=channel == "extract_topics"),
        },
    )
    return {
        "conversation_id": str(convo_id),
        "message_id": saved_assistant.get("message_id"),
        "validated": validated,
        "answer": answer,
        "usage": usage,
    }
