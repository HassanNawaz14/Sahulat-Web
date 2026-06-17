# P17 — Usage Insights Module (M12)

**Document Type:** Rigid Plan  
**Status:** Authoritative  
**Depends On:** P03 (Database Schema), P06 (Bill Tracker), P07 (Consumption Monitor), P08 (Bill Estimator), P10 (Budget Manager), P11 (Solar Dashboard), P12 (Community Reports)  
**Required By:** P18 (Monetization), P19 (Notifications), P20 (Frontend), P21 (API Spec)

---

## 1. Scope

Usage Insights is the analytics layer that turns raw bills, meter readings, budget entries, solar production, and community data into actionable recommendations. It is V2/P3 because it needs several months of data to be genuinely useful.

Insights must be explainable. Do not show black-box claims without the source data used.

---

## 2. Insight Types

| Code | Description | Source |
|------|-------------|--------|
| `bill_spike` | Bill increased unusually | Bills |
| `usage_spike` | Units increased unusually | Meter readings/bills |
| `slab_risk` | User likely to cross next slab | P07/P08 |
| `seasonal_pattern` | Comparison to past months | Bills |
| `budget_risk` | Projected overspend | P10 |
| `solar_underperformance` | Production lower than baseline | P11 |
| `area_outage_pattern` | Area has frequent outages | P12 |
| `appliance_cost_estimate` | Estimate AC/heater cost | P07/P08 |

---

## 3. Rules Engine

Backend location:

```
backend/app/services/insights/
  engine.py
  rules.py
  serializers.py
```

Each insight rule implements:

```python
class InsightRule(Protocol):
    code: str
    min_data_points: int
    async def evaluate(self, user_id: UUID, db) -> list[Insight]: ...
```

Insights are stored only when actionable. Avoid filling the UI with generic tips.

---

## 4. Example Rules

### 4.1 Bill Spike

Trigger when current electricity bill is 25% higher than 3-month average and at least Rs. 1,000 higher.

Message:

```text
Your electricity bill is 31% higher than your recent average. Most of the increase came from 78 extra units, which pushed you into the 301-400 slab.
```

### 4.2 Appliance Cost Estimate

For AC estimate:

```text
estimated_ac_cost = daily_hours * ac_kw_rating * days * effective_unit_rate
```

User must be able to change assumptions.

### 4.3 Solar Underperformance

Uses P11 health baseline. Shows only if solar installation exists.

---

## 5. Frontend Placement

Insights appear in:

- `/dashboard` as top 1-2 cards
- `/consumption` as slab and usage insights
- `/budget` as overspend insights
- `/solar` as production insights

Each card needs:

1. short title
2. explanation
3. source label
4. action button
5. dismiss button

---

## 6. API Contracts

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/insights` | GET | List active insights |
| `/api/v1/insights/{id}/dismiss` | POST | Dismiss insight |
| `/api/v1/insights/recompute` | POST | Auth/admin recompute |

---

## 7. Notification Rules

Only urgent insights create notifications:

- slab risk within 10 units
- budget exceeded
- solar zero production
- scheduled outage reminder is handled by P09/P19, not here

---

## 8. Acceptance Criteria

- Insights are generated from real user data.
- Every insight includes source fields.
- User can dismiss insights.
- No insight requires machine learning in V1/V2.
- Rules are unit-tested with fixed fixtures.
