import os
from typing import Any, Literal
import logging

from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from pydantic import BaseModel

from agent.context_budget import EXTRACTION_MAX_TOKENS, ROUTER_MAX_TOKENS, cap_generation_max_tokens
from agent.usage import (
    coerce_to_schema,
    extract_token_usage,
    model_name,
    salvage_structured,
    timed_invoke,
    unwrap_structured,
    _message_text,
)
from backend.config import settings
from backend.errors import MissingLLMConfigError
from backend.telemetry import llm_invoke_span, record_llm_usage

logger = logging.getLogger(__name__)

ChatRole = Literal["extraction", "router", "generation"]
StructuredMethod = Literal["json_schema", "json_mode"]


def require_groq() -> None:
    key = settings.groq_api_key or os.environ.get("GROQ_API_KEY", "")
    if not key.strip():
        raise MissingLLMConfigError("GROQ_API_KEY is not configured")
    os.environ["GROQ_API_KEY"] = key


def chat_model_kwargs(
    *,
    role: ChatRole = "generation",
    temperature: float = 0,
    max_tokens: int | None = None,
    top_p: float | None = None,
) -> dict[str, Any]:
    """Build ChatGroq kwargs. Always set max_tokens: Groq TPM counts prompt + declared max_tokens."""
    models = {
        "extraction": settings.extraction_model,
        "router": settings.router_model,
        "generation": settings.generation_model,
    }
    if role == "generation":
        completion = cap_generation_max_tokens(max_tokens)
    elif role == "extraction":
        completion = EXTRACTION_MAX_TOKENS if max_tokens is None else min(int(max_tokens), EXTRACTION_MAX_TOKENS)
    else:
        completion = ROUTER_MAX_TOKENS if max_tokens is None else min(int(max_tokens), ROUTER_MAX_TOKENS)
    kwargs: dict[str, Any] = {"model": models[role], "temperature": temperature, "max_tokens": completion}
    if "gpt-oss" in str(models[role]):
        kwargs["reasoning_effort"] = "low"
    if top_p is not None:
        kwargs["model_kwargs"] = {"top_p": top_p}
    return kwargs


def get_chat_model(
    *,
    role: ChatRole = "generation",
    temperature: float = 0,
    max_tokens: int | None = None,
    top_p: float | None = None,
) -> ChatGroq:
    require_groq()
    return ChatGroq(**chat_model_kwargs(role=role, temperature=temperature, max_tokens=max_tokens, top_p=top_p))


def _with_json_schema_hint(messages: list[Any], schema: type[BaseModel]) -> list[Any]:
    hint = (
        "Return only a JSON object that matches this schema. "
        "Do not wrap it in markdown. Do not call tools.\n"
        f"{schema.model_json_schema()}"
    )
    if not messages:
        return [("system", hint)]
    first = messages[0]
    if isinstance(first, tuple) and first and first[0] == "system":
        return [(first[0], f"{first[1]}\n\n{hint}"), *messages[1:]]
    return [("system", hint), *messages]


def _structured_runnable(llm: Any, schema: type[BaseModel], **kwargs: Any) -> Any:
    try:
        return llm.with_structured_output(schema, include_raw=True, **kwargs)
    except TypeError:
        return llm.with_structured_output(schema, **kwargs)


def invoke_structured_tracked(
    llm: Any,
    schema: type[BaseModel],
    messages: list[Any],
    *,
    event_type: str,
) -> tuple[Any, dict[str, Any]]:
    """Like ``invoke_structured``, plus token counts and latency for usage tracking."""
    last_error: BaseException | None = None
    attempts: list[tuple[StructuredMethod, dict[str, Any]]] = [
        ("json_schema", {"strict": True}),
        ("json_mode", {}),
    ]
    model = model_name(llm)
    for method, extra in attempts:
        try:
            runnable = _structured_runnable(llm, schema, method=method, **extra)
            payload = messages if method == "json_schema" else _with_json_schema_hint(messages, schema)
            with llm_invoke_span(event_type=event_type, model=model) as span:
                result, latency_ms = timed_invoke(runnable, payload)
                parsed, raw = unwrap_structured(result, schema)
                tokens = extract_token_usage(raw if raw is not None else result)
                usage = {
                    "event_type": event_type,
                    "model": model,
                    "input_tokens": tokens["input_tokens"],
                    "output_tokens": tokens["output_tokens"],
                    "tokens": tokens["total_tokens"],
                    "latency_ms": latency_ms,
                }
                span.set_attribute("gen_ai.usage.input_tokens", tokens["input_tokens"])
                span.set_attribute("gen_ai.usage.output_tokens", tokens["output_tokens"])
                span.set_attribute("ci.llm.latency_ms", latency_ms)
                record_llm_usage(
                    event_type=event_type,
                    model=model,
                    input_tokens=tokens["input_tokens"],
                    output_tokens=tokens["output_tokens"],
                    latency_ms=latency_ms,
                )
                return parsed, usage
        except TypeError as exc:
            if "method" not in str(exc) and "unexpected keyword" not in str(exc).lower():
                raise
            with llm_invoke_span(event_type=event_type, model=model) as span:
                result, latency_ms = timed_invoke(llm.with_structured_output(schema), messages)
                parsed, raw = unwrap_structured(result, schema)
                tokens = extract_token_usage(raw if raw is not None else result)
                span.set_attribute("gen_ai.usage.input_tokens", tokens["input_tokens"])
                span.set_attribute("gen_ai.usage.output_tokens", tokens["output_tokens"])
                span.set_attribute("ci.llm.latency_ms", latency_ms)
                record_llm_usage(
                    event_type=event_type,
                    model=model,
                    input_tokens=tokens["input_tokens"],
                    output_tokens=tokens["output_tokens"],
                    latency_ms=latency_ms,
                )
                return parsed, {
                    "event_type": event_type,
                    "model": model,
                    "input_tokens": tokens["input_tokens"],
                    "output_tokens": tokens["output_tokens"],
                    "tokens": tokens["total_tokens"],
                    "latency_ms": latency_ms,
                }
        except MissingLLMConfigError:
            raise
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            salvaged = salvage_structured(schema, exc)
            if salvaged is not None:
                logger.warning("structured output %s failed; salvaged failed_generation", method)
                return salvaged, {
                    "event_type": event_type,
                    "model": model,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "tokens": 0,
                    "latency_ms": 0,
                }
            if method != "json_mode":
                logger.warning("structured output %s failed; retrying with json_mode: %s", method, exc)
                continue
            parsed = _plain_text_fallback(llm, schema, messages, event_type=event_type, model=model)
            if parsed is not None:
                return parsed
            raise
    if last_error:
        raise last_error
    raise RuntimeError("structured output failed")


def _plain_text_fallback(
    llm: Any,
    schema: type[BaseModel],
    messages: list[Any],
    *,
    event_type: str,
    model: str | None,
) -> tuple[Any, dict[str, Any]] | None:
    if "text" not in getattr(schema, "model_fields", {}):
        return None
    try:
        with llm_invoke_span(event_type=event_type, model=model) as span:
            result, latency_ms = timed_invoke(llm, _with_json_schema_hint(messages, schema))
            tokens = extract_token_usage(result)
            text = _message_text(result)
            span.set_attribute("gen_ai.usage.input_tokens", tokens["input_tokens"])
            span.set_attribute("gen_ai.usage.output_tokens", tokens["output_tokens"])
            span.set_attribute("ci.llm.latency_ms", latency_ms)
            record_llm_usage(
                event_type=event_type,
                model=model,
                input_tokens=tokens["input_tokens"],
                output_tokens=tokens["output_tokens"],
                latency_ms=latency_ms,
            )
            parsed = coerce_to_schema(schema, text)
            if parsed is None and text.strip():
                parsed = schema.model_validate({"text": text.strip()})
            if parsed is None:
                return None
            return parsed, {
                "event_type": event_type,
                "model": model,
                "input_tokens": tokens["input_tokens"],
                "output_tokens": tokens["output_tokens"],
                "tokens": tokens["total_tokens"],
                "latency_ms": latency_ms,
            }
    except Exception as exc:  # noqa: BLE001
        logger.warning("plain-text fallback failed: %s", exc)
        return None


def invoke_structured(llm: Any, schema: type[BaseModel], messages: list[Any]) -> Any:
    """Parse a Pydantic schema without Groq tool-calling.

    gpt-oss models often return invalid tool-call JSON (``tool_use_failed``).
    Prefer constrained JSON schema, then JSON object mode.
    """
    parsed, _usage = invoke_structured_tracked(llm, schema, messages, event_type="llm")
    return parsed


def get_embeddings() -> HuggingFaceEmbeddings:
    token = settings.hf_token or os.environ.get("HF_TOKEN", "") or os.environ.get("HUGGINGFACEHUB_API_TOKEN", "")
    if token.strip():
        os.environ.setdefault("HF_TOKEN", token)
    return HuggingFaceEmbeddings(
        model_name=settings.embedding_model,
        model_kwargs={"device": settings.embedding_device},
        encode_kwargs={"normalize_embeddings": True},
    )
