from __future__ import annotations

import asyncio
import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sse_starlette.sse import EventSourceResponse

from agent.rag.graph import rag_graph
from backend.api_schemas import (
    AnswerCodeOut,
    AnswerTableOut,
    ChatRequest,
    ChatResponse,
    CitationOut,
    TokenUsageOut,
    TopicOut,
)
from backend.deps import get_user_id
from backend.errors import MissingLLMConfigError

router = APIRouter(prefix="/v1/chat", tags=["chat"])


def rag_input(user_id: UUID, body: ChatRequest) -> dict:
    return {
        "user_id": str(user_id),
        "question": body.question,
        "resume_id": str(body.resume_id) if body.resume_id else None,
        "job_ids": [str(i) for i in body.job_ids],
        "conversation_id": str(body.conversation_id) if body.conversation_id else None,
        "temperature": body.temperature,
        "top_p": body.top_p,
        "max_tokens": body.max_tokens,
        "system_prompt": body.system_prompt,
        "web_search": body.web_search,
        "model": body.model,
        "channel": body.channel,
        "topic_id": str(body.topic_id) if body.topic_id else None,
        "source_conversation_id": str(body.source_conversation_id) if body.source_conversation_id else None,
        "source_message_id": str(body.source_message_id) if body.source_message_id else None,
    }


def invoke_rag(user_id: UUID, body: ChatRequest) -> dict:
    return rag_graph.invoke(rag_input(user_id, body))


def _table_out(raw: object) -> AnswerTableOut | None:
    if not isinstance(raw, dict):
        return None
    headers = raw.get("headers") or []
    rows = raw.get("rows") or []
    if not isinstance(headers, list) or not isinstance(rows, list):
        return None
    if not headers and not rows:
        return None
    return AnswerTableOut(
        headers=[str(item) for item in headers],
        rows=[[str(cell) for cell in row] if isinstance(row, list) else [str(row)] for row in rows],
    )


def _code_out(raw: object) -> AnswerCodeOut | None:
    if not isinstance(raw, dict):
        return None
    language = str(raw.get("language") or "")
    content = str(raw.get("content") or "")
    if not content:
        return None
    return AnswerCodeOut(language=language, content=content)


def to_chat_response(result: dict) -> ChatResponse:
    answer = result.get("answer") or {}
    conversation_id = result.get("conversation_id")
    citations = [
        CitationOut(id=c.get("id", ""), label=c.get("label", ""))
        for c in (answer.get("citations") or [])
        if isinstance(c, dict)
    ]
    usage_raw = result.get("usage") or {}
    usage = TokenUsageOut(
        tokens=int(usage_raw.get("tokens") or 0),
        prompt_tokens=int(usage_raw.get("prompt_tokens") or 0),
        completion_tokens=int(usage_raw.get("completion_tokens") or 0),
    )
    topics: list[TopicOut] = []
    for item in result.get("topics") or []:
        if not isinstance(item, dict) or not item.get("id"):
            continue
        topics.append(TopicOut.model_validate(item))
    message_id = result.get("message_id")
    return ChatResponse(
        conversation_id=UUID(conversation_id) if conversation_id else None,
        text=answer.get("text") or result.get("error") or "",
        citations=citations,
        strengths=answer.get("strengths") or [],
        gaps=answer.get("gaps") or [],
        usage=usage,
        channel=str(result.get("channel") or "assistant"),
        topic_id=UUID(str(result.get("topic_id"))) if result.get("topic_id") else None,
        topics=topics,
        table=_table_out(answer.get("table")),
        code=_code_out(answer.get("code")),
        validated=bool(result.get("validated")),
        message_id=UUID(str(message_id)) if message_id else None,
        topics_existing=bool(result.get("topics_existing")),
    )


def chat_error_detail(result: dict) -> str | None:
    if result.get("blocked") and result.get("error"):
        return str(result["error"])
    return None


@router.post("")
async def chat(body: ChatRequest, user_id: UUID = Depends(get_user_id)):
    try:
        result = await asyncio.to_thread(invoke_rag, user_id, body)
    except MissingLLMConfigError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail="chat failed") from exc

    payload = to_chat_response(result)
    blocked = chat_error_detail(result)
    if blocked:
        raise HTTPException(status_code=400, detail=blocked)

    if not body.stream:
        return payload

    async def events():
        text = payload.text
        step = 16
        for i in range(0, len(text), step):
            yield {
                "event": "token",
                "data": json.dumps({"text": text[i : i + step]}),
            }
            await asyncio.sleep(0)
        yield {
            "event": "done",
            "data": payload.model_dump_json(),
        }

    return EventSourceResponse(events())
