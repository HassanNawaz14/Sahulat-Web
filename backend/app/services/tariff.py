from datetime import date, datetime
from typing import Optional

from dateutil.relativedelta import relativedelta

from app.core.supabase import supabase

PROTECTED_SLABS = [
    {"min": 0,   "max": 100, "rate": 7.74},
    {"min": 101, "max": 200, "rate": 13.01},
]

UNPROTECTED_SLABS = [
    {"min": 0,   "max": 100, "rate": 22.44},
    {"min": 101, "max": 200, "rate": 28.91},
    {"min": 201, "max": 300, "rate": 33.10},
    {"min": 301, "max": 400, "rate": 36.46},
    {"min": 401, "max": 500, "rate": 38.95},
    {"min": 501, "max": 600, "rate": 40.22},
    {"min": 601, "max": 700, "rate": 41.85},
    {"min": 701, "max": None, "rate": 47.20},
]

FALLBACK_SLABS = {
    "protected": PROTECTED_SLABS,
    "unprotected": UNPROTECTED_SLABS,
}

# When a DB row has an older effective_date than this, ignore it —
# our hardcoded rates supersede stale seed data.
HARDCODED_EFFECTIVE_DATE = date(2026, 6, 22)


def _is_protected_consumer(consumer_account_id: str) -> bool:
    """Check if consumer's last 6 bills all had under 200 units (protected status)."""
    result = (
        supabase.table("bills")
        .select("units_consumed")
        .eq("consumer_account_id", consumer_account_id)
        .not_.is_("units_consumed", "null")
        .order("billing_month", desc=True)
        .limit(6)
        .execute()
    )
    bills = result.data or []
    if len(bills) < 6:
        return False
    return all(float(b["units_consumed"]) < 200 for b in bills)


def get_active_tariffs(
    provider_code: str = "lesco",
    category: str = "unprotected",
    as_of: date | None = None,
) -> list[dict]:
    as_of = as_of or date.today()
    db_cat = "protected" if category == "protected" else "residential"
    result = (
        supabase.table("electricity_tariffs")
        .select("*")
        .eq("category", db_cat)
        .lte("effective_date", as_of.isoformat())
        .order("effective_date", desc=True)
        .limit(100)
        .execute()
    )
    rows = result.data or []

    if rows:
        latest_effective = rows[0]["effective_date"]
        if isinstance(latest_effective, str):
            latest_effective = date.fromisoformat(latest_effective)
        # Only use DB data if it's newer than our hardcoded rates
        if latest_effective >= HARDCODED_EFFECTIVE_DATE:
            slabs = [r for r in rows if str(r["effective_date"]) == str(latest_effective)]
            slabs.sort(key=lambda s: s["slab_min"])
            return [
                {"min": s["slab_min"], "max": s["slab_max"], "rate": float(s["rate_per_unit"])}
                for s in slabs
            ]

    # Fallback to hardcoded rates (ours are more current than stale DB seed data)
    return FALLBACK_SLABS.get(category, UNPROTECTED_SLABS)


def get_current_slab(units: float, slabs: list[dict] | None = None) -> dict | None:
    if slabs is None:
        slabs = get_active_tariffs()
    for slab in slabs:
        if slab["min"] <= units <= (slab["max"] if slab["max"] is not None else float("inf")):
            return slab
    return slabs[-1] if slabs else None


def get_next_slab(current_slab: dict, slabs: list[dict] | None = None) -> dict | None:
    if slabs is None:
        slabs = get_active_tariffs()
    for i, slab in enumerate(slabs):
        if slab["min"] == current_slab["min"] and slab["max"] == current_slab["max"]:
            return slabs[i + 1] if i + 1 < len(slabs) else None
    return None


def compute_electricity_bill(
    units: float,
    provider_code: str = "lesco",
    category: str = "unprotected",
) -> dict:
    slabs = get_active_tariffs(provider_code, category)
    energy_charges = 0.0
    remaining = units
    applied_slabs = []
    for slab in slabs:
        if remaining <= 0:
            break
        slab_max = slab["max"] if slab["max"] is not None else float("inf")
        effective_min = max(slab["min"], 1)
        slab_units = min(remaining, slab_max - effective_min + 1)
        slab_cost = round(slab_units * slab["rate"], 2)
        energy_charges += slab_cost
        applied_slabs.append({
            "slab": f"{slab['min']}-{slab['max'] if slab['max'] else '+'}",
            "units": slab_units,
            "rate": slab["rate"],
            "cost": slab_cost,
        })
        remaining -= slab_units

    fc_surcharge = round(energy_charges * 0.071, 2)
    gst = round((energy_charges + fc_surcharge) * 0.18, 2)
    meter_rent = 35.0
    total = round(energy_charges + fc_surcharge + gst + meter_rent, 2)
    current_slab = get_current_slab(units, slabs)

    return {
        "units": units,
        "energy_charges": energy_charges,
        "fc_surcharge": fc_surcharge,
        "gst": gst,
        "meter_rent": meter_rent,
        "total": total,
        "slabs": applied_slabs,
        "current_slab": current_slab,
    }


def compute_marginal_cost(units: float, slabs: list[dict] | None = None) -> float:
    if slabs is None:
        slabs = get_active_tariffs()
    current = get_current_slab(units, slabs)
    if current is None or current["max"] is None:
        return 0.0
    next_s = get_next_slab(current, slabs)
    if next_s is None:
        return 0.0
    cost_staying = units * current["rate"]
    cost_crossing = (units + 1) * next_s["rate"]
    return round(cost_crossing - cost_staying, 2)


def get_cycle_start(account: dict, last_bill: dict | None = None) -> date:
    if last_bill and last_bill.get("billing_month"):
        bill_mo = date.fromisoformat(last_bill["billing_month"])
        return bill_mo + relativedelta(months=1)
    return date.today().replace(day=1)


def get_tariff_slab_label(units: float, provider_code: str = "lesco") -> str:
    slabs = get_active_tariffs(provider_code)
    slab = get_current_slab(units, slabs)
    if slab:
        return f"{slab['min']}-{slab['max'] if slab['max'] else '+'}"
    return f"{units} units"
