from __future__ import annotations

from datetime import date
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from backend.api_schemas import UsageActivitiesOut, UsageSummaryOut
from backend.db import get_db
from backend.deps import get_user_id
from backend.models import UsageEvent
from backend.usage_service import (
    USAGE_RANGE_DAYS,
    list_usage_activities,
    resolve_activity_window,
    summarize_usage_events,
)

router = APIRouter(prefix="/v1/usage", tags=["usage"])

UsageRange = Literal["7d", "30d", "90d"]


def _user_events(db: Session, user_id: UUID) -> list:
    return db.exec(select(UsageEvent).where(UsageEvent.user_id == user_id)).all()


@router.get("", response_model=UsageSummaryOut)
def usage_summary(
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_user_id),
    range: UsageRange = Query(default="30d"),
) -> UsageSummaryOut:
    range_key = range if range in USAGE_RANGE_DAYS else "30d"
    return summarize_usage_events(_user_events(db, user_id), range_key=range_key)


@router.get("/activities", response_model=UsageActivitiesOut)
def usage_activities(
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_user_id),
    start: date | None = Query(default=None),
    end: date | None = Query(default=None),
) -> UsageActivitiesOut:
    start_date, end_date = resolve_activity_window(start, end)
    activities = list_usage_activities(_user_events(db, user_id), start=start_date, end=end_date)
    return UsageActivitiesOut(start=start_date.isoformat(), end=end_date.isoformat(), activities=activities)
