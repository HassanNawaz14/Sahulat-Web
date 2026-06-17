# P06 — Bill Tracker Module (M1)

**Document Type:** Rigid Plan  
**Status:** Authoritative  
**Depends On:** P02 (Tech Stack), P03 (Database Schema), P04 (Auth & User System), P05 (Scraper System)  
**Required By:** P07 (Consumption Monitor), P08 (Bill Estimator), P10 (Budget Manager), P19 (Notifications), P21 (API Spec)

---

## 1. Scope

The Bill Tracker is the **core P0 module** of Sahulat. It enables users to add consumer accounts (electricity, gas, water, internet), fetch their latest bills from utility portals, view bill history with trend graphs, mark bills as paid, and receive due-date alerts. Every other module either feeds into or reads from the bill data layer established here.

---

## 2. User-Facing Features

| Feature | Priority | Description |
|---------|----------|-------------|
| Add consumer account | P0 | Validate + store consumer number with provider |
| Fetch latest bill | P0 | On-demand scrape from utility portal |
| Auto-refresh bills | P0 | Background cron refreshes all bills daily |
| Bill history (6 months) | P0 | Chart of monthly bill amounts |
| Bill detail view | P0 | Full breakdown: units, slabs, arrears, taxes |
| Mark as paid | P1 | Manual status update; auto-detect via next bill's arrears = 0 |
| Bill due date countdown | P1 | "Due in 3 days" badge on dashboard |
| Multi-utility dashboard | P0 | All utilities in one card grid view |
| WhatsApp share | P1 | Share bill summary as formatted text |
| Bill export (PDF) | P2 | Premium feature — download bill history as PDF |

---

## 3. Consumer Account Management

### 3.1 Add Consumer Account Flow

**Frontend route:** `/settings` → "Add Utility" button → modal

**Step-by-step:**
1. User selects utility type (Electricity / Gas / Water / Internet) — tab selector
2. Based on type, show provider dropdown — only V1-supported providers shown; others marked "Coming Soon"
3. User enters consumer number — input mask applied per provider format (from `P04 §5.1` DISCO map)
4. Client-side regex validation against `consumer_number_pattern` (pulled from a static `consumerNumberPatterns` map in `frontend/lib/constants/consumerPatterns.ts`)
5. If valid format: POST `/api/v1/consumer-accounts` → backend validates again (Pydantic), inserts row, immediately triggers `fetch_bill` for the new account
6. Return bill data (or `NoBillFoundError` if no bill currently pending) to show instant result
7. Account card appears on dashboard

**Provider dropdown options by utility type (V1 only — others show "Coming Soon" badge):**

| Type | V1 Options | V2+ (Coming Soon) |
|------|-----------|------------------|
| Electricity | LESCO, K-Electric | GEPCO, FESCO, MEPCO, IESCO, PESCO, QESCO, HESCO, SEPCO |
| Gas | SNGPL, SSGC | — |
| Water | WASA Lahore, KW&SB | WASA Rawalpindi, WASA Faisalabad |
| Internet | PTCL, Nayatel | StormFiber, Jazz Home, Zong Home |

### 3.2 Consumer Account Card (Dashboard)

Each linked consumer account renders as a card on the main dashboard:

```
┌──────────────────────────────────────────────┐
│ ⚡ LESCO — Main Meter            [Refresh ↺] │
│                                               │
│  Rs. 4,280            Due: 3 days             │
│  ████████░░░░  6-month sparkline              │
│                                               │
│  Units: 312 kWh   Slab: 301–400              │
│  [View Details]  [Mark Paid]  [Share]         │
└──────────────────────────────────────────────┘
```

**Card data pulled from:**
- `consumer_accounts` — label, provider, type
- `bills` (latest row by `billing_month`) — amount, due date, units, slab
- `bills` (last 6 rows) — sparkline data

### 3.3 Consumer Account Limits (Free Tier)

Per P04 §7.3: max 10 consumer accounts on free tier (across all utility types). Enforced at `POST /api/v1/consumer-accounts`. Premium removes cap.

---

## 4. Bill Fetch Logic

### 4.1 On-Demand Fetch (User Clicks "Refresh")

**Endpoint:** `POST /api/v1/bills/fetch/{consumer_account_id}`

```python
@router.post("/bills/fetch/{consumer_account_id}")
async def fetch_bill(
    consumer_account_id: UUID,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    # 1. Verify ownership
    account = await db.fetch_one(
        "SELECT * FROM consumer_accounts WHERE id = :id AND user_id = :uid",
        {"id": consumer_account_id, "uid": current_user["user_id"]}
    )
    if not account:
        raise HTTPException(404, "Consumer account not found")

    # 2. Dispatch to scraper registry
    scraper = get_scraper(account["provider_code"])

    # 3. Fetch
    try:
        bill_data = await scraper.fetch_bill(decrypt(account["consumer_number"]))
    except InvalidConsumerNumberError:
        raise HTTPException(422, "Invalid consumer number format")
    except PortalUnreachableError:
        raise HTTPException(503, "Utility portal temporarily unavailable")
    except NoBillFoundError:
        return {"status": "no_bill", "message": "No pending bill found"}
    except ParsingFailedError:
        raise HTTPException(502, "Bill data parsing failed — portal may have changed")
    except CaptchaDetectedError:
        raise HTTPException(503, "Captcha detected — manual check required")

    # 4. Upsert bill record
    billing_month = parse_billing_month(bill_data.issue_date)
    await db.execute("""
        INSERT INTO bills (consumer_account_id, user_id, billing_month, issue_date, due_date,
            amount_payable, units_consumed, previous_reading, current_reading,
            arrears, taxes, surcharges, meter_rent, fc_surcharge, tariff_slab, raw_data)
        VALUES (:ca_id, :uid, :month, :issue, :due, :amount, :units, :prev, :curr,
            :arrears, :taxes, :surcharges, :meter_rent, :fc, :slab, :raw)
        ON CONFLICT (consumer_account_id, billing_month) DO UPDATE SET
            amount_payable = EXCLUDED.amount_payable,
            due_date = EXCLUDED.due_date,
            units_consumed = EXCLUDED.units_consumed,
            raw_data = EXCLUDED.raw_data,
            updated_at = NOW()
    """, {...})

    # 5. Update last_fetched_at
    await db.execute(
        "UPDATE consumer_accounts SET last_fetched_at = NOW() WHERE id = :id",
        {"id": consumer_account_id}
    )

    # 6. Return full bill response
    return format_bill_response(bill_data, account)
```

### 4.2 Background Auto-Refresh (Daily Cron)

**Job name:** `refresh_all_bills`  
**Schedule:** Daily at 07:00 PKT (02:00 UTC)

```python
# backend/app/jobs/cron_definitions.py

async def refresh_all_bills():
    """Re-fetch latest bill for every active consumer account."""
    accounts = await db.fetch_all(
        "SELECT * FROM consumer_accounts WHERE is_active = TRUE ORDER BY provider_code"
    )

    # Group by provider to respect per-provider sequential processing (P05 §12)
    by_provider = group_by(accounts, key="provider_code")

    async def process_provider(provider_code, provider_accounts):
        scraper = get_scraper(provider_code)
        for account in provider_accounts:
            try:
                bill_data = await scraper.fetch_bill(decrypt(account["consumer_number"]))
                await upsert_bill(account, bill_data)
                await asyncio.sleep(random.uniform(2, 5))  # Ethical delay (P05 §4)
            except Exception as e:
                await log_scraper_run(provider_code, "bill_fetch", "failed", str(account["id"]), str(e))

    # Run providers concurrently, accounts within each provider sequentially
    await asyncio.gather(*[
        process_provider(pc, accs) for pc, accs in by_provider.items()
    ])
```

**Batch size cap:** 200 accounts per provider per cron run (P05 §12). Pagination via `OFFSET` if more exist.

### 4.3 Billing Month Detection

The `billing_month` field is derived from the bill's `issue_date`. Since DISCO bills can have inconsistent formats:

```python
def parse_billing_month(issue_date_str: Optional[str]) -> date:
    """Return first day of the billing month from issue_date."""
    if not issue_date_str:
        return date.today().replace(day=1)
    try:
        d = datetime.strptime(issue_date_str, "%d-%m-%Y").date()
    except ValueError:
        d = datetime.strptime(issue_date_str, "%Y-%m-%d").date()
    return d.replace(day=1)
```

---

## 5. Bill Detail View

**Frontend route:** `/bills/[consumerAccountId]`

### 5.1 Layout

```
┌─────────────────────────────────────────────────────┐
│ ← Back     LESCO — Main Meter          [Share] [⋮] │
├─────────────────────────────────────────────────────┤
│          JUNE 2025 BILL                             │
│                                                     │
│  Amount Due          Rs. 4,280                      │
│  Due Date            15 Jul 2025   [3 days left]    │
│  Status              UNPAID  →  [Mark as Paid]      │
├─────────────────────────────────────────────────────┤
│ CONSUMPTION BREAKDOWN                               │
│  Current Reading     2,145 kWh                      │
│  Previous Reading    1,833 kWh                      │
│  Units Consumed      312 kWh                        │
│  Tariff Slab         301–400 units                  │
├─────────────────────────────────────────────────────┤
│ CHARGES BREAKDOWN                                   │
│  Energy charges      Rs. 3,420                      │
│  Fuel Cost Adj.      Rs. 387                        │
│  Taxes               Rs. 351                        │
│  Meter Rent          Rs. 35                         │
│  Arrears             Rs. 87                         │
│  ─────────────────────────────                      │
│  Total Payable       Rs. 4,280                      │
├─────────────────────────────────────────────────────┤
│ 6-MONTH TREND                                       │
│  [Bar chart: Jan–Jun monthly amounts]               │
├─────────────────────────────────────────────────────┤
│ QUICK ACTIONS                                       │
│  [Pay via JazzCash]  [File Complaint]  [Estimate]   │
└─────────────────────────────────────────────────────┘
```

### 5.2 "Pay via JazzCash" Deep Link

Not actual payment processing. Constructs a deep link:

```typescript
// frontend/lib/utils/paymentDeepLink.ts
export function buildJazzCashDeepLink(consumerNumber: string, amount: number): string {
  // JazzCash supports pre-filled bill payment via deep link
  return `jazzcash://pay?type=utility&consumer=${encodeURIComponent(consumerNumber)}&amount=${amount}`;
}

export function buildEasypaisaDeepLink(consumerNumber: string): string {
  return `easypaisa://billpayment?ref=${encodeURIComponent(consumerNumber)}`;
}
```

Both links shown as buttons. If app not installed, falls back to web URLs for JazzCash/Easypaisa web portal pre-filled with consumer number.

### 5.3 Bill History API

**Endpoint:** `GET /api/v1/bills/{consumer_account_id}/history?months=6`

Returns last N months of bills for the given consumer account. Used to populate the trend chart.

Response shape:
```json
{
  "consumer_account_id": "uuid",
  "history": [
    {
      "billing_month": "2025-06-01",
      "amount_payable": 4280.00,
      "units_consumed": 312,
      "status": "unpaid"
    },
    ...
  ]
}
```

---

## 6. Dashboard — Unified Bill View

**Frontend route:** `/dashboard`

### 6.1 Empty State (No Consumer Accounts)

Shown when `consumer_accounts` count = 0:

```
┌──────────────────────────────────────┐
│  🏠 Welcome to Sahulat!             │
│                                     │
│  Add your first utility to start    │
│  tracking bills and outages.        │
│                                     │
│  [+ Add Electricity Bill]           │
│  [+ Add Gas Bill]                   │
│  [+ Add Water Bill]                 │
│  [+ Add Internet Bill]              │
└──────────────────────────────────────┘
```

### 6.2 Populated Dashboard

All consumer account cards rendered in a vertical list, grouped by utility type. Order: Electricity → Gas → Water → Internet. Within each type, default home's accounts first.

**Total monthly spend summary card** (top of dashboard):
```
┌──────────────────────────────────────────┐
│  This Month's Utilities    Rs. 11,430    │
│  ⚡ Rs. 4,280  🔥 Rs. 3,150  💧 Rs. 820  │
│                             🌐 Rs. 3,180  │
│  [+12% vs last month]                    │
└──────────────────────────────────────────┘
```

### 6.3 Coming Soon Card

For V2 providers (e.g., GEPCO), if a user from Gujranwala is detected (via `profiles.city`):

```
┌──────────────────────────────────────────┐
│  ⚡ GEPCO Support — Coming Soon         │
│  We're working on GEPCO bill tracking.   │
│  [Notify me when available]              │
└──────────────────────────────────────────┘
```

"Notify me" stores a `coming_soon_signups` table entry (provider_code, user_id) — used to send push notification when that provider goes live.

---

## 7. Mark as Paid

**Endpoint:** `PATCH /api/v1/bills/{bill_id}/status`

Request body: `{ "status": "paid" }`

Rules:
- Only the bill owner can update status (RLS + user_id check in handler)
- Auto-override: if next month's scrape shows `arrears = 0`, the previous bill status is auto-set to `paid` in the upsert logic
- Status options: `unpaid` | `paid` | `overdue`
- A bill becomes `overdue` automatically when `due_date < TODAY()` and `status = 'unpaid'` — checked in the daily `refresh_all_bills` job

---

## 8. WhatsApp Share

**Trigger:** "Share" button on bill card or detail view

Constructs a pre-formatted WhatsApp message:

```typescript
export function buildWhatsAppShareText(bill: Bill, account: ConsumerAccount): string {
  return encodeURIComponent(
    `📋 *Sahulat Bill Summary*\n` +
    `Utility: ${account.provider_code.toUpperCase()} (${account.account_label})\n` +
    `Month: ${formatMonth(bill.billing_month)}\n` +
    `Amount: Rs. ${bill.amount_payable.toLocaleString()}\n` +
    `Due Date: ${formatDate(bill.due_date)}\n` +
    `Units: ${bill.units_consumed} kWh\n\n` +
    `Track your bills on Sahulat: https://sahulat.pk`
  );
}

// Opens: https://wa.me/?text=...
```

---

## 9. API Endpoints Summary

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/consumer-accounts` | List all user's consumer accounts | Yes |
| POST | `/api/v1/consumer-accounts` | Add new consumer account | Yes |
| PATCH | `/api/v1/consumer-accounts/{id}` | Update label, home assignment | Yes |
| DELETE | `/api/v1/consumer-accounts/{id}` | Deactivate account (soft delete) | Yes |
| POST | `/api/v1/bills/fetch/{consumer_account_id}` | On-demand bill fetch | Yes |
| GET | `/api/v1/bills/{consumer_account_id}/latest` | Get latest bill | Yes |
| GET | `/api/v1/bills/{consumer_account_id}/history` | Get bill history (up to 24 months) | Yes |
| PATCH | `/api/v1/bills/{bill_id}/status` | Update bill paid/unpaid status | Yes |
| GET | `/api/v1/bills/summary` | Aggregate this-month spend across all utilities | Yes |

Full request/response schemas in **P21 — API Spec**.

---

## 10. Frontend Components

All components live in `frontend/app/(dashboard)/bills/`:

| Component | File | Purpose |
|-----------|------|---------|
| `ConsumerAccountCard` | `components/ConsumerAccountCard.tsx` | Dashboard bill card |
| `BillDetailView` | `app/bills/[id]/page.tsx` | Full bill breakdown page |
| `BillTrendChart` | `components/BillTrendChart.tsx` | Recharts bar chart, 6-month |
| `AddUtilityModal` | `components/AddUtilityModal.tsx` | Multi-step add flow |
| `ProviderSelector` | `components/ProviderSelector.tsx` | Utility type + provider picker |
| `ConsumerNumberInput` | `components/ConsumerNumberInput.tsx` | Masked input with validation |
| `DashboardSummaryCard` | `components/DashboardSummaryCard.tsx` | Total spend overview |
| `EmptyStateCTA` | `components/EmptyStateCTA.tsx` | No-account welcome state |

### 10.1 React Query Keys

```typescript
// frontend/lib/queryKeys.ts
export const billKeys = {
  all: ['bills'] as const,
  byAccount: (accountId: string) => ['bills', accountId] as const,
  history: (accountId: string, months: number) => ['bills', accountId, 'history', months] as const,
  summary: () => ['bills', 'summary'] as const,
};
```

### 10.2 Optimistic Update on Mark Paid

When user taps "Mark as Paid":
1. Optimistically update local React Query cache (`status: 'paid'`)
2. PATCH request fires in background
3. On error: rollback cache to previous state + show toast "Update failed"

---

## 11. Error States & Edge Cases

| Scenario | Handling |
|----------|----------|
| Portal unreachable (503) | Show "Portal temporarily unavailable. Try again later." with last-fetched timestamp |
| No bill found | Show "No pending bill. Either already paid or not yet generated." |
| Parsing failed | Show "Our parser may be outdated. We've been alerted and will fix it." (triggers admin alert per P05 §10) |
| Consumer number already added | Return 409 Conflict from API; frontend shows "This consumer number is already linked to your account" |
| Captcha detected | Show "LESCO is currently blocking automated checks. Please try in 30 minutes." |
| Bill unchanged since last fetch | Return cached bill with `from_cache: true` flag; show "Last updated: X hours ago" |

---

## 12. Caching Strategy

- Latest bill per consumer account: cached in React Query with `staleTime: 30 * 60 * 1000` (30 minutes) — prevents unnecessary re-fetches on navigation
- Bill history: `staleTime: 24 * 60 * 60 * 1000` (24 hours) — history doesn't change
- Dashboard summary: `staleTime: 15 * 60 * 1000` (15 minutes)
- Manual "Refresh ↺" button bypasses stale time and forces a live scrape
