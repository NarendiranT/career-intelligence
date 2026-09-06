from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

SkillCategory = Literal[
    "Programming Languages",
    "Frameworks & Libraries",
    "Cloud & DevOps",
    "AI / Machine Learning",
    "Databases & Storage",
    "Other Skills",
]

SKILL_CATEGORIES: tuple[SkillCategory, ...] = (
    "Programming Languages",
    "Frameworks & Libraries",
    "Cloud & DevOps",
    "AI / Machine Learning",
    "Databases & Storage",
    "Other Skills",
)

_CATEGORY_ALIASES: dict[str, SkillCategory] = {
    "programming languages": "Programming Languages",
    "languages": "Programming Languages",
    "frameworks & libraries": "Frameworks & Libraries",
    "frameworks": "Frameworks & Libraries",
    "libraries": "Frameworks & Libraries",
    "cloud & devops": "Cloud & DevOps",
    "devops": "Cloud & DevOps",
    "devops & ci/cd": "Cloud & DevOps",
    "ci/cd": "Cloud & DevOps",
    "cloud": "Cloud & DevOps",
    "ai / machine learning": "AI / Machine Learning",
    "ai": "AI / Machine Learning",
    "machine learning": "AI / Machine Learning",
    "ml": "AI / Machine Learning",
    "databases & storage": "Databases & Storage",
    "databases": "Databases & Storage",
    "storage": "Databases & Storage",
    "other skills": "Other Skills",
    "other": "Other Skills",
}


def normalize_skill_category(value: Any) -> SkillCategory:
    if not isinstance(value, str):
        return "Other Skills"
    text = " ".join(value.strip().split())
    if text in SKILL_CATEGORIES:
        return text  # type: ignore[return-value]
    mapped = _CATEGORY_ALIASES.get(text.lower())
    if mapped:
        return mapped
    lowered = text.lower()
    if "devops" in lowered or "ci/cd" in lowered or "cloud" in lowered:
        return "Cloud & DevOps"
    if "machine learning" in lowered or lowered in {"ai", "ml"}:
        return "AI / Machine Learning"
    if "database" in lowered or "storage" in lowered:
        return "Databases & Storage"
    if "framework" in lowered or "librar" in lowered:
        return "Frameworks & Libraries"
    if "language" in lowered:
        return "Programming Languages"
    return "Other Skills"


class ExperienceItem(BaseModel):
    company: str | None = None
    title: str | None = None
    dates: str | None = None
    highlights: list[str] = Field(default_factory=list)


class EducationItem(BaseModel):
    school: str | None = None
    degree: str | None = None
    dates: str | None = None


class ResumeSkill(BaseModel):
    name: str
    category: SkillCategory = "Other Skills"
    proficiency: int = Field(default=3, ge=1, le=5)

    @field_validator("category", mode="before")
    @classmethod
    def coerce_category(cls, value: Any) -> SkillCategory:
        return normalize_skill_category(value)

    @field_validator("proficiency", mode="before")
    @classmethod
    def coerce_proficiency(cls, value: Any) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return 3
        return max(1, min(5, parsed))


class ResumeProfile(BaseModel):
    name: str | None = None
    headline: str | None = None
    skills: list[ResumeSkill] = Field(default_factory=list)
    experience: list[ExperienceItem] = Field(default_factory=list)
    education: list[EducationItem] = Field(default_factory=list)
    summary: str | None = None
    skill_summary: str | None = None
    insights: list[str] = Field(default_factory=list)

    @field_validator("skills", mode="before")
    @classmethod
    def coerce_skills(cls, value: Any) -> Any:
        if not isinstance(value, list):
            return value
        items: list[Any] = []
        for item in value:
            if isinstance(item, str):
                name = item.strip()
                if name:
                    items.append({"name": name})
            else:
                items.append(item)
        return items


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


class AnswerTable(BaseModel):
    headers: list[str] = Field(default_factory=list)
    rows: list[list[str]] = Field(default_factory=list)


class AnswerCode(BaseModel):
    language: str = ""
    content: str = ""


class GeneratedAnswer(BaseModel):
    text: str
    citations: list[Citation] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    table: AnswerTable | None = None
    code: AnswerCode | None = None


class InterviewTopicCandidate(BaseModel):
    label: str
    reason: str = ""


class InterviewTopicPlan(BaseModel):
    topics: list[InterviewTopicCandidate] = Field(default_factory=list)


class FaithfulnessResult(BaseModel):
    grounded: bool
    reason: str = ""


class RetrievedChunk(BaseModel):
    document_id: str
    filename: str
    content: str
    distance: float = 0.0
