from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from backend.realtime import document_events
from backend.security import decode_access_token

router = APIRouter(tags=["realtime"])


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
