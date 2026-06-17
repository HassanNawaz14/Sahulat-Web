# P16 — Solar Sizing Tool Module (M11)

**Document Type:** Rigid Plan  
**Status:** Authoritative  
**Depends On:** P08 (Bill Estimator), P11 (Solar Dashboard), P18 (Monetization)  
**Required By:** P18 (Monetization), P20 (Frontend), P21 (API Spec)

---

## 1. Scope

Solar Sizing Tool recommends a home solar system size, estimated cost, battery option, payback period, and vendor lead path based on a user's electricity consumption, bill history, city, roof constraints, and net metering preference.

It is a V2/V3 module with high monetization potential through solar vendor leads.

---

## 2. Inputs

| Field | Required | Source |
|-------|----------|--------|
| Monthly units | Yes | User input or P06 bill history |
| City | Yes | Profile/home |
| Average bill amount | No | P06 bills |
| Roof area | No | User input |
| Daytime usage ratio | No | Default 60% |
| Battery backup required | No | User input |
| Net metering desired | No | User input |
| Budget range | No | User input |

---

## 3. Output

```json
{
  "recommended_system_kw": 7.5,
  "estimated_monthly_generation_kwh": 900,
  "estimated_cost_min": 900000,
  "estimated_cost_max": 1250000,
  "battery_recommendation": "optional",
  "estimated_monthly_savings": 32000,
  "estimated_payback_years": 3.2,
  "roof_area_required_sqft": 650,
  "net_metering_recommended": true
}
```

---

## 4. Calculation Rules

### 4.1 System Size

```text
required_kw = monthly_units / (city_solar_yield_kwh_per_kw_per_month)
recommended_kw = round_up_to_nearest_0_5(required_kw * safety_factor)
```

Default city yield:

| City | kWh/kW/month |
|------|--------------|
| Lahore | 120 |
| Karachi | 125 |
| Islamabad | 115 |
| Multan | 130 |
| Peshawar | 118 |
| Quetta | 132 |

Safety factor: 1.15.

### 4.2 Cost Estimate

```text
cost_min = recommended_kw * low_market_rate_per_kw
cost_max = recommended_kw * high_market_rate_per_kw
```

Rates are admin-maintained because market prices change quickly.

### 4.3 Payback

Uses P08 tariff estimate for current units and solar generation offset.

---

## 5. Frontend Routes

| Route | Purpose |
|-------|---------|
| `/solar/sizing` | Public calculator |
| `/solar/sizing/results` | Recommendation results |
| `/solar/sizing/vendor-lead` | Optional vendor contact form |

---

## 6. Vendor Lead Flow

1. User views result.
2. App asks consent to connect with vetted installer.
3. User enters phone and preferred contact time.
4. Backend creates lead with recommended system size and city.
5. Admin/vendor dashboard exports lead.

No lead is sent without explicit consent.

---

## 7. Acceptance Criteria

- Tool works without login.
- Logged-in users can use bill history as input.
- Recommendation includes system size, cost range, savings, payback.
- Vendor lead creation is consent-based.
- All assumptions are visible in result details.
