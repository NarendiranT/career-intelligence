from __future__ import annotations

import asyncio
import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sse_starlette.sse import EventSourceResponse

from agent.rag.graph import rag_graph
from backend.api_schemas import ChatRequest, ChatResponse, CitationOut
from backend.deps import get_user_id
from backend.errors import MissingLLMConfigError

router = APIRouter(prefix="/v1/chat", tags=["chat"])


def _invoke_rag(user_id: UUID, body: ChatRequest) -> dict:
    return rag_graph.invoke(
        {
            "user_id": str(user_id),
            "question": body.question,
            "resume_id": str(body.resume_id) if body.resume_id else None,
            "job_ids": [str(i) for i in body.job_ids],
            "conversation_id": str(body.conversation_id) if body.conversation_id else None,
        }
    )


def _to_response(result: dict) -> ChatResponse:
    answer = result.get("answer") or {}
    conversation_id = result.get("conversation_id")
    citations = [
        CitationOut(id=c.get("id", ""), label=c.get("label", ""))
        for c in (answer.get("citations") or [])
        if isinstance(c, dict)
    ]
    return ChatResponse(
        conversation_id=UUID(conversation_id) if conversation_id else None,
        text=answer.get("text") or result.get("error") or "",
        citations=citations,
        strengths=answer.get("strengths") or [],
        gaps=answer.get("gaps") or [],
    )


@router.post("")
async def chat(body: ChatRequest, user_id: UUID = Depends(get_user_id)):
    try:
        result = await asyncio.to_thread(_invoke_rag, user_id, body)
    except MissingLLMConfigError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail="chat failed") from exc

    payload = _to_response(result)
    if result.get("blocked") and result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])

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
