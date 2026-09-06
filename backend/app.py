from __future__ import annotations

import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from backend.config import settings
from backend.db import engine
from backend.telemetry import setup_telemetry
from backend.errors import MissingLLMConfigError
from backend.realtime import document_events
from backend.routers.auth import router as auth_router
from backend.routers.chat import router as chat_router
from backend.routers.conversations import router as conversations_router
from backend.routers.documents import router as documents_router
from backend.routers.home import router as home_router
from backend.routers.skills import router as skills_router
from backend.routers.topics import router as topics_router
from backend.routers.usage import router as usage_router
from backend.routers.ws import router as ws_router

app = FastAPI(title="Career Intelligence API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)
app.include_router(home_router)
app.include_router(skills_router)
app.include_router(usage_router)
app.include_router(documents_router)
app.include_router(chat_router)
app.include_router(conversations_router)
app.include_router(topics_router)
app.include_router(ws_router)
setup_telemetry(app)


@app.on_event("startup")
async def on_startup() -> None:
    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    document_events.bind_loop(asyncio.get_running_loop())


@app.exception_handler(MissingLLMConfigError)
async def missing_llm_handler(_, exc: MissingLLMConfigError):
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.get("/health")
def health() -> dict[str, str]:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"status": "ok"}
