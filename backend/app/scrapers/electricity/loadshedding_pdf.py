import re
from datetime import date

import pdfplumber
import httpx

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
