from __future__ import annotations

import time
import uuid
from typing import Any

from pydantic import BaseModel

from mcp.registry import tools

DETAILS_MAX = 160


def _as_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def extract_token_usage(raw: Any) -> dict[str, int]:
    """Read prompt/completion/total tokens from a LangChain or Groq payload."""
    input_tokens = 0
    output_tokens = 0
    total_tokens = 0

    if raw is None:
        return {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}

    payload = raw
    if isinstance(raw, dict):
        payload = raw.get("raw", raw)

    usage_meta = getattr(payload, "usage_metadata", None)
    if usage_meta is None and isinstance(payload, dict):
        usage_meta = payload.get("usage_metadata")
    if isinstance(usage_meta, dict):
        input_tokens = _as_int(usage_meta.get("input_tokens") or usage_meta.get("prompt_tokens"))
        output_tokens = _as_int(usage_meta.get("output_tokens") or usage_meta.get("completion_tokens"))
        total_tokens = _as_int(usage_meta.get("total_tokens"))

    response_meta = getattr(payload, "response_metadata", None)
    if response_meta is None and isinstance(payload, dict):
        response_meta = payload.get("response_metadata")
    token_usage = {}
    if isinstance(response_meta, dict):
        token_usage = response_meta.get("token_usage") or response_meta.get("usage") or {}
    elif isinstance(payload, dict):
        token_usage = payload.get("token_usage") or payload.get("usage") or {}
    if isinstance(token_usage, dict):
        input_tokens = input_tokens or _as_int(token_usage.get("prompt_tokens") or token_usage.get("input_tokens"))
        output_tokens = output_tokens or _as_int(
            token_usage.get("completion_tokens") or token_usage.get("output_tokens")
        )
        total_tokens = total_tokens or _as_int(token_usage.get("total_tokens"))

    if not total_tokens:
        total_tokens = input_tokens + output_tokens
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
    }


def model_name(llm: Any) -> str | None:
    value = getattr(llm, "model_name", None) or getattr(llm, "model", None)
    if value is None:
        return None
    return str(value)


def unwrap_structured(result: Any, schema: type[BaseModel]) -> tuple[Any, Any]:
    if isinstance(result, schema):
        return result, None
    if isinstance(result, dict) and "parsed" in result:
        return result["parsed"], result.get("raw")
    return result, None


def summarize_usage(events: list[dict[str, Any]] | None) -> dict[str, int]:
    prompt = 0
    completion = 0
    total = 0
    for event in events or []:
        prompt += _as_int(event.get("input_tokens"))
        completion += _as_int(event.get("output_tokens"))
        total += _as_int(event.get("tokens") or event.get("total_tokens"))
    if not total:
        total = prompt + completion
    return {"tokens": total, "prompt_tokens": prompt, "completion_tokens": completion}


def append_usage(state: dict[str, Any], usage: dict[str, Any] | None) -> list[dict[str, Any]]:
    events = list(state.get("usage_events") or [])
    if usage:
        events.append(usage)
    return events


def timed_invoke(runnable: Any, payload: Any) -> tuple[Any, float]:
    started = time.perf_counter()
    result = runnable.invoke(payload)
    latency_ms = round((time.perf_counter() - started) * 1000, 2)
    return result, latency_ms


def clip_details(text: str, limit: int = DETAILS_MAX) -> str:
    value = " ".join((text or "").split())
    if len(value) <= limit:
        return value
    return value[: max(0, limit - 1)].rstrip() + "…"


def feature_for_event(*, event_type: str, channel: str | None = None) -> str:
    if (event_type or "").startswith("indexing."):
        return "documents"
    if channel in {"interview", "extract_topics"} or event_type == "rag.extract_topics":
        return "interview"
    return "chat"


def document_usage_details(doc_type: str | None, filename: str | None) -> str:
    if doc_type == "resume":
        kind = "resume"
    elif doc_type == "job":
        kind = "job description"
    else:
        kind = "document"
    name = (filename or "").strip()
    if name:
        return clip_details(f"Processed {kind} ({name})")
    return f"Processed {kind}"


def default_feature_details(feature: str) -> str:
    if feature == "interview":
        return "Interview Preparation"
    if feature == "documents":
        return "Document processing"
    return "Chat with Assistant"


def question_usage_details(question: str | None, *, extract_topics: bool = False) -> str:
    if extract_topics:
        return "Extracted interview topics"
    text = clip_details(question or "")
    if not text:
        return default_feature_details("chat")
    return clip_details(f"Asked about {text}")


def persist_usage_events(
    *,
    user_id: Any,
    conversation_id: Any = None,
    events: list[dict[str, Any]] | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    snapshot = dict(extra or {})
    snapshot["activity_id"] = str(snapshot.get("activity_id") or uuid.uuid4())
    channel = snapshot.get("channel")
    if channel is not None:
        snapshot["channel"] = str(channel)
    for event in events or []:
        event_type = str(event.get("event_type") or "llm")
        payload_extra: dict[str, Any] = {
            "input_tokens": _as_int(event.get("input_tokens")),
            "output_tokens": _as_int(event.get("output_tokens")),
        }
        payload_extra.update(snapshot)
        payload_extra["feature"] = payload_extra.get("feature") or feature_for_event(
            event_type=event_type, channel=payload_extra.get("channel")
        )
        if not payload_extra.get("details"):
            if payload_extra["feature"] == "documents":
                payload_extra["details"] = document_usage_details(
                    payload_extra.get("doc_type"), payload_extra.get("filename")
                )
            else:
                payload_extra["details"] = question_usage_details(
                    None, extract_topics=payload_extra.get("channel") == "extract_topics"
                )
        tools.invoke(
            "update_usage",
            user_id=user_id,
            conversation_id=conversation_id,
            event_type=event_type,
            model=event.get("model"),
            tokens=_as_int(event.get("tokens") or event.get("total_tokens")),
            latency_ms=event.get("latency_ms"),
            extra=payload_extra,
        )
