# P10 — Budget Manager Module (M5)

**Document Type:** Rigid Plan  
**Status:** Authoritative  
**Depends On:** P03 (Database Schema), P04 (Auth), P06 (Bill Tracker), P07 (Consumption Monitor), P08 (Bill Estimator)  
**Required By:** P18 (Monetization), P19 (Notifications), P20 (Frontend), P21 (API Spec)

---

## 1. Scope

The Budget Manager gives users one place to track monthly household utility spending and adjacent recurring costs. It combines actual scraped bills, estimated current-cycle bills, and manual expense entries into a monthly budget dashboard.

Cable TV and mobile data are not separate modules. They exist here as manual budget categories because reliable public data sources do not exist.

---

## 2. User-Facing Features

| Feature | Priority | Description |
|---------|----------|-------------|
| Monthly utility summary | P0 | Total electricity, gas, water, internet spending |
| Budget limit per category | P1 | User sets monthly caps |
| Actual vs projected | P0 | Combines paid bills and estimates |
| Manual expense entry | P1 | Add cable, mobile data, groceries, education, repairs |
| Recurring expenses | P1 | Auto-create monthly expense entries |
| Overspend alerts | P1 | Notify when category crosses 80% or 100% |
| Monthly report | P2 | Export PDF/CSV; premium feature |
| Multi-home budget | P2 | Group expenses by home |

---

## 3. Budget Categories

Default categories seeded for every user:

| Code | Label | Type | Source |
|------|-------|------|--------|
| `electricity` | Electricity | utility | Bills + estimates |
| `gas` | Gas | utility | Bills + estimates |
| `water` | Water | utility | Bills + estimates |
| `internet` | Internet | utility | Bills + manual |
| `cable_tv` | Cable TV | manual | Manual only |
| `mobile_data` | Mobile Data | manual | Manual only |
| `solar_maintenance` | Solar Maintenance | manual | Manual only |
| `groceries` | Groceries | manual | Manual only |
| `education` | Education | manual | Manual only |
| `other` | Other | manual | Manual only |

Users can add custom categories after onboarding.

---

## 4. Frontend Routes

| Route | Purpose |
|-------|---------|
| `/budget` | Monthly budget dashboard |
| `/budget/add` | Add manual expense |
| `/budget/categories` | Manage categories and budget limits |
| `/budget/report/[month]` | Monthly report view |

---

## 5. Dashboard Layout

Required sections:

1. Month selector
2. Total spend card
3. Projected end-of-month spend card
4. Category progress bars
5. Utility bill cards from P06
6. Manual expenses list
7. Add expense floating action button
8. Insight card from P17 when available

---

## 6. Calculation Rules

### 6.1 Actual Spend

Actual spend for a month:

```text
actual_spend = sum(bills.amount_payable where billing_month = selected_month)
             + sum(expense_entries.amount where expense_month = selected_month)
```

### 6.2 Projected Spend

Projected spend:

```text
projected_spend = actual_paid_or_issued_bills
                + current_cycle_estimates_from_P08_for_unissued_bills
                + recurring_manual_expenses_not_yet_entered
```

Never double-count a utility if an official bill exists for the selected month.

### 6.3 Budget Status

| Status | Rule |
|--------|------|
| `safe` | spend < 80% of limit |
| `warning` | spend >= 80% and < 100% |
| `exceeded` | spend >= 100% |

---

## 7. API Contracts

### 7.1 `GET /api/v1/budget/summary?month=2025-06`

Response:
```json
{
  "month": "2025-06",
  "actual_spend": 18400,
  "projected_spend": 22600,
  "budget_limit": 25000,
  "status": "warning",
  "categories": [
    { "code": "electricity", "actual": 4280, "projected": 5100, "limit": 9000, "status": "safe" },
    { "code": "gas", "actual": 1200, "projected": 1200, "limit": 3000, "status": "safe" }
  ]
}
```

### 7.2 `POST /api/v1/budget/expenses`

Request:
```json
{
  "category_id": "uuid",
  "home_id": "uuid",
  "amount": 700,
  "expense_date": "2025-06-05",
  "description": "Cable guy",
  "is_recurring": true
}
```

### 7.3 `PUT /api/v1/budget/limits/{category_id}`

Sets or updates a monthly limit.

---

## 8. Notifications

P19 sends:

- 80% budget warning
- 100% budget exceeded alert
- monthly report ready notification
- recurring expense reminder if not entered by expected date

---

## 9. Monetization Hooks

Budget context may show affiliate recommendations only when relevant:

| Trigger | Recommendation |
|---------|----------------|
| Electricity spend up 25% | Energy-saving appliances, UPS battery check |
| Internet bill high | ISP Comparison module link |
| Solar maintenance due | Solar cleaning/vendor lead |
| Mobile data high | Manual tips only; no affiliate until partnerships exist |

Ads must not appear inside the expense entry form.

---

## 10. Acceptance Criteria

- Budget dashboard combines bills, estimates, and manual expenses correctly.
- Cable TV and mobile data are manual expense categories only.
- Free users can track at least 10 categories.
- Overspend status is available through API for notifications.
- No projected utility is counted once an official bill exists.
