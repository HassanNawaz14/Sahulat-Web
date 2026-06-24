import re
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Optional

import pdfplumber
import httpx

from app.scrapers.common.feeder_area_map import lookup_area, default_city
from app.core.supabase import supabase

DISCO_PDF_URLS: dict[str, str] = {
    "lesco": "https://www.lesco.gov.pk:36269/Modules/LoadShedding/LoadSheddingSchedule.pdf",
}

WEEKDAYS = [
    "monday", "tuesday", "wednesday", "thursday",
    "friday", "saturday", "sunday",
]


class LoadSheddingEntry:
    def __init__(
        self,
        feeder_code: str,
        feeder_name: str,
        schedule_date: date,
        slots: list[dict],
    ):
        self.feeder_code = feeder_code
        self.feeder_name = feeder_name
        self.schedule_date = schedule_date
        self.slots = slots


@dataclass
class NormalizedOutageRow:
    provider_code: str
    city: str
    area_slug: str
    feeder_name: str
    feeder_code: str
    start_time: str
    end_time: str
    schedule_date: str
    outage_type: str = "scheduled"
    source_type: str = "pdf"
    confidence_score: float = 0.82
    area_tags: list[str] = field(default_factory=list)


async def parse_loadshedding_pdf(
    provider_code: str,
) -> list[LoadSheddingEntry]:
    url = DISCO_PDF_URLS.get(provider_code)
    if not url:
        return []

    async with httpx.AsyncClient(
        follow_redirects=True, verify=False, timeout=30
    ) as client:
        resp = await client.get(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Linux; Android 13) "
                    "AppleWebKit/537.36 Chrome/124.0 Mobile Safari/537.36"
                )
            },
        )
        resp.raise_for_status()

    entries: list[LoadSheddingEntry] = []
    with pdfplumber.open(resp.content) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for row in table[1:]:
                    if not row or not row[0]:
                        continue
                    feeder_code = _clean(row[0])
                    feeder_name = _clean(row[1]) if len(row) > 1 else ""
                    slots = _parse_slots(row[2:]) if len(row) > 2 else []
                    if feeder_code:
                        entries.append(
                            LoadSheddingEntry(
                                feeder_code=feeder_code,
                                feeder_name=feeder_name,
                                schedule_date=date.today(),
                                slots=slots,
                            )
                        )
    return entries


def normalize_schedule_row(
    entry: LoadSheddingEntry,
    provider_code: str,
    pdf_url: str = "",
    raw_text: str = "",
) -> list[NormalizedOutageRow]:
    """Convert a LoadSheddingEntry into one ore more NormalizedOutageRow objects.

    One row is generated per slot per day, with start_time/end_time as ISO datetime
    strings in PKT timezone (+05:00).
    """
    rows: list[NormalizedOutageRow] = []
    city = default_city(provider_code)
    area_tags = lookup_area(entry.feeder_name)

    for slot in entry.slots:
        day_name = slot.get("day", "").lower()
        start_str = slot.get("start", "")
        end_str = slot.get("end", "")

        if not start_str or not end_str:
            continue

        # Determine the date for this day slot
        slot_date = _resolve_slot_date(entry.schedule_date, day_name)

        # Parse time strings (e.g., "06:00" or "6:00 AM")
        start_iso = _time_to_iso(slot_date, start_str)
        end_iso = _time_to_iso(slot_date, end_str)

        if start_iso and end_iso:
            rows.append(NormalizedOutageRow(
                provider_code=provider_code,
                city=city,
                area_slug=area_tags[0] if area_tags else entry.feeder_name.lower().replace(" ", "-"),
                feeder_name=entry.feeder_name,
                feeder_code=entry.feeder_code,
                start_time=start_iso,
                end_time=end_iso,
                schedule_date=slot_date.isoformat(),
                outage_type="scheduled",
                source_type="pdf",
                confidence_score=0.82,
                area_tags=area_tags,
            ))

    return rows


def upsert_outage_schedules(
    rows: list[NormalizedOutageRow],
    source_url: str = "",
) -> int:
    """Upsert normalized outage rows into the outage_schedules table.

    Uses (provider_code, feeder_code, schedule_date) as the unique key.
    Returns the count of rows upserted.
    """
    count = 0
    for row in rows:
        # Build slots array from the time range
        slots_data = [{
            "start": row.start_time,
            "end": row.end_time,
        }]
        schedule_date_obj = date.fromisoformat(row.schedule_date)
        week_start = _get_week_start(schedule_date_obj)

        payload = {
            "provider_code": row.provider_code,
            "feeder_code": row.feeder_code,
            "feeder_name": row.feeder_name,
            "area_tags": row.area_tags,
            "city": row.city,
            "schedule_date": row.schedule_date,
            "slots": slots_data,
            "week_start": week_start.isoformat(),
            "source_pdf_url": source_url or None,
            "confidence_score": row.confidence_score,
            "source_url": source_url or None,
            "raw_text": f"{row.feeder_name} {row.start_time}-{row.end_time}",
        }

        supabase.table("outage_schedules").upsert(
            payload,
            on_conflict="provider_code, feeder_code, schedule_date",
        ).execute()
        count += 1

    return count


def _clean(val: str | None) -> str:
    return val.strip() if val else ""


def _parse_slots(cells: list[str | None]) -> list[dict]:
    slots = []
    for i, cell in enumerate(cells):
        time_range = _clean(cell)
        if time_range and "-" in time_range:
            parts = time_range.split("-", 1)
            slots.append({
                "day": WEEKDAYS[i] if i < len(WEEKDAYS) else f"day-{i}",
                "start": parts[0].strip(),
                "end": parts[1].strip(),
            })
    return slots


def _resolve_slot_date(base_date: date, day_name: str) -> date:
    """Given a base_date (monday of week) and a day_name, return the actual date."""
    if not day_name:
        return base_date
    day_name = day_name.strip().lower()
    day_map = {d: i for i, d in enumerate(WEEKDAYS)}
    target_dow = day_map.get(day_name, 0)
    base_dow = base_date.weekday()  # monday=0
    diff = target_dow - base_dow
    return base_date + timedelta(days=diff)


def _time_to_iso(slot_date: date, time_str: str) -> Optional[str]:
    """Parse a time string and return ISO datetime with PKT timezone."""
    time_str = time_str.strip().upper()
    # Handle formats like "6:00 AM", "06:00", "6AM"
    match = re.match(r"(\d{1,2}):?(\d{2})?\s*(AM|PM)?", time_str)
    if not match:
        return None

    hour = int(match.group(1))
    minute = int(match.group(2)) if match.group(2) else 0
    ampm = match.group(3)

    if ampm == "PM" and hour != 12:
        hour += 12
    elif ampm == "AM" and hour == 12:
        hour = 0

    if hour >= 24 or minute >= 60:
        return None

    dt = datetime(slot_date.year, slot_date.month, slot_date.day, hour, minute)
    return dt.isoformat() + "+05:00"


def _get_week_start(d: date) -> date:
    """Return the monday of the week containing d."""
    return d - timedelta(days=d.weekday())
