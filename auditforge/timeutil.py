"""Fixed-offset time helpers (no DST, no tzdata dependency => offline-safe)."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone


def tz_from_minutes(minutes: int) -> timezone:
    return timezone(timedelta(minutes=minutes))


def offset_label(minutes: int) -> str:
    sign = "+" if minutes >= 0 else "-"
    m = abs(minutes)
    return f"UTC{sign}{m // 60:02d}:{m % 60:02d}"


def parse_offset_label(label: str) -> int:
    assert label.startswith("UTC") and len(label) == 9, label
    sign = 1 if label[3] == "+" else -1
    return sign * (int(label[4:6]) * 60 + int(label[7:9]))


def parse_iso(s: str) -> datetime:
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        raise ValueError(f"naive timestamp not allowed: {s}")
    return dt


def to_iso(dt: datetime, offset_minutes: int) -> str:
    """Render instant `dt` with a given UTC offset (ISO-8601 with explicit offset)."""
    return dt.astimezone(tz_from_minutes(offset_minutes)).isoformat(timespec="seconds")


def local_date(dt: datetime, company_offset_minutes: int) -> date:
    return dt.astimezone(tz_from_minutes(company_offset_minutes)).date()


def side_of_period(dt: datetime, start: datetime, end: datetime) -> str:
    """Period is [start, end). Returns 'before' | 'in' | 'after'."""
    if dt < start:
        return "before"
    if dt >= end:
        return "after"
    return "in"
