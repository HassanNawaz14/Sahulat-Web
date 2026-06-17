# P09 — Outage Tracker Module (M3)

**Document Type:** Rigid Plan  
**Status:** Authoritative  
**Depends On:** P02 (Tech Stack), P03 (Database Schema), P04 (Auth & User System), P05 (Scraper System), P19 (Notifications)  
**Required By:** P12 (Community Reports), P19 (Notifications), P20 (Frontend), P21 (API Spec)

---

## 1. Scope

The Outage Tracker combines scheduled electricity load shedding data with real-time crowd reports for electricity, gas, water, and internet outages. Scheduled outage data comes primarily from DISCO weekly PDFs. Unscheduled outages and gas/water/internet issues are crowd-sourced.

This module is a P0 retention driver. Users should check it before leaving home, before charging devices, and during an outage to see whether the issue is local or widespread.

---

## 2. User-Facing Features

| Feature | Priority | Description |
|---------|----------|-------------|
| Today/tomorrow schedule | P0 | Show scheduled load shedding for user's area/feeders |
| Countdown timer | P0 | "Power cut starts in 22 minutes" |
| Push warnings | P0 | Notify 15 minutes before scheduled outage |
| One-tap outage report | P0 | User reports electricity/gas/water/internet issue |
| Area outage map | P1 | Cluster reports by city/area |
| Report confidence score | P1 | Verified status based on volume, recency, and reputation |
| Feeder search | P1 | User can map their area to a feeder |
| WhatsApp share | P1 | Share today's schedule or active outage |
| Admin schedule correction | P1 | Admin can manually fix parsed schedule rows |

---

## 3. Data Sources

| Source | Utility | Reliability | Method |
|--------|---------|-------------|--------|
| DISCO weekly PDFs | Electricity | Medium-high | Download and parse with `pdfplumber` |
| DISCO websites/news | Electricity | Medium | HTML scrape |
| SNGPL/SSGC announcements | Gas | Low-medium | News scrape + manual admin entry |
| WASA/KW&SB notices | Water | Low | Manual admin entry + crowd reports |
| ISP outage data | Internet | Low | Crowd reports only |
| User reports | All | Improves with scale | Supabase insert + realtime feed |

---

## 4. Database Tables

Uses P03 tables:

- `outage_schedules`
- `community_outage_reports`
- `homes`
- `profiles`
- `notification_preferences`

Required additional fields if not already present in P03:

| Table | Field | Purpose |
|-------|-------|---------|
| `outage_schedules` | `confidence_score NUMERIC` | Parser/admin confidence from 0 to 1 |
| `outage_schedules` | `source_url TEXT` | PDF or notice URL |
| `outage_schedules` | `raw_text TEXT` | Extracted row text for debugging |
| `community_outage_reports` | `expires_at TIMESTAMPTZ` | Auto-hide stale reports |

---

## 5. PDF Parser Workflow

### 5.1 Job

**Job name:** `parse_loadshedding_schedules`  
**Schedule:** Every Monday at 09:00 PKT; retry daily at 09:30 if missing

```python
async def parse_loadshedding_schedules():
    for provider_code in ELECTRICITY_PROVIDERS:
        pdf_url = await discover_latest_schedule_pdf(provider_code)
        if not pdf_url:
            await log_scraper_run(provider_code, "loadshedding_pdf", "missing")
            continue

        pdf_bytes = await download_pdf(pdf_url)
        rows = parse_pdf_rows(pdf_bytes, provider_code)
        normalized = [normalize_schedule_row(row, provider_code) for row in rows]
        await upsert_outage_schedules(normalized, source_url=pdf_url)
```

### 5.2 Normalized Schedule Row

```json
{
  "provider_code": "lesco",
  "city": "lahore",
  "area_slug": "dha-phase-5",
  "feeder_name": "DHA R-BLOCK",
  "start_time": "2025-06-17T10:00:00+05:00",
  "end_time": "2025-06-17T11:00:00+05:00",
  "outage_type": "scheduled",
  "source_type": "pdf",
  "confidence_score": 0.82
}
```

### 5.3 Feeder Mapping

The parser will not always know the user's area. A static and admin-editable mapping must exist:

```
backend/app/scrapers/common/feeder_area_map.py
frontend/lib/constants/feederAreaMap.ts
```

When mapping is uncertain, the UI asks the user to select a feeder manually and stores it on the `homes` record as `feeder_name`.

---

## 6. Outage Screen

**Route:** `/outages`

Required sections:

1. Current status card: "No scheduled outage right now" or "Outage active until 11:00 AM"
2. Next scheduled outage card
3. Today timeline by hour
4. Report outage button group: Electricity, Gas, Water, Internet
5. Community reports near user's area
6. Map/list toggle for reports
7. Feeder selector if missing

---

## 7. Reporting Flow

### 7.1 One-Tap Report

1. User taps utility type.
2. App uses user's default home city/area.
3. Optional details sheet appears: severity, note, provider.
4. Backend inserts report with `status = active`, `expires_at = now() + interval '3 hours'`.
5. Supabase realtime broadcasts report to users in same city/area.

### 7.2 API

`POST /api/v1/outages/reports`

```json
{
  "utility_type": "electricity",
  "provider_code": "lesco",
  "home_id": "uuid",
  "severity": "full_outage",
  "note": "Power gone in whole street"
}
```

Response:
```json
{
  "id": "uuid",
  "status": "active",
  "confidence_score": 0.45,
  "expires_at": "2025-06-17T18:00:00Z"
}
```

---

## 8. Verification Rules

A crowd report becomes `verified` when at least one condition is true:

| Condition | Rule |
|-----------|------|
| Volume | 5+ reports in same area within 30 minutes |
| Cross-area | 10+ reports across adjacent areas within 45 minutes |
| Schedule match | Report overlaps an official scheduled outage |
| Trusted users | 3+ reports from users with high reputation |

Reports expire automatically after 3 hours unless renewed by new reports.

---

## 9. Notifications

P19 sends:

- 15-minute scheduled outage warning
- outage started notification
- outage restored notification if enough users mark restored
- high-confidence nearby outage alert

Users can disable each category separately.

---

## 10. Edge Cases

| Case | Required Behavior |
|------|-------------------|
| PDF layout changes | Mark parser failed, keep previous week's schedule visible with stale warning |
| User has no area | Show city-level schedule and prompt to complete profile |
| Duplicate reports | One active report per user per utility per home per 30 minutes |
| False reports | Rate-limit and reputation-score reports silently |
| Timezone | Store UTC; display PKT |

---

## 11. Acceptance Criteria

- LESCO schedule parsing works before public launch.
- User can report outages for all utility types.
- Nearby reports update in real time.
- Scheduled outage notifications are generated through P19.
- Parser failures are visible in admin logs, not as broken user screens.
