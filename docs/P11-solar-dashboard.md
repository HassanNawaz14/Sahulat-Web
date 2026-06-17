# P11 — Solar Dashboard Module (M6)

**Document Type:** Rigid Plan  
**Status:** Authoritative  
**Depends On:** P02 (Tech Stack), P03 (Database Schema), P04 (Auth), P06 (Bill Tracker), P08 (Bill Estimator)  
**Required By:** P16 (Solar Sizing Tool), P17 (Usage Insights), P18 (Monetization), P19 (Notifications), P21 (API Spec)

---

## 1. Scope

The Solar Dashboard connects a user's home solar inverter account to Sahulat and displays production, savings, net metering value, grid offset, ROI progress, and panel health alerts. It is a V1 P1 module because solar owners are high-value users with strong affiliate and lead-generation potential.

Supported inverter brands in priority order: Growatt, Solis, Huawei FusionSolar. Growatt is V1 priority.

---

## 2. User-Facing Features

| Feature | Priority | Description |
|---------|----------|-------------|
| Add solar installation | P1 | User enters system size, install cost, inverter brand |
| Connect inverter account | P1 | Store encrypted API credentials/token |
| Daily production chart | P1 | kWh produced today and last 7 days |
| Monthly savings | P1 | Compare solar production against DISCO unit rate |
| Net metering credit | P1 | Estimate exported units at NEPRA buyback rate |
| ROI countdown | P1 | Months/years until system pays back |
| Panel health alert | P2 | Detect abnormal production drop |
| Maintenance reminder | P2 | Cleaning reminder every 30-45 days |

---

## 3. Data Model

Uses P03 solar tables:

- `solar_installations`
- `solar_daily_production`
- `solar_alerts`
- `consumer_accounts`
- `bills`

Required solar installation fields:

| Field | Purpose |
|-------|---------|
| `system_size_kw` | Installed capacity |
| `installation_cost` | ROI base value |
| `inverter_brand` | `growatt`, `solis`, `huawei` |
| `api_username_encrypted` | Optional encrypted username |
| `api_password_encrypted` | Optional encrypted password |
| `api_token_encrypted` | Optional encrypted token |
| `net_metering_enabled` | Enables export credit calculations |
| `commissioning_date` | ROI and production baseline start |

---

## 4. Onboarding Flow

**Route:** `/solar/setup`

Steps:

1. Select inverter brand.
2. Enter system size in kW.
3. Enter installation cost.
4. Select linked electricity consumer account if available.
5. Toggle net metering enabled.
6. Enter inverter credentials or skip API connection.
7. Backend tests connection and fetches last 7 days production.
8. Dashboard becomes active.

Skipping API connection creates a manual solar profile where the user can enter daily production manually.

---

## 5. Inverter Integration

Backend location:

```
backend/app/services/solar/
  base.py
  growatt.py
  solis.py
  huawei.py
  normalizer.py
```

All adapters implement:

```python
class BaseSolarAdapter(ABC):
    async def authenticate(self, credentials: SolarCredentials) -> SolarAuthResult: ...
    async def fetch_daily_production(self, installation: dict, date: date) -> SolarProduction: ...
    async def fetch_range(self, installation: dict, start: date, end: date) -> list[SolarProduction]: ...
```

Normalize all production to kWh.

---

## 6. Savings Calculation

Monthly savings:

```text
self_consumed_value = estimated_self_consumed_kwh * effective_import_rate
export_credit = exported_kwh * nepra_net_metering_export_rate
monthly_savings = self_consumed_value + export_credit
roi_remaining = installation_cost - sum(monthly_savings_since_commissioning)
```

If smart import/export data is unavailable, estimate self-consumed vs exported split using:

| Input | Default |
|-------|---------|
| Daytime household usage ratio | 60% self-consumed |
| Export ratio | 40% exported |
| Export rate | Rs. 27/unit unless tariff table overrides |

The estimate must be labelled as estimate until real net-meter bill data is linked.

---

## 7. API Contracts

### 7.1 `POST /api/v1/solar/installations`

Creates installation.

### 7.2 `POST /api/v1/solar/installations/{id}/connect`

Stores encrypted credentials and tests adapter.

### 7.3 `GET /api/v1/solar/dashboard/{installation_id}`

Response:
```json
{
  "installation_id": "uuid",
  "system_size_kw": 10,
  "today_kwh": 42.5,
  "month_kwh": 860.2,
  "estimated_monthly_savings": 31200,
  "export_credit": 9200,
  "roi_paid_back_percent": 36,
  "estimated_payback_months_remaining": 28,
  "health_status": "normal",
  "chart": [
    { "date": "2025-06-17", "production_kwh": 42.5 }
  ]
}
```

---

## 8. Panel Health Rules

Create alert when:

| Rule | Trigger |
|------|---------|
| Sunny baseline drop | Today's production is 30% below rolling 14-day sunny baseline |
| Zero production | Production is 0 after 11:00 AM local time on a non-rainy day |
| Inverter disconnected | API fetch fails for 24 hours |
| Cleaning due | 45 days since last maintenance mark |

Weather API is not required in V1. Use production baseline only.

---

## 9. Monetization Hooks

- Solar cleaning service leads
- Battery upgrade affiliate links
- Inverter/UPS product recommendations
- Solar sizing tool handoff for non-solar users
- Vendor lead form for users whose bills remain high

---

## 10. Acceptance Criteria

- User can create a solar installation manually.
- Growatt adapter is implemented before solar public launch.
- Dashboard shows today, month, savings, ROI, and health status.
- Credentials are encrypted before storage.
- Failed API syncs do not break dashboard; last known data remains visible.
