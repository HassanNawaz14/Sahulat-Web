# P05 — Scraper System

**Document Type:** Rigid Plan
**Status:** Authoritative
**Depends On:** P02 (Tech Stack), P03 (Database Schema), P04 (Auth & User System)
**Required By:** P06 (Bill Tracker), P07 (Consumption Monitor), P09 (Outage Tracker), P14 (ISP Comparison)

---

## 1. Scope

This document defines every scraper in Sahulat: target URLs, request patterns, parsing logic, error handling, scheduling, and the standard interface every scraper must implement. This is the most fragile part of the system (third-party site dependent) and therefore has the strictest structural rules.

---

## 2. Scraper Module Structure

All scrapers live in a single backend package:

```
backend/
  app/
    scrapers/
      __init__.py
      base.py                    # BaseScraper abstract class
      registry.py                 # Maps provider_code → scraper class
      electricity/
        lesco.py
        kelectric.py
        gepco.py
        fesco.py
        mepco.py
        iesco.py
        pesco.py
        qesco.py
        hesco.py
        sepco.py
        loadshedding_pdf.py       # Shared PDF parser used by all DISCOs
      gas/
        sngpl.py
        ssgc.py
      water/
        wasa_lhr.py
        kwsb.py
      internet/
        ptcl.py
        nayatel.py
      common/
        http_client.py            # Shared httpx client with retry/backoff
        feeder_area_map.py         # Feeder name → area_slug lookup
    jobs/
      cron_definitions.py
      runner.py
```

---

## 3. Base Scraper Interface

Every scraper MUST inherit from this abstract class and implement exactly these two methods. This uniform interface is what allows `registry.py` to dispatch dynamically by `provider_code` without per-provider conditional logic anywhere else in the codebase.

```python
# backend/app/scrapers/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

@dataclass
class ScrapedBill:
    issue_date: Optional[str]       # ISO date string
    due_date: Optional[str]
    amount_payable: float
    units_consumed: Optional[float]
    previous_reading: Optional[float]
    current_reading: Optional[float]
    arrears: float = 0.0
    taxes: float = 0.0
    surcharges: float = 0.0
    meter_rent: float = 0.0
    fc_surcharge: float = 0.0
    tariff_slab: Optional[str] = None
    raw_data: dict = None

class BaseScraper(ABC):
    provider_code: str            # e.g. 'lesco'
    utility_type: str             # 'electricity' | 'gas' | 'water' | 'internet'
    consumer_number_pattern: str   # regex used to validate before scraping

    @abstractmethod
    async def fetch_bill(self, consumer_number: str) -> ScrapedBill:
        """Fetch the latest bill. Raises ScraperError subclasses on failure."""
        ...

    @abstractmethod
    def validate_consumer_number(self, consumer_number: str) -> bool:
        """Regex validation against consumer_number_pattern before any network call."""
        ...
```

### 3.1 Exception Hierarchy

```python
# backend/app/scrapers/base.py (continued)
class ScraperError(Exception): ...
class InvalidConsumerNumberError(ScraperError): ...
class PortalUnreachableError(ScraperError): ...
class ParsingFailedError(ScraperError): ...
class CaptchaDetectedError(ScraperError): ...
class NoBillFoundError(ScraperError): ...
```

Every scraper call site (API route in P06) catches these specifically and maps to a structured API error response — never a raw 500.

---

## 4. Shared HTTP Client

All scrapers use one shared `httpx.AsyncClient` configuration to enforce ethical scraping rules (P02 §5.3) uniformly:

```python
# backend/app/scrapers/common/http_client.py
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Mobile Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

def get_client(timeout: float = 15.0) -> httpx.AsyncClient:
    return httpx.AsyncClient(headers=DEFAULT_HEADERS, timeout=timeout, follow_redirects=True)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=2, max=10))
async def fetch_with_retry(client: httpx.AsyncClient, method: str, url: str, **kwargs) -> httpx.Response:
    resp = await client.request(method, url, **kwargs)
    resp.raise_for_status()
    return resp
```

**Mandatory delay:** Every scraper inserts `await asyncio.sleep(random.uniform(2, 5))` before each request when running in a batch job (e.g., re-fetching all users' bills) — never in tight loops. Single on-demand fetches (user clicks "Refresh Bill") are not delayed since they are one-off.

---

## 5. Electricity Scrapers

### 5.1 LESCO (`lesco.py`) — V1 Priority Provider

| Property | Value |
|----------|-------|
| Portal URL | `https://bill.lesco.gov.pk/` (bill check form) |
| Method | `POST` form submission with `RefNo` field |
| Response format | HTML table |
| Consumer number pattern | `^\d{2}-\d{5}-\d{7}-[A-Z]$` (LESCO reference format) |

**Parsing logic:**
1. POST the reference number to the bill check endpoint.
2. Parse returned HTML with BeautifulSoup4 — locate the bill details table by its known CSS class/ID (determined during implementation via manual inspection; documented in code comments with a snapshot date since DISCO sites redesign without notice).
3. Extract fields: issue date, due date, amount payable, units consumed, previous/current reading, arrears, FC surcharge, taxes.
4. If the table is not found (`ParsingFailedError`), the run is logged and a Slack/email alert fires (see §10) — DISCO sites change layout periodically and this must be caught fast, not silently fail.

### 5.2 K-Electric (`kelectric.py`) — V1 Priority Provider

| Property | Value |
|----------|-------|
| Portal URL | `https://www.ke.com.pk/billcalculator/` or equivalent public bill-check page |
| Method | `POST` |
| Consumer number pattern | `^\d{10,12}$` |

Same parsing pattern as LESCO — implementation differs only in field selectors and consumer number regex.

### 5.3 Remaining DISCOs (GEPCO, FESCO, MEPCO, IESCO, PESCO, QESCO, HESCO, SEPCO) — V2

Each gets its own file following the identical `BaseScraper` interface. **Not built in V1.** Placeholder stub files raise `NotImplementedError` and are registered in `registry.py` with a `coming_soon: true` flag so the frontend can show "Coming soon for [DISCO]" instead of a broken "Add Utility" option (see P06 §4.2).

### 5.4 Load Shedding PDF Parser (`loadshedding_pdf.py`) — Shared Across All DISCOs

Used by the weekly cron job `fetch_loadshedding_pdfs` (P02 §3.3).

**Process:**
1. For each DISCO with a known PDF URL pattern (maintained in a static dict, since URLs follow a predictable weekly naming convention for most DISCOs, e.g. `lesco.gov.pk/loadshedding/week-{date}.pdf`), download the PDF via `httpx`.
2. Parse with `pdfplumber` — extract tables. LESCO PDFs (highest priority, most consistent) have one row per feeder with columns: Feeder Code, Feeder Name, Day-wise time slots.
3. For each row, map `feeder_name` → `area_tags` using `feeder_area_map.py` — a static, manually curated lookup built once and refined as user feedback identifies wrong mappings (admin-editable lookup, stored as a JSON file in V1, migrated to a `feeder_area_mappings` DB table if it grows past ~200 entries).
4. Upsert into `outage_schedules` table (P03 §6.1) — one row per `(provider_code, feeder_code, schedule_date)`.
5. If PDF download fails or table extraction returns zero rows, log to `scraper_run_log` (see §9) with status `failed` and do **not** overwrite existing schedule data — stale-but-present data is better than wiped data.

---

## 6. Gas Scrapers

### 6.1 SNGPL (`sngpl.py`)

| Property | Value |
|----------|-------|
| Portal URL | `https://www.sngpl.com.pk/web/billing-system/` (or current bill inquiry endpoint) |
| Method | `GET`/`POST` by consumer number |
| Consumer number pattern | `^\d{10}$` |

### 6.2 SSGC (`ssgc.py`)

| Property | Value |
|----------|-------|
| Portal URL | `https://www.ssgc.com.pk/SSGCWEB/billing` (or current equivalent) |
| Method | `POST` |
| Consumer number pattern | `^\d{9,11}$` |

Both follow the identical `BaseScraper` pattern. Gas load-management schedules (winter pressure reduction announcements) are **not** scraped automatically in V1 — they are non-machine-readable per P01 §7 and handled via manual admin entry into `outage_schedules` with `provider_code = 'sngpl'`/`'ssgc'` and a simplified `slots` JSON, supplemented by crowd-sourced reports (P12).

---

## 7. Water Scrapers (V1: WASA Lahore + KW&SB Only)

### 7.1 WASA Lahore (`wasa_lhr.py`)

| Property | Value |
|----------|-------|
| Portal URL | `https://wasa.punjab.gov.pk` bill inquiry page |
| Method | `POST` |
| Consumer number pattern | `^\d{8,12}$` |

### 7.2 KW&SB (`kwsb.py`)

| Property | Value |
|----------|-------|
| Portal URL | `https://kwsb.gos.pk` (or current domain) bill inquiry |
| Method | `POST` |
| Consumer number pattern | `^\d{8,12}$` |

Other WASA cities (Rawalpindi, Faisalabad, Multan) are V2 — stub registered as `coming_soon`.

---

## 8. Internet Scrapers (V1: PTCL + Nayatel — Public Portals Only)

PTCL and Nayatel offer public bill lookup without login. StormFiber, Jazz Home, and Zong Home require **stored user credentials** (encrypted, per P02 §5.2) and are deferred to V2 since credential-based scraping carries higher legal/ethical sensitivity and requires Playwright (session login) rather than simple form POST.

### 8.1 PTCL (`ptcl.py`)

| Property | Value |
|----------|-------|
| Portal URL | `https://ptcl.com.pk/customer/publicbill_payment` |
| Method | `POST` (ASP.NET ViewState, dynamic field extraction via BeautifulSoup) |
| Consumer number pattern | `^\d{11}$` (04X + 8 digits, e.g. `04212345678`) |
| Scraper approach | GET form → extract all ASP.NET fields dynamically → detect phone input + area code dropdown → POST with extracted ViewState → parse HTML or PDF response |

**Key details:**
- Phone number `04212345678` is split: area code `042`, local number `12345678`
- The area code dropdown is detected by finding a `<select>` whose `<option>` values are 2–4 digit numbers matching the area code
- The phone input is detected by finding a `<input type="text">` whose `name` attribute contains "phone", "txtphone", or "mobile"; if none found, falls back to the first visible text input
- No Account ID required — the public bill inquiry accepts phone-only search
- Falls back to PDF parsing (pdfplumber) if the response is `application/pdf`
- If the response HTML still contains the search form (`_is_search_form` check), raises `NoBillFoundError` with the error message extracted from the page
- Logs all form field names and response status for debugging

**Imperfect detection (known limitation):** Since `ptcl.com.pk` blocks non-Pakistan IPs, field name heuristics cannot be verified. If the portal changes its HTML structure, the heuristics may select the wrong fields. Debug logs (`logger.info`) output the actual form field names found on each request — check backend logs to diagnose. If the scraper stops working, retarget to the fallback DBill portal at `https://dbill.ptcl.net.pk/PTCLSearchInvoice.aspx` (requires Account ID + phone number).

**PTCL no-bill false positive fix (2026-06-22):** PTCL result pages can still include generic portal text like "phone number" and "public bill" even when bill data is present. The scraper now prefers explicit bill markers and explicit no-record messages, and only falls back to search-form detection when no bill content is present. This prevents real bills from being downgraded to `NoBillFoundError`.

**PTCL Account ID support (2026-06-22):** The official PTCL bill inquiry page also exposes an `Account ID` field for the landline flow. Sahulat persists it as an optional provider-specific reference and includes it in the PTCL payload when available, but the normal landline flow must continue to work without it.

**PTCL paid-bill payload handling (2026-06-22):** PTCL may return the bill markup inside a JSON envelope rather than as raw HTML. The scraper now unwraps `message` when the payload is JSON and also records the `Status` field so paid bills with `Total Due Amount = 0` still count as valid bill data instead of falling through to `ParsingFailedError`.

### 8.2 Nayatel (`nayatel.py`)

| Property | Value |
|----------|-------|
| Portal URL | `https://nayatel.com` self-care bill inquiry |
| Method | `POST` |
| Consumer number pattern | `^[A-Z0-9]{6,12}$` |

---

## 9. Scraper Run Logging

A dedicated table (additive migration to P03's schema, owned by this document since it's scraper infrastructure rather than user-facing data):

```sql
CREATE TABLE public.scraper_run_log (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  provider_code   TEXT NOT NULL,
  job_type        TEXT NOT NULL,           -- 'bill_fetch' | 'loadshedding_pdf' | 'isp_packages'
  status          TEXT NOT NULL,           -- 'success' | 'failed' | 'partial'
  target_id       TEXT,                    -- consumer_account_id or batch identifier
  error_message   TEXT,
  duration_ms     INTEGER,
  run_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_scraper_log_provider_time ON scraper_run_log(provider_code, run_at DESC);
```

No RLS — internal/admin table only, never exposed via a public API route (only via `/api/v1/admin/scraper-logs`, protected by `get_admin_user`, P04 §7.2).

---

## 10. Failure Alerting

When `scraper_run_log.status = 'failed'` for the **same `provider_code` + `job_type`** three times in a row, the `runner.py` job dispatcher sends an alert via a simple webhook POST to a configured `ADMIN_ALERT_WEBHOOK_URL` (Slack incoming webhook or Discord webhook — admin's choice, configured as an env var). This is the only automated alerting in V1; no dedicated monitoring service (e.g., Sentry) is provisioned until Phase 6 (post-launch scale, per P01 §10).

---

## 11. Registry Dispatch Pattern

```python
# backend/app/scrapers/registry.py
from .electricity.lesco import LescoScraper
from .electricity.kelectric import KElectricScraper
from .gas.sngpl import SngplScraper
from .gas.ssgc import SsgcScraper
from .water.wasa_lhr import WasaLahoreScraper
from .water.kwsb import KwsbScraper
from .internet.ptcl import PtclScraper
from .internet.nayatel import NayatelScraper

SCRAPER_REGISTRY = {
    "lesco": LescoScraper(),
    "kelectric": KElectricScraper(),
    "sngpl": SngplScraper(),
    "ssgc": SsgcScraper(),
    "wasa_lhr": WasaLahoreScraper(),
    "kwsb": KwsbScraper(),
    "ptcl": PtclScraper(),
    "nayatel": NayatelScraper(),
    # Remaining DISCOs/ISPs registered as coming_soon stubs — see COMING_SOON set below
}

COMING_SOON = {"gepco", "fesco", "mepco", "iesco", "pesco", "qesco", "hesco", "sepco",
                "wasa_rwp", "stormfiber", "jazz_home", "zong_home"}

def get_scraper(provider_code: str):
    if provider_code in COMING_SOON:
        raise NotImplementedError(f"{provider_code} support coming soon")
    scraper = SCRAPER_REGISTRY.get(provider_code)
    if not scraper:
        raise ValueError(f"Unknown provider_code: {provider_code}")
    return scraper
```

This registry is the single point consumed by the Bill Tracker module (P06) and the manual "Refresh Bill" endpoint — no other module ever imports a provider-specific scraper file directly.

---

## 12. Rate Limiting & Concurrency Rules

- Batch jobs (re-fetch all active consumer accounts) process **sequentially per provider**, not concurrently, to respect the 1-request-per-3-seconds rule (P02 §5.3). Different providers may run concurrently with each other (e.g., LESCO batch and SNGPL batch run in parallel asyncio tasks).
- Maximum batch size per cron run: 200 consumer accounts per provider. If more exist, the job paginates across multiple cron ticks rather than risk a single run exceeding Railway's execution time limits.
- On-demand single fetches (user-triggered) bypass the batch queue and execute immediately, but still go through the shared rate-limited HTTP client.
