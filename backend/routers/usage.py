from __future__ import annotations

from collections import defaultdict
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from backend.api_schemas import UsageByEventOut, UsageSummaryOut
from backend.db import get_db
from backend.deps import get_user_id
from backend.models import UsageEvent

router = APIRouter(prefix="/v1/usage", tags=["usage"])


@router.get("", response_model=UsageSummaryOut)
def usage_summary(
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_user_id),
) -> UsageSummaryOut:
    events = db.exec(select(UsageEvent).where(UsageEvent.user_id == user_id)).all()
    total_tokens = 0
    prompt_tokens = 0
    completion_tokens = 0
    by_type: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for event in events:
        tokens = int(event.tokens or 0)
        extra = event.extra or {}
        prompt = int(extra.get("input_tokens") or 0)
        completion = int(extra.get("output_tokens") or 0)
        total_tokens += tokens
        prompt_tokens += prompt
        completion_tokens += completion
        bucket = by_type[event.event_type]
        bucket[0] += tokens
        bucket[1] += 1
    return UsageSummaryOut(
        total_tokens=total_tokens,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        event_count=len(events),
        by_event_type=[
            UsageByEventOut(event_type=name, tokens=counts[0], count=counts[1])
            for name, counts in sorted(by_type.items())
        ],
    )
