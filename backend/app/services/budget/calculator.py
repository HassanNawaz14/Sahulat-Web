import calendar
from datetime import date

from app.core.supabase import supabase
from app.services.tariff import compute_electricity_bill

DEFAULT_BUDGET_CATEGORIES = [
    {"code": "electricity", "label": "Electricity", "monthly_limit": 15000},
    {"code": "gas", "label": "Gas", "monthly_limit": 3000},
    {"code": "water", "label": "Water", "monthly_limit": 2000},
    {"code": "internet", "label": "Internet", "monthly_limit": 2500},
    {"code": "cable_tv", "label": "Cable TV", "monthly_limit": 1000},
    {"code": "mobile_data", "label": "Mobile Data", "monthly_limit": 1500},
    {"code": "solar_maintenance", "label": "Solar Maintenance", "monthly_limit": 2000},
    {"code": "groceries", "label": "Groceries", "monthly_limit": 25000},
    {"code": "education", "label": "Education", "monthly_limit": 5000},
    {"code": "other", "label": "Other"},
]

UTILITY_CATEGORIES = {"electricity", "gas", "water", "internet"}


def calculate_budget_status(actual: float, limit: float) -> str:
    if limit <= 0:
        return "safe"
    ratio = actual / limit
    if ratio >= 1.0:
        return "exceeded"
    if ratio >= 0.8:
        return "warning"
    return "safe"


def _billing_month_start(month: str) -> str:
    return f"{month}-01"


def seed_default_categories(user_id: str):
    existing = (
        supabase.table("budget_categories")
        .select("id, code, monthly_limit")
        .eq("user_id", user_id)
        .execute()
    )
    existing_codes = {r["code"] for r in (existing.data or [])}

    # Insert missing default categories (with limits)
    to_insert = [
        {**cat, "user_id": user_id}
        for cat in DEFAULT_BUDGET_CATEGORIES
        if cat["code"] not in existing_codes
    ]
    if to_insert:
        supabase.table("budget_categories").insert(to_insert).execute()

    # Fill NULL limits on existing categories with defaults
    default_by_code = {cat["code"]: cat.get("monthly_limit") for cat in DEFAULT_BUDGET_CATEGORIES}
    for row in (existing.data or []):
        if row.get("monthly_limit") is not None:
            continue
        new_limit = default_by_code.get(row["code"])
        if new_limit is not None:
            supabase.table("budget_categories").update(
                {"monthly_limit": new_limit}
            ).eq("id", row["id"]).execute()


def _estimate_from_readings(account_id: str, provider_code: str, month: str) -> float:
    """Use meter readings to estimate electricity bill for a no-bill month.
    
    Returns estimated total (0 if insufficient data).
    """
    cycle_start = f"{month}-01"
    readings = (
        supabase.table("meter_readings")
        .select("reading_value, units_since_last, reading_date")
        .eq("consumer_account_id", account_id)
        .gte("reading_date", cycle_start)
        .order("reading_date", desc=False)
        .execute()
    )
    rows = readings.data or []
    if not rows:
        return 0.0

    if rows[0].get("units_since_last") is not None and float(rows[0].get("units_since_last") or 0) > 0:
        total = sum(float(r["units_since_last"] or 0) for r in rows)
    else:
        total = float(rows[0]["reading_value"]) + sum(float(r.get("units_since_last") or 0) for r in rows[1:])

    last_r = rows[-1]
    last_date = date.fromisoformat(last_r["reading_date"]) if isinstance(last_r["reading_date"], str) else last_r["reading_date"]
    cycle_start_date = date.fromisoformat(cycle_start)
    days_elapsed = max(1, (last_date - cycle_start_date).days)
    _, total_days = calendar.monthrange(cycle_start_date.year, cycle_start_date.month)
    days_remaining = max(0, total_days - last_date.day)
    daily = total / days_elapsed
    projected_units = round(total + (daily * days_remaining), 2)

    bill = compute_electricity_bill(projected_units, provider_code, "unprotected")
    return bill["total"]


def _bills_for_month(account_ids: list[str], month: str) -> list[dict]:
    """Fetch all non-draft bills for the given month (range query)."""
    month_start = _billing_month_start(month)
    _, last_day = calendar.monthrange(
        int(month[:4]), int(month[5:7])
    )
    month_end = f"{month}-{last_day:02d}"
    result = (
        supabase.table("bills")
        .select("amount_payable, status")
        .in_("consumer_account_id", account_ids)
        .neq("status", "draft")
        .gte("billing_month", month_start)
        .lte("billing_month", month_end)
        .execute()
    )
    return result.data or []


def _last_bill_total(account_ids: list[str]) -> float:
    """Get the sum of the most recent bill amounts across accounts."""
    total = 0.0
    for aid in account_ids:
        last = (
            supabase.table("bills")
            .select("amount_payable")
            .eq("consumer_account_id", aid)
            .neq("status", "draft")
            .order("billing_month", desc=True)
            .limit(1)
            .execute()
        )
        if last.data:
            total += float(last.data[0]["amount_payable"])
    return total


def get_category_spend(user_id: str, category_code: str, month: str) -> dict:
    if category_code in UTILITY_CATEGORIES:
        accounts = (
            supabase.table("consumer_accounts")
            .select("id, provider_code")
            .eq("user_id", user_id)
            .eq("utility_type", category_code)
            .execute()
        )
        account_ids = [a["id"] for a in (accounts.data or [])]
        if not account_ids:
            return {"actual": 0.0, "projected": 0.0}

        bills = _bills_for_month(account_ids, month)
        bill_total = sum(
            float(b["amount_payable"]) for b in bills
        )
        actual = bill_total
        projected = bill_total

        # If no bill exists this month, project from last bill or estimates
        if bill_total == 0:
            if category_code == "electricity":
                for acct in (accounts.data or []):
                    est = _estimate_from_readings(acct["id"], acct["provider_code"], month)
                    if est > 0:
                        projected += est
            if projected == 0:
                projected = _last_bill_total(account_ids)

        return {"actual": actual, "projected": projected}
    else:
        categories = (
            supabase.table("budget_categories")
            .select("id")
            .eq("user_id", user_id)
            .eq("code", category_code)
            .execute()
        )
        if not categories.data:
            return {"actual": 0.0, "projected": 0.0}

        cat_id = categories.data[0]["id"]
        expenses_list = (
            supabase.table("budget_expenses")
            .select("amount")
            .eq("user_id", user_id)
            .eq("category_id", cat_id)
            .gte("expense_date", f"{month_start}")
            .lte("expense_date", f"{month}-31")
            .execute()
        )
        total = sum(float(e["amount"]) for e in (expenses_list.data or []))
        return {"actual": total, "projected": total}


def get_monthly_summary(user_id: str, month: str) -> dict:
    seed_default_categories(user_id)

    categories_list = (
        supabase.table("budget_categories")
        .select("*")
        .eq("user_id", user_id)
        .execute()
    )

    cat_results = []
    total_actual = 0.0
    total_projected = 0.0
    total_limit = 0.0

    for cat in (categories_list.data or []):
        spend = get_category_spend(user_id, cat["code"], month)
        limit_val = float(cat["monthly_limit"] or 0)
        status = calculate_budget_status(spend["actual"], limit_val)

        cat_results.append({
            "code": cat["code"],
            "label": cat["label"],
            "actual": spend["actual"],
            "projected": spend["projected"],
            "limit": limit_val,
            "status": status,
        })

        total_actual += spend["actual"]
        total_projected += spend["projected"]
        total_limit += limit_val

    overall_status = calculate_budget_status(total_actual, total_limit)

    return {
        "month": month,
        "actual_spend": total_actual,
        "projected_spend": total_projected,
        "budget_limit": total_limit,
        "status": overall_status,
        "categories": cat_results,
    }
