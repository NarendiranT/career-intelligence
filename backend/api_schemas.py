from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
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
    temperature: float = Field(default=0.7, ge=0, le=2)
    top_p: float = Field(default=1, ge=0, le=1)
    max_tokens: int = Field(default=1024, ge=64, le=8192)
    system_prompt: str = ""
    model: str = ""
    channel: Literal["assistant", "interview", "extract_topics"] = "assistant"
    topic_id: UUID | None = None
    source_conversation_id: UUID | None = None
    source_message_id: UUID | None = None


class TopicOut(BaseModel):
    id: UUID
    label: str
    slug: str
    conversation_id: UUID | None = None
    created_at: datetime | None = None
    question_count: int = 0


class TopicDetailOut(TopicOut):
    context: dict[str, Any] | None = None
    resume_id: UUID | None = None
    job_ids: list[UUID] = Field(default_factory=list)


class AnswerTableOut(BaseModel):
    headers: list[str] = Field(default_factory=list)
    rows: list[list[str]] = Field(default_factory=list)


class AnswerCodeOut(BaseModel):
    language: str = ""
    content: str = ""


class CitationOut(BaseModel):
    id: str
    label: str


class TokenUsageOut(BaseModel):
    tokens: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0


class ChatResponse(BaseModel):
    conversation_id: UUID | None = None
    text: str
    citations: list[CitationOut] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    usage: TokenUsageOut = Field(default_factory=TokenUsageOut)
    channel: str = "assistant"
    topic_id: UUID | None = None
    topics: list[TopicOut] = Field(default_factory=list)
    table: AnswerTableOut | None = None
    code: AnswerCodeOut | None = None
    validated: bool = False
    message_id: UUID | None = None
    topics_existing: bool = False


class UsageByEventOut(BaseModel):
    event_type: str
    tokens: int
    count: int


class UsageFeatureOut(BaseModel):
    id: str
    label: str
    tokens: int
    percent: int
    activity_count: int


class UsageDailyOut(BaseModel):
    date: str
    chat: int
    interview: int
    documents: int


class UsageActivityOut(BaseModel):
    id: str
    created_at: datetime
    feature: str
    tokens: int
    details: str


class UsageActivitiesOut(BaseModel):
    start: str
    end: str
    activities: list[UsageActivityOut] = Field(default_factory=list)


class UsageSummaryOut(BaseModel):
    range: str = "30d"
    days: int = 30
    total_tokens: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    event_count: int = 0
    range_tokens: int = 0
    previous_range_tokens: int = 0
    delta_percent: int = 0
    by_event_type: list[UsageByEventOut] = Field(default_factory=list)
    features: list[UsageFeatureOut] = Field(default_factory=list)
    daily: list[UsageDailyOut] = Field(default_factory=list)
    recent: list[UsageActivityOut] = Field(default_factory=list)


class HomeStatsOut(BaseModel):
    resume_count: int
    job_count: int
    insight_count: int
    saved_result_count: int


class ConversationOut(BaseModel):
    id: UUID
    title: str
    updated_at: datetime | None = None
    bookmarked: bool = False


class ConversationBookmarkIn(BaseModel):
    bookmarked: bool


class ConversationMessageOut(BaseModel):
    id: UUID
    role: str
    content: str
    citations: list[CitationOut] = Field(default_factory=list)
    extra: dict[str, Any] | None = None
    created_at: datetime | None = None


class ConversationDetailOut(ConversationOut):
    resume_id: UUID | None = None
    job_ids: list[UUID] = Field(default_factory=list)
    messages: list[ConversationMessageOut] = Field(default_factory=list)


class HomeSummaryOut(BaseModel):
    documents: list[DocumentOut]
    stats: HomeStatsOut
    conversations: list[ConversationOut]
    saved_results: list[ConversationOut] = Field(default_factory=list)


class SkillItemOut(BaseModel):
    name: str
    proficiency: int


class SkillCategoryOut(BaseModel):
    name: str
    skills: list[SkillItemOut] = Field(default_factory=list)


class SkillActivityOut(BaseModel):
    kind: str
    label: str
    detail: str = ""
    created_at: datetime | None = None


class SkillsSummaryOut(BaseModel):
    resume_count: int = 0
    total_skills: int = 0
    skill_summary: str = ""
    insights: list[str] = Field(default_factory=list)
    categories: list[SkillCategoryOut] = Field(default_factory=list)
    recent_activity: list[SkillActivityOut] = Field(default_factory=list)
