from __future__ import annotations

import time
from typing import Any

from pydantic import BaseModel

from mcp.registry import tools


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


def persist_usage_events(
    *,
    user_id: Any,
    conversation_id: Any = None,
    events: list[dict[str, Any]] | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    for event in events or []:
        payload_extra: dict[str, Any] = {
            "input_tokens": _as_int(event.get("input_tokens")),
            "output_tokens": _as_int(event.get("output_tokens")),
        }
        if extra:
            payload_extra.update(extra)
        tools.invoke(
            "update_usage",
            user_id=user_id,
            conversation_id=conversation_id,
            event_type=str(event.get("event_type") or "llm"),
            model=event.get("model"),
            tokens=_as_int(event.get("tokens") or event.get("total_tokens")),
            latency_ms=event.get("latency_ms"),
            extra=payload_extra,
        )
