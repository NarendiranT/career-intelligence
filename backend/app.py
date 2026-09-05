from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from backend.config import settings
from backend.db import engine
from backend.errors import MissingLLMConfigError
from backend.routers.auth import router as auth_router
from backend.routers.chat import router as chat_router
from backend.routers.documents import router as documents_router
from backend.routers.home import router as home_router

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
app.include_router(documents_router)
app.include_router(chat_router)


@app.on_event("startup")
def on_startup() -> None:
    settings.uploads_dir.mkdir(parents=True, exist_ok=True)


@app.exception_handler(MissingLLMConfigError)
async def missing_llm_handler(_, exc: MissingLLMConfigError):
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.get("/health")
def health() -> dict[str, str]:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"status": "ok"}
