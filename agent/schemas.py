from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ExperienceItem(BaseModel):
    company: str | None = None
    title: str | None = None
    dates: str | None = None
    highlights: list[str] = Field(default_factory=list)


class EducationItem(BaseModel):
    school: str | None = None
    degree: str | None = None
    dates: str | None = None


class ResumeProfile(BaseModel):
    name: str | None = None
    headline: str | None = None
    skills: list[str] = Field(default_factory=list)
    experience: list[ExperienceItem] = Field(default_factory=list)
    education: list[EducationItem] = Field(default_factory=list)
    summary: str | None = None


class JobProfile(BaseModel):
    title: str | None = None
    company: str | None = None
    skills: list[str] = Field(default_factory=list)
    requirements: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    summary: str | None = None


class DocumentClassification(BaseModel):
    doc_type: Literal["resume", "job"]
    confidence: float = 0.0
    reason: str = ""


class QueryPlan(BaseModel):
    intent: Literal["resume", "job", "comparison", "general"]
    rewritten_query: str


class Citation(BaseModel):
    id: str
    label: str


class GeneratedAnswer(BaseModel):
    text: str
    citations: list[Citation] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)


class FaithfulnessResult(BaseModel):
    grounded: bool
    reason: str = ""


class RetrievedChunk(BaseModel):
    document_id: str
    filename: str
    content: str
    distance: float = 0.0
