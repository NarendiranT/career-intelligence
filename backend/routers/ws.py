from __future__ import annotations

import asyncio
import logging
from uuid import UUID

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from backend.api_schemas import ChatRequest
from backend.errors import MissingLLMConfigError
from backend.realtime import document_events
from backend.routers.chat import chat_error_detail, invoke_rag, to_chat_response
from backend.security import decode_access_token

logger = logging.getLogger(__name__)

router = APIRouter(tags=["realtime"])

_TOKEN_CHUNK = 16


def _user_id_from_token(token: str | None) -> UUID | None:
    if not token:
        return None
    try:
        payload = decode_access_token(token)
        return UUID(str(payload["sub"]))
    except Exception:
        return None


@router.websocket("/v1/ws/documents")
async def document_status_ws(
    websocket: WebSocket,
    token: str | None = Query(default=None),
) -> None:
    user_id = _user_id_from_token(token)
    if user_id is None:
        await websocket.close(code=4401)
        return
    await document_events.connect(user_id, websocket)
    try:
        while True:
            message = await websocket.receive()
            if message.get("type") == "websocket.disconnect":
                break
    except WebSocketDisconnect:
        pass
    finally:
        document_events.disconnect(user_id, websocket)


@router.websocket("/v1/ws/chat")
async def chat_ws(
    websocket: WebSocket,
    token: str | None = Query(default=None),
) -> None:
    user_id = _user_id_from_token(token)
    if user_id is None:
        await websocket.close(code=4401)
        return
    await websocket.accept()
    busy = False
    try:
        while True:
            raw = await websocket.receive_json()
            if not isinstance(raw, dict) or raw.get("type") != "chat.ask":
                await websocket.send_json({"type": "chat.error", "detail": "expected chat.ask"})
                continue
            if busy:
                await websocket.send_json({"type": "chat.error", "detail": "a request is already in progress"})
                continue
            payload = {k: v for k, v in raw.items() if k != "type"}
            try:
                body = ChatRequest.model_validate(payload)
            except ValidationError as exc:
                await websocket.send_json({"type": "chat.error", "detail": str(exc.errors()[0].get("msg", "invalid request"))})
                continue
            busy = True
            try:
                await websocket.send_json({"type": "chat.status", "status": "running"})
                result = await asyncio.to_thread(invoke_rag, user_id, body)
                blocked = chat_error_detail(result)
                if blocked:
                    await websocket.send_json({"type": "chat.error", "detail": blocked})
                    continue
                response = to_chat_response(result)
                done = {"type": "chat.done", **response.model_dump(mode="json")}
                if body.stream:
                    text = response.text
                    for i in range(0, len(text), _TOKEN_CHUNK):
                        await websocket.send_json({"type": "chat.token", "text": text[i : i + _TOKEN_CHUNK]})
                        await asyncio.sleep(0)
                await websocket.send_json(done)
            except MissingLLMConfigError as exc:
                await websocket.send_json({"type": "chat.error", "detail": str(exc)})
            except Exception:
                logger.exception("chat websocket request failed")
                await websocket.send_json({"type": "chat.error", "detail": "chat failed"})
            finally:
                busy = False
    except WebSocketDisconnect:
        pass
