from __future__ import annotations

from typing import Any

from sqlmodel import Session, select

from agent.schemas import SKILL_CATEGORIES
from backend.api_schemas import SkillActivityOut, SkillCategoryOut, SkillItemOut, SkillsSummaryOut
from backend.models import Document, DocumentStatus, DocType, ResumeProfile

OTHER_CATEGORY = "Other Skills"
INSIGHT_LIMIT = 5
ACTIVITY_LIMIT = 8


def _normalize_skill(item: Any) -> tuple[str, str, int] | None:
    if isinstance(item, str):
        name = item.strip()
        if not name:
            return None
        return name, OTHER_CATEGORY, 3
    if not isinstance(item, dict):
        return None
    name = str(item.get("name") or "").strip()
    if not name:
        return None
    category = str(item.get("category") or OTHER_CATEGORY)
    if category not in SKILL_CATEGORIES:
        category = OTHER_CATEGORY
    try:
        proficiency = int(item.get("proficiency") or 3)
    except (TypeError, ValueError):
        proficiency = 3
    return name, category, max(1, min(5, proficiency))


def _prefer_category(current: str, incoming: str) -> str:
    if current == OTHER_CATEGORY and incoming != OTHER_CATEGORY:
        return incoming
    return current


def _fallback_summary(categories: list[SkillCategoryOut], total: int) -> str:
    if total == 0:
        return "Upload a resume to see your skill profile."
    top = categories[0].name if categories else OTHER_CATEGORY
    if len(categories) == 1:
        return f"You have {total} skills in {top}."
    return (
        f"You have {total} skills across {len(categories)} categories, "
        f"with the strongest set in {top}."
    )


def merge_resume_skills(profiles: list[ResumeProfile]) -> tuple[list[SkillCategoryOut], list[str], str | None]:
    merged: dict[str, tuple[str, str, int]] = {}
    ranked = sorted(
        profiles,
        key=lambda row: (
            len(row.skills or []),
            1 if str((row.payload or {}).get("skill_summary") or "").strip() else 0,
        ),
        reverse=True,
    )
    insights: list[str] = []
    skill_summary: str | None = None

    for row in ranked:
        payload = row.payload or {}
        if skill_summary is None:
            text = str(payload.get("skill_summary") or "").strip() or str(payload.get("summary") or "").strip()
            if text:
                skill_summary = text
        for raw in payload.get("insights") or []:
            text = str(raw).strip()
            if text and text not in insights and len(insights) < INSIGHT_LIMIT:
                insights.append(text)
        source = row.skills if row.skills else payload.get("skills") or []
        for item in source:
            parsed = _normalize_skill(item)
            if parsed is None:
                continue
            name, category, proficiency = parsed
            key = name.casefold()
            if key not in merged:
                merged[key] = (name, category, proficiency)
                continue
            existing_name, existing_category, existing_level = merged[key]
            merged[key] = (
                existing_name,
                _prefer_category(existing_category, category),
                max(existing_level, proficiency),
            )

    grouped: dict[str, list[SkillItemOut]] = {name: [] for name in SKILL_CATEGORIES}
    for name, category, proficiency in merged.values():
        grouped.setdefault(category, []).append(SkillItemOut(name=name, proficiency=proficiency))

    categories: list[SkillCategoryOut] = []
    for category in SKILL_CATEGORIES:
        skills = sorted(grouped.get(category) or [], key=lambda item: (-item.proficiency, item.name.casefold()))
        if skills:
            categories.append(SkillCategoryOut(name=category, skills=skills))
    return categories, insights, skill_summary


def recent_skill_activity(documents: list[Document]) -> list[SkillActivityOut]:
    items: list[SkillActivityOut] = []
    for doc in documents:
        created = doc.created_at
        if doc.doc_type == DocType.resume:
            items.append(
                SkillActivityOut(
                    kind="resume_uploaded",
                    label="Resume Uploaded",
                    detail=doc.filename,
                    created_at=created,
                )
            )
            if doc.status == DocumentStatus.processed:
                items.append(
                    SkillActivityOut(
                        kind="analysis_completed",
                        label="AI Analysis Completed",
                        detail=doc.filename,
                        created_at=created,
                    )
                )
        elif doc.doc_type == DocType.job:
            items.append(
                SkillActivityOut(
                    kind="job_uploaded",
                    label="Job Description Uploaded",
                    detail=doc.filename,
                    created_at=created,
                )
            )
        if len(items) >= ACTIVITY_LIMIT:
            break
    return items[:ACTIVITY_LIMIT]


def summarize_user_skills(db: Session, user_id) -> SkillsSummaryOut:
    profiles = db.exec(select(ResumeProfile).where(ResumeProfile.user_id == user_id)).all()
    documents = db.exec(
        select(Document).where(Document.user_id == user_id).order_by(Document.created_at.desc())
    ).all()
    categories, insights, skill_summary = merge_resume_skills(list(profiles))
    total = sum(len(group.skills) for group in categories)
    return SkillsSummaryOut(
        resume_count=len(profiles),
        total_skills=total,
        skill_summary=skill_summary or _fallback_summary(categories, total),
        insights=insights,
        categories=categories,
        recent_activity=recent_skill_activity(list(documents)),
    )
