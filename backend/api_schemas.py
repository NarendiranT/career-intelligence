from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class DocumentOut(BaseModel):
    id: UUID
    filename: str
    doc_type: str | None
    status: str
    mime: str | None = None
    size: int | None = None
    error_message: str | None = None
    created_at: datetime | None = None


class ChatRequest(BaseModel):
    question: str
    resume_id: UUID | None = None
    job_ids: list[UUID] = Field(default_factory=list)
    stream: bool = False
    conversation_id: UUID | None = None


class CitationOut(BaseModel):
    id: str
    label: str


class ChatResponse(BaseModel):
    conversation_id: UUID | None = None
    text: str
    citations: list[CitationOut] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)


class HomeStatsOut(BaseModel):
    resume_count: int
    job_count: int
    insight_count: int
    saved_result_count: int


class HomeConversationOut(BaseModel):
    id: UUID
    title: str
    updated_at: datetime | None = None


class HomeSummaryOut(BaseModel):
    documents: list[DocumentOut]
    stats: HomeStatsOut
    conversations: list[HomeConversationOut]
