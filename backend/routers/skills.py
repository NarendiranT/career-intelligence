from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlmodel import Session

from backend.api_schemas import SkillsSummaryOut
from backend.db import get_db
from backend.deps import get_user_id
from backend.skills_service import summarize_user_skills

router = APIRouter(prefix="/v1/skills", tags=["skills"])


@router.get("", response_model=SkillsSummaryOut)
def skills_summary(
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_user_id),
) -> SkillsSummaryOut:
    return summarize_user_skills(db, user_id)
