# P08 — Bill Estimator Module (M4)

**Document Type:** Rigid Plan  
**Status:** Authoritative  
**Depends On:** P02 (Tech Stack), P03 (Database Schema), P06 (Bill Tracker), P07 (Consumption Monitor)  
**Required By:** P07 (Consumption Monitor), P10 (Budget Manager), P16 (Solar Sizing Tool), P17 (Usage Insights), P19 (Notifications), P21 (API Spec)

---

## 1. Scope

The Bill Estimator calculates expected utility bills before the official bill is issued. It supports electricity, gas, and water in V1, with internet package cost estimation in V2 through the ISP dataset. The estimator is a P0 feature because it powers slab alerts, consumption projections, budget forecasting, solar savings comparison, and SEO traffic from searches like "LESCO bill calculator" and "SNGPL bill estimate".

The estimator must be deterministic. Given the same provider, tariff version, units, protected/lifeline flags, and taxes, it must always return the same result.

---

## 2. User-Facing Features

| Feature | Priority | Description |
|---------|----------|-------------|
| Electricity bill estimate | P0 | Enter kWh units and provider; return estimated bill with slab breakdown |
| Gas bill estimate | P0 | Enter MMBtu/Hm3 reading difference; return OGRA slab estimate |
| Water bill estimate | P1 | Enter consumption or flat category; return WASA/KW&SB estimate |
| Public SEO calculator page | P0 | `/estimate` usable without login |
| Authenticated saved estimate | P1 | Save estimates against a consumer account for future comparison |
| Slab crossing delta | P0 | Show extra cost if one more unit crosses the next slab |
| Taxes and surcharge breakdown | P0 | Display energy charges, FC surcharge, GST, meter rent, arrears placeholder |
| Tariff version display | P0 | Show effective tariff month and source authority |
| WhatsApp share | P1 | Share estimate as formatted text |

---

## 3. Frontend Routes

| Route | Access | Purpose |
|-------|--------|---------|
| `/estimate` | Public | Main multi-utility estimator landing page |
| `/estimate/electricity` | Public | SEO page for electricity estimate |
| `/estimate/gas` | Public | SEO page for gas estimate |
| `/estimate/water` | Public | SEO page for water estimate |
| `/consumption/[consumerAccountId]/estimate` | Auth | Estimate current cycle bill from saved readings |

Public estimator pages must be server-rendered or statically generated with current tariff metadata so search engines can index meaningful content.

---

## 4. Estimator Inputs

### 4.1 Electricity Input

| Field | Type | Required | Rule |
|-------|------|----------|------|
| `provider_code` | string | Yes | One of DISCO provider codes from P03 |
| `units` | number | Yes | `0 <= units <= 5000` |
| `phase_type` | string | Yes | `single_phase` or `three_phase` |
| `connection_type` | string | Yes | V1 only `residential` |
| `protected_customer` | boolean | No | Defaults false |
| `lifeline_customer` | boolean | No | Defaults false |
| `include_taxes` | boolean | No | Defaults true |
| `arrears` | number | No | Defaults 0 |

### 4.2 Gas Input

| Field | Type | Required | Rule |
|-------|------|----------|------|
| `provider_code` | string | Yes | `sngpl` or `ssgc` |
| `consumption_mmbtu` | number | Yes | `0 <= value <= 50` |
| `meter_rent` | number | No | Defaults from tariff table |
| `include_taxes` | boolean | No | Defaults true |

### 4.3 Water Input

| Field | Type | Required | Rule |
|-------|------|----------|------|
| `provider_code` | string | Yes | `wasa_lhr`, `kwsb`, or supported WASA code |
| `usage_units` | number | No | Optional where metered billing exists |
| `property_type` | string | Yes | `residential` or `commercial` |
| `property_size_marla` | number | No | Used by flat-rate providers |

---

## 5. Tariff Data Rules

Tariffs are stored in P03 tables: `electricity_tariffs`, `gas_tariffs`, and `water_tariffs`.

Mandatory tariff fields used by the engine:

| Field | Meaning |
|-------|---------|
| `provider_code` | Utility provider |
| `effective_from` | First date this tariff applies |
| `effective_to` | Last date; null means current |
| `slab_min` | Inclusive lower unit boundary |
| `slab_max` | Inclusive upper unit boundary; null means open-ended |
| `rate_per_unit` | Base rate |
| `fixed_charge` | Meter rent or monthly charge |
| `tax_config` | JSONB for GST, FC surcharge, quarterly adjustments |

**Rule:** Tariff updates are admin-managed, not scraped automatically in V1. NEPRA/OGRA notices are checked quarterly and inserted manually through admin SQL seed files or the internal admin panel.

---

## 6. Calculation Engine

### 6.1 Backend Location

```
backend/app/services/estimators/
  __init__.py
  electricity.py
  gas.py
  water.py
  schemas.py
  tariff_loader.py
```

### 6.2 Electricity Algorithm

```python
def estimate_electricity_bill(input: ElectricityEstimateInput, tariffs: list[TariffSlab]) -> EstimateResult:
    applicable = select_current_tariffs(tariffs, input.provider_code, input.connection_type)
    units_remaining = input.units
    energy_total = 0
    slab_lines = []

    for slab in applicable:
        if units_remaining <= 0:
            break
        slab_units = min(units_remaining, slab.max_units - slab.min_units + 1 if slab.max_units else units_remaining)
        line_amount = slab_units * slab.rate_per_unit
        energy_total += line_amount
        slab_lines.append({"range": slab.label, "units": slab_units, "rate": slab.rate_per_unit, "amount": line_amount})
        units_remaining -= slab_units

    taxes = compute_electricity_taxes(energy_total, input.provider_code) if input.include_taxes else 0
    total = energy_total + taxes + fixed_charges + input.arrears
    return EstimateResult(total=round(total), breakdown=slab_lines, taxes=taxes)
```

**Important:** If Pakistan's active tariff policy charges all units at the final slab rate for any category, the `tariff_mode` column must control the algorithm: `incremental` vs `single_slab`. Never hardcode the policy in the UI.

### 6.3 Slab Boundary Delta

The engine must return:

```json
{
  "current_slab": "201-300",
  "next_slab_threshold": 301,
  "units_to_next_slab": 11,
  "estimated_extra_cost_if_crossed": 800
}
```

This object is consumed directly by P07 and P19.

---

## 7. API Contracts

### 7.1 `POST /api/v1/estimates/electricity`

Request:
```json
{
  "provider_code": "lesco",
  "units": 312,
  "phase_type": "single_phase",
  "connection_type": "residential",
  "protected_customer": false,
  "include_taxes": true,
  "arrears": 0
}
```

Response:
```json
{
  "provider_code": "lesco",
  "utility_type": "electricity",
  "units": 312,
  "estimated_total": 4280,
  "currency": "PKR",
  "tariff_version": "2025-Q2",
  "breakdown": [
    { "label": "0-100", "units": 100, "rate": 7.74, "amount": 774 },
    { "label": "101-200", "units": 100, "rate": 10.06, "amount": 1006 },
    { "label": "201-300", "units": 100, "rate": 16.80, "amount": 1680 },
    { "label": "301-400", "units": 12, "rate": 20.15, "amount": 242 }
  ],
  "taxes": 578,
  "slab_warning": {
    "current_slab": "301-400",
    "next_slab_threshold": 401,
    "units_to_next_slab": 89,
    "estimated_extra_cost_if_crossed": 0
  }
}
```

### 7.2 `POST /api/v1/estimates/gas`

Same response shape with `utility_type = gas` and slab labels in MMBtu.

### 7.3 `POST /api/v1/estimates/from-consumption/{consumer_account_id}`

Auth required. Uses current meter readings from P07 and account metadata from P06. Returns the same estimate response plus `source = "meter_readings"`.

---

## 8. UI Requirements

The estimator screen must show:

1. Utility tabs: Electricity, Gas, Water
2. Provider dropdown
3. Unit input with utility-specific unit label
4. Optional advanced settings accordion
5. Total estimated bill as the largest value on screen
6. Breakdown table
7. Slab progress bar for electricity
8. CTA cards for logged-out users: "Save this estimate by adding your bill"
9. Ad slot below result only; never above input form

---

## 9. Edge Cases

| Case | Required Behavior |
|------|-------------------|
| No tariff found | Return 503 with `TARIFF_NOT_CONFIGURED` |
| Units below zero | Return 422 |
| Units unusually high | Allow but show warning after 2000 kWh |
| Protected/lifeline mismatch | Apply lifeline only when units <= policy threshold |
| Tariff date overlap | Backend must fail startup tariff validation |
| Manual arrears | Add as separate line item, never merge with energy charges |

---

## 10. Acceptance Criteria

- Electricity estimate works for LESCO and K-Electric before public launch.
- Gas estimate works for SNGPL and SSGC before public launch.
- Every estimate returns total, breakdown, taxes, tariff version, and slab warning.
- P07 can call the estimator without duplicating tariff logic.
- Public `/estimate` pages render without auth and are indexable.
- All tariff calculations are covered by unit tests with fixed example inputs.
