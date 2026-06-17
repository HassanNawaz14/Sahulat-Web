# P07 — Consumption Monitor Module (M2)

**Document Type:** Rigid Plan  
**Status:** Authoritative  
**Depends On:** P03 (Database Schema), P04 (Auth), P06 (Bill Tracker), P08 (Bill Estimator)  
**Required By:** P08 (Bill Estimator), P10 (Budget Manager), P19 (Notifications)

---

## 1. Scope

The Consumption Monitor allows users to track electricity (and optionally gas/water) unit consumption across a billing cycle by entering periodic meter readings. It computes daily usage rate, projects the end-of-month bill before the actual bill arrives, and fires slab boundary alerts when a user is approaching a higher tariff slab. This is the feature that drives the highest daily opens — users check consumption daily to see if they're on track.

---

## 2. Features

| Feature | Priority | Description |
|---------|----------|-------------|
| Manual meter reading entry | P0 | User enters meter reading; app computes units since last reading |
| Daily usage rate | P0 | Average units/day based on readings in current cycle |
| Month-end bill projection | P0 | Estimated bill if consumption continues at current rate |
| Slab boundary alert | P0 | "10 units away from next slab — Rs. 800 extra" |
| Consumption trend chart | P1 | Month-over-month unit consumption bar chart |
| Seasonal comparison | P1 | "Same month last year you used 280 units" |
| Appliance cost estimator | P2 | "Your AC (~1.5 ton) costs ~Rs. 4,200/month at current rate" |
| Reading reminder notification | P2 | Push reminder every 3 days to enter a new reading |

---

## 3. Meter Reading Entry

### 3.1 Frontend Route

`/consumption` — main consumption screen  
`/consumption/[consumerAccountId]` — per-account detail

### 3.2 Entry Form

Only shown for accounts with `utility_type IN ('electricity', 'gas', 'water')` — internet has no meter.

```
┌───────────────────────────────────────────┐
│  ⚡ LESCO — Main Meter                   │
│                                           │
│  Enter Today's Reading                    │
│  ┌────────────────────────┐               │
│  │  2,157                 │  kWh          │
│  └────────────────────────┘               │
│                                           │
│  Previous Reading:  2,145  (3 days ago)   │
│  Units since then:  12 kWh (4.0/day)     │
│                                           │
│  [Save Reading]                           │
└───────────────────────────────────────────┘
```

### 3.3 API — Submit Meter Reading

**Endpoint:** `POST /api/v1/consumption/readings`

**Request:**
```json
{
  "consumer_account_id": "uuid",
  "reading_date": "2025-06-17",
  "reading_value": 2157.0,
  "notes": "optional"
}
```

**Backend logic:**
```python
@router.post("/consumption/readings")
async def submit_reading(body: MeterReadingCreate, current_user=Depends(get_current_user), db=Depends(get_db)):
    # 1. Verify account ownership
    account = await get_owned_account(body.consumer_account_id, current_user["user_id"], db)

    # 2. Fetch previous reading
    prev = await db.fetch_one(
        "SELECT * FROM meter_readings WHERE consumer_account_id = :id ORDER BY reading_date DESC LIMIT 1",
        {"id": body.consumer_account_id}
    )

    # 3. Compute units_since_last
    units_since_last = None
    if prev and body.reading_value >= prev["reading_value"]:
        units_since_last = body.reading_value - prev["reading_value"]
    elif prev and body.reading_value < prev["reading_value"]:
        # Meter rollover (rare but possible for older meters)
        units_since_last = (99999 - prev["reading_value"]) + body.reading_value

    # 4. Compute estimated bill using current tariff (calls P08 tariff engine)
    estimated_bill = None
    if account["utility_type"] == "electricity":
        # Get total units consumed this cycle
        cycle_start = get_current_cycle_start(account)
        total_units = await get_cycle_units(body.consumer_account_id, cycle_start, body.reading_value, db)
        estimated_bill = compute_electricity_bill(total_units, account["provider_code"])

    # 5. Insert reading
    await db.execute("""
        INSERT INTO meter_readings (consumer_account_id, user_id, reading_date, reading_value, units_since_last, estimated_bill, notes)
        VALUES (:ca_id, :uid, :date, :val, :units, :est, :notes)
        ON CONFLICT (consumer_account_id, reading_date) DO UPDATE SET
            reading_value = EXCLUDED.reading_value,
            units_since_last = EXCLUDED.units_since_last,
            estimated_bill = EXCLUDED.estimated_bill
    """, {...})

    # 6. Check slab boundary — if near threshold, create alert
    await check_slab_boundary(body.consumer_account_id, current_user["user_id"], total_units, db)

    return {"units_since_last": units_since_last, "estimated_bill": estimated_bill, "total_cycle_units": total_units}
```

### 3.4 Cycle Start Detection

The billing cycle start date is determined from the last fetched bill's `issue_date`. If no bill exists yet, default to the 1st of the current month. The cycle is always approximately 30 days.

```python
def get_current_cycle_start(account: dict, last_bill: dict = None) -> date:
    if last_bill and last_bill.get("issue_date"):
        # Cycle starts ~1 month after last bill's issue date
        last_issue = date.fromisoformat(last_bill["issue_date"])
        return last_issue.replace(day=1) + relativedelta(months=1)
    return date.today().replace(day=1)
```

---

## 4. Consumption Dashboard

### 4.1 Stats Cards

For each electricity/gas/water consumer account:

```
┌─────────────────────────────────────────────────┐
│  ⚡ LESCO — Main Meter       Cycle: Jun 2025    │
├──────────────┬──────────────┬───────────────────┤
│ Total So Far │  Daily Rate  │  Est. Month Bill  │
│  210 kWh     │  8.4/day     │  Rs. ~3,600       │
├──────────────┴──────────────┴───────────────────┤
│ SLAB PROGRESS                                   │
│  [============================░░░░░░] 70%       │
│  210 / 300 units → Next slab at 301             │
│  ⚠ 90 units left in current slab               │
├─────────────────────────────────────────────────┤
│ PROJECTION                                      │
│  At 8.4 units/day, you'll use ~252 units        │
│  by end of month — staying in 201–300 slab ✓   │
└─────────────────────────────────────────────────┘
```

### 4.2 Consumption Trend Chart

**Component:** `ConsumptionTrendChart.tsx` using Recharts `BarChart`

- X-axis: Last 6 billing months
- Y-axis: Units consumed
- Bars colored by slab: green (0–200), yellow (201–300), orange (301–400), red (401+)
- Tooltip: "June 2025: 312 kWh — Slab 301–400 — Rs. 4,280"
- Data source: `bills.units_consumed` for historical months; `meter_readings` aggregate for current month

### 4.3 API — Get Consumption Summary

**Endpoint:** `GET /api/v1/consumption/summary/{consumer_account_id}`

Response:
```json
{
  "consumer_account_id": "uuid",
  "cycle_start": "2025-06-01",
  "total_units_so_far": 210.0,
  "daily_rate": 8.4,
  "days_elapsed": 25,
  "days_remaining": 5,
  "projected_units": 252.0,
  "current_slab": { "min": 201, "max": 300, "rate": 16.80 },
  "next_slab": { "threshold": 301, "rate": 20.15, "units_away": 90 },
  "estimated_bill": 3600.0,
  "last_reading": { "date": "2025-06-17", "value": 2157.0 },
  "readings_this_cycle": 8
}
```

---

## 5. Slab Boundary Alert System

### 5.1 Alert Trigger Logic

Called every time a meter reading is submitted AND by the daily `slab_boundary_check` cron job.

```python
ELECTRICITY_SLABS = [
    {"min": 0,    "max": 100,  "rate": 7.74},
    {"min": 101,  "max": 200,  "rate": 10.06},
    {"min": 201,  "max": 300,  "rate": 16.80},
    {"min": 301,  "max": 400,  "rate": 20.15},
    {"min": 401,  "max": 500,  "rate": 22.65},
    {"min": 501,  "max": 600,  "rate": 25.09},
    {"min": 601,  "max": 700,  "rate": 26.40},
    {"min": 701,  "max": None, "rate": 26.84},
]

ALERT_THRESHOLDS = [10, 20, 50]  # Alert when N units away from next slab

async def check_slab_boundary(consumer_account_id: UUID, user_id: UUID, current_units: float, db):
    current_slab = get_current_slab(current_units)
    if current_slab["max"] is None:
        return  # Already in highest slab

    units_to_next = current_slab["max"] - current_units + 1

    for threshold in ALERT_THRESHOLDS:
        if units_to_next <= threshold:
            billing_period = date.today().replace(day=1)

            # Check if already alerted for this threshold this cycle
            existing = await db.fetch_one("""
                SELECT id FROM slab_alerts
                WHERE consumer_account_id = :ca_id
                AND billing_period = :period
                AND slab_threshold = :threshold
            """, {"ca_id": consumer_account_id, "period": billing_period, "threshold": current_slab["max"] + 1})

            if existing:
                continue  # Already sent this alert

            # Compute cost if crossed
            next_slab = get_next_slab(current_slab)
            cost_if_crossed = compute_marginal_cost(current_units, current_slab, next_slab)

            # Insert alert record
            await db.execute("""
                INSERT INTO slab_alerts (consumer_account_id, user_id, billing_period, slab_threshold, units_at_alert, cost_if_crossed)
                VALUES (:ca_id, :uid, :period, :threshold, :units, :cost)
                ON CONFLICT DO NOTHING
            """, {...})

            # Fire push notification
            await send_slab_alert_notification(user_id, units_to_next, cost_if_crossed)
            break  # Only send the tightest threshold alert
```

### 5.2 Cost Calculation for Slab Crossing

The "extra cost if you cross the slab" is not just the marginal rate on the extra units — in Pakistan's electricity billing, crossing a slab threshold causes **all units in the month to be re-rated at the new slab's rate** (cumulative rate, not marginal). This is the critical insight unique to Sahulat.

```python
def compute_marginal_cost(current_units: float, current_slab: dict, next_slab: dict) -> float:
    """
    In NEPRA slab billing, the rate for the ENTIRE consumption changes when you
    cross a slab boundary. This function computes the extra cost of crossing by 1 unit.
    """
    cost_staying = current_units * current_slab["rate"]
    cost_crossing = (current_units + 1) * next_slab["rate"]  # All units re-rated
    return round(cost_crossing - cost_staying, 2)
```

**Example:** User at 299 units. Next unit (300→301) triggers 301–400 slab. Extra cost = (300 × Rs. 20.15) - (299 × Rs. 16.80) = Rs. 6,045 - Rs. 5,023.20 = **Rs. 1,021.80 extra for ONE unit.** This is the killer alert message.

### 5.3 Alert Notification Message

```
Title: ⚠️ Slab Alert — LESCO
Body:  You've used 290 units. Just 10 more units will push your entire
       month's bill into the next slab, costing Rs. 1,022 extra!
       Tap to see your consumption.
```

---

## 6. Appliance Cost Estimator (P2 Feature)

Available as a separate card within the consumption detail view. Uses average wattage estimates for common Pakistani household appliances.

```typescript
// frontend/lib/constants/appliances.ts
export const APPLIANCES = [
  { id: "ac_1ton",    name: "AC (1 Ton)",     watts: 1100, hoursPerDay: 8 },
  { id: "ac_1_5ton",  name: "AC (1.5 Ton)",   watts: 1500, hoursPerDay: 8 },
  { id: "fridge",     name: "Refrigerator",   watts: 150,  hoursPerDay: 24 },
  { id: "washing",    name: "Washing Machine", watts: 500,  hoursPerDay: 1  },
  { id: "tv_led",     name: "LED TV (43\")",  watts: 80,   hoursPerDay: 6  },
  { id: "fan",        name: "Ceiling Fan",    watts: 75,   hoursPerDay: 16 },
  { id: "water_pump", name: "Water Pump",     watts: 750,  hoursPerDay: 2  },
  { id: "iron",       name: "Iron",           watts: 1000, hoursPerDay: 0.5},
];

export function estimateApplianceCost(
  watts: number, hoursPerDay: number, dailyRatePKR: number
): number {
  const kwhPerDay = (watts / 1000) * hoursPerDay;
  const kwhPerMonth = kwhPerDay * 30;
  return kwhPerMonth * dailyRatePKR;
}
```

UI: Checklist of appliances → user toggles which they have → app shows estimated monthly cost per appliance and total. Not persisted — purely frontend calculation. `dailyRatePKR` is derived from the user's current slab rate.

---

## 7. Reading History View

**Route:** `/consumption/[consumerAccountId]/history`

Simple table of all meter reading entries:

| Date | Reading | Units | Est. Bill |
|------|---------|-------|-----------|
| Jun 17 | 2,157 | 12 kWh | Rs. 3,600 |
| Jun 14 | 2,145 | 18 kWh | Rs. 3,200 |
| Jun 11 | 2,127 | ... | ... |

**API:** `GET /api/v1/consumption/readings/{consumer_account_id}?limit=30`

Returns last 30 readings ordered by `reading_date DESC`.

---

## 8. API Endpoints Summary

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/api/v1/consumption/readings` | Submit new meter reading | Yes |
| GET | `/api/v1/consumption/readings/{consumer_account_id}` | Reading history | Yes |
| GET | `/api/v1/consumption/summary/{consumer_account_id}` | Current cycle stats + projection | Yes |
| GET | `/api/v1/consumption/trend/{consumer_account_id}` | 6-month historical units data | Yes |
| GET | `/api/v1/consumption/slab-alerts/{consumer_account_id}` | Slab alerts fired this cycle | Yes |

---

## 9. Frontend Components

| Component | File | Purpose |
|-----------|------|---------|
| `ReadingEntryForm` | `components/consumption/ReadingEntryForm.tsx` | Meter reading input |
| `ConsumptionSummaryCard` | `components/consumption/ConsumptionSummaryCard.tsx` | Stats + slab progress bar |
| `SlabProgressBar` | `components/consumption/SlabProgressBar.tsx` | Visual slab indicator |
| `ConsumptionTrendChart` | `components/consumption/ConsumptionTrendChart.tsx` | Recharts bar chart |
| `ProjectionCard` | `components/consumption/ProjectionCard.tsx` | Month-end projection display |
| `ApplianceEstimator` | `components/consumption/ApplianceEstimator.tsx` | Appliance checklist calculator |
| `ReadingHistory` | `components/consumption/ReadingHistory.tsx` | Tabular reading log |
