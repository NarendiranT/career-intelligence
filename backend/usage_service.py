from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from typing import Any

from agent.usage import _as_int, default_feature_details, feature_for_event
from backend.api_schemas import (
    UsageActivityOut,
    UsageByEventOut,
    UsageDailyOut,
    UsageFeatureOut,
    UsageSummaryOut,
)
from backend.models import UsageEvent

USAGE_RANGE_DAYS: dict[str, int] = {"7d": 7, "30d": 30, "90d": 90}

FEATURE_LABELS: dict[str, str] = {
    "chat": "Chat with Assistant",
    "interview": "Interview Preparation",
    "documents": "Document Processing",
}

RECENT_ACTIVITY_LIMIT = 5


def _aware(value: datetime | None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def event_feature(event: UsageEvent) -> str:
    extra = event.extra or {}
    feature = extra.get("feature")
    if feature in FEATURE_LABELS:
        return str(feature)
    channel = extra.get("channel")
    return feature_for_event(event_type=event.event_type, channel=str(channel) if channel else None)


def event_activity_id(event: UsageEvent) -> str:
    extra = event.extra or {}
    activity_id = extra.get("activity_id")
    if activity_id:
        return str(activity_id)
    return str(event.id)


def _window(range_key: str, *, now: datetime | None = None) -> tuple[date, date, date, date]:
    days = USAGE_RANGE_DAYS.get(range_key) or USAGE_RANGE_DAYS["30d"]
    end_date = _aware(now).date()
    start_date = end_date - timedelta(days=days - 1)
    previous_end = start_date - timedelta(days=1)
    previous_start = previous_end - timedelta(days=days - 1)
    return start_date, end_date, previous_start, previous_end


def _in_range(created_at: datetime | None, start: date, end: date) -> bool:
    return start <= _aware(created_at).date() <= end


def _activity_rows(events: list[UsageEvent]) -> list[dict[str, Any]]:
    grouped: dict[str, list[UsageEvent]] = defaultdict(list)
    for event in events:
        grouped[event_activity_id(event)].append(event)
    rows: list[dict[str, Any]] = []
    for activity_id, items in grouped.items():
        items_sorted = sorted(items, key=lambda item: _aware(item.created_at))
        latest = items_sorted[-1]
        extra = latest.extra or {}
        feature = event_feature(latest)
        details = str(extra.get("details") or "").strip() or default_feature_details(feature)
        tokens = sum(int(item.tokens or 0) for item in items)
        prompt = sum(_as_int((item.extra or {}).get("input_tokens")) for item in items)
        completion = sum(_as_int((item.extra or {}).get("output_tokens")) for item in items)
        rows.append(
            {
                "id": activity_id,
                "feature": feature,
                "tokens": tokens,
                "prompt_tokens": prompt,
                "completion_tokens": completion,
                "details": details,
                "created_at": _aware(latest.created_at),
            }
        )
    rows.sort(key=lambda row: row["created_at"], reverse=True)
    return rows


def _activity_out(row: dict[str, Any]) -> UsageActivityOut:
    return UsageActivityOut(
        id=row["id"],
        created_at=row["created_at"],
        feature=row["feature"],
        tokens=row["tokens"],
        details=row["details"],
    )


def resolve_activity_window(
    start: date | None = None,
    end: date | None = None,
    *,
    now: datetime | None = None,
) -> tuple[date, date]:
    today = _aware(now).date()
    end_date = end or today
    start_date = start or (end_date - timedelta(days=29))
    if start_date > end_date:
        start_date, end_date = end_date, start_date
    return start_date, end_date


def list_usage_activities(
    events: list[UsageEvent],
    *,
    start: date | None = None,
    end: date | None = None,
    now: datetime | None = None,
) -> list[UsageActivityOut]:
    start_date, end_date = resolve_activity_window(start, end, now=now)
    filtered = [event for event in events if _in_range(event.created_at, start_date, end_date)]
    return [_activity_out(row) for row in _activity_rows(filtered)]


def summarize_usage_events(
    events: list[UsageEvent],
    *,
    range_key: str = "30d",
    now: datetime | None = None,
) -> UsageSummaryOut:
    if range_key not in USAGE_RANGE_DAYS:
        range_key = "30d"
    start, end, previous_start, previous_end = _window(range_key, now=now)
    days = USAGE_RANGE_DAYS[range_key]

    total_tokens = 0
    prompt_tokens = 0
    completion_tokens = 0
    by_type: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    current_events: list[UsageEvent] = []
    previous_events: list[UsageEvent] = []

    for event in events:
        tokens = int(event.tokens or 0)
        extra = event.extra or {}
        prompt = _as_int(extra.get("input_tokens"))
        completion = _as_int(extra.get("output_tokens"))
        total_tokens += tokens
        prompt_tokens += prompt
        completion_tokens += completion
        bucket = by_type[event.event_type]
        bucket[0] += tokens
        bucket[1] += 1
        if _in_range(event.created_at, start, end):
            current_events.append(event)
        elif _in_range(event.created_at, previous_start, previous_end):
            previous_events.append(event)

    current_activities = _activity_rows(current_events)
    previous_activities = _activity_rows(previous_events)
    current_total = sum(row["tokens"] for row in current_activities)
    previous_total = sum(row["tokens"] for row in previous_activities)
    if previous_total:
        delta_percent = round(((current_total - previous_total) / previous_total) * 100)
    elif current_total:
        delta_percent = 100
    else:
        delta_percent = 0

    feature_tokens = {name: 0 for name in FEATURE_LABELS}
    feature_counts = {name: 0 for name in FEATURE_LABELS}
    for row in current_activities:
        feature_tokens[row["feature"]] += row["tokens"]
        feature_counts[row["feature"]] += 1

    features = []
    for name, label in FEATURE_LABELS.items():
        tokens = feature_tokens[name]
        percent = round((tokens / current_total) * 100) if current_total else 0
        features.append(
            UsageFeatureOut(
                id=name,
                label=label,
                tokens=tokens,
                percent=percent,
                activity_count=feature_counts[name],
            )
        )

    daily_map: dict[date, dict[str, int]] = {}
    cursor = start
    while cursor <= end:
        daily_map[cursor] = {name: 0 for name in FEATURE_LABELS}
        cursor += timedelta(days=1)
    for row in current_activities:
        day = row["created_at"].date()
        if day in daily_map:
            daily_map[day][row["feature"]] += row["tokens"]

    daily = [
        UsageDailyOut(date=day.isoformat(), chat=values["chat"], interview=values["interview"], documents=values["documents"])
        for day, values in sorted(daily_map.items())
    ]

    recent = [_activity_out(row) for row in current_activities[:RECENT_ACTIVITY_LIMIT]]

    return UsageSummaryOut(
        range=range_key,
        total_tokens=total_tokens,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        event_count=len(events),
        range_tokens=current_total,
        previous_range_tokens=previous_total,
        delta_percent=delta_percent,
        by_event_type=[
            UsageByEventOut(event_type=name, tokens=counts[0], count=counts[1])
            for name, counts in sorted(by_type.items())
        ],
        features=features,
        daily=daily,
        recent=recent,
        days=days,
    )