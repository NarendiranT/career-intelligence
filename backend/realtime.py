from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from typing import Any
from uuid import UUID

from fastapi import WebSocket
from starlette.websockets import WebSocketState

logger = logging.getLogger(__name__)


class DocumentEventHub:
    def __init__(self) -> None:
        self._loop: asyncio.AbstractEventLoop | None = None
        self._connections: dict[UUID, set[WebSocket]] = defaultdict(set)

    def bind_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    async def connect(self, user_id: UUID, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections[user_id].add(websocket)

    def disconnect(self, user_id: UUID, websocket: WebSocket) -> None:
        sockets = self._connections.get(user_id)
        if not sockets:
            return
        sockets.discard(websocket)
        if not sockets:
            self._connections.pop(user_id, None)

    async def _broadcast(self, user_id: UUID, message: dict[str, Any]) -> None:
        sockets = list(self._connections.get(user_id, ()))
        for websocket in sockets:
            if websocket.client_state != WebSocketState.CONNECTED:
                self.disconnect(user_id, websocket)
                continue
            try:
                await websocket.send_json(message)
            except Exception:
                logger.debug("dropping stale document websocket for %s", user_id, exc_info=True)
                self.disconnect(user_id, websocket)

    def publish(self, user_id: UUID, message: dict[str, Any]) -> None:
        try:
            loop = asyncio.get_running_loop()
            self._loop = loop
            loop.create_task(self._broadcast(user_id, message))
            return
        except RuntimeError:
            loop = self._loop
        if loop is None or not loop.is_running():
            logger.debug("no event loop to publish document event for %s", user_id)
            return
        asyncio.run_coroutine_threadsafe(self._broadcast(user_id, message), loop)


document_events = DocumentEventHub()


def publish_document_status(user_id: UUID, document: dict[str, Any]) -> None:
    document_events.publish(
        user_id,
        {"type": "document.status", "document": document},
    )


def publish_document_deleted(user_id: UUID, document_id: UUID) -> None:
    document_events.publish(
        user_id,
        {"type": "document.deleted", "document_id": str(document_id)},
    )
