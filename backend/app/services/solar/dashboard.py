"""Solar dashboard aggregation service."""

import calendar
from datetime import date, timedelta
from typing import Any, Dict, List

from app.core.supabase import supabase
from app.services.solar.alerts import get_user_alerts_for_installation


def get_installations_list(user_id: str) -> List[Dict[str, Any]]:
    """List all solar installations for a user with quick status."""
    result = (
        supabase.table("solar_installations")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    installations = result.data or []
    today = date.today()

    for inst in installations:
        today_prod = get_production_data(inst["id"], today, today)
        inst["today_kwh"] = today_prod[0]["production_kwh"] if today_prod else 0
        inst["health_status"] = inst.get("health_status", "normal")

    return installations


def get_dashboard_data(installation_id: str, user_id: str) -> Dict[str, Any]:
    """Get complete dashboard data for a solar installation."""
    installation = get_installation(installation_id, user_id)

    today = date.today()
    month_start = date(today.year, today.month, 1)

    production_data = get_production_data(installation_id, month_start, today)
    today_kwh = sum(p["production_kwh"] for p in production_data if p["date"] == today.isoformat())
    month_kwh = sum(p["production_kwh"] for p in production_data)

    chart_data = get_chart_data(installation_id, today, days_back=14)

    savings = estimate_savings(installation_id, production_data, user_id)
    roi_data = calculate_roi(installation_id, production_data, user_id)

    health_status = get_health_status(installation_id, user_id, today)

    alerts = get_user_alerts_for_installation(installation_id, user_id)

    return {
        "installation": installation,
        "today_kwh": today_kwh,
        "month_kwh": month_kwh,
        "estimated_monthly_savings": savings["monthly_savings"],
        "self_consumed_value": savings["self_consumed_value"],
        "export_credit": savings["export_credit"],
        "roi_paid_back_percent": roi_data["roi_percent"],
        "roi_amount_paid_back": roi_data["amount_paid_back"],
        "estimated_payback_months_remaining": roi_data["months_remaining"],
        "health_status": health_status,
        "chart": chart_data,
        "alerts": alerts,
    }


def get_installation(installation_id: str, user_id: str) -> Dict[str, Any]:
    """Get solar installation details."""
    result = (
        supabase.table("solar_installations")
        .select("*")
        .eq("id", installation_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    if not result.data:
        raise Exception("Solar installation not found")
    return result.data


def get_production_data(installation_id: str, start_date: date, end_date: date) -> List[Dict[str, Any]]:
    """Get production data for a date range."""
    result = (
        supabase.table("solar_daily_production")
        .select("date, production_kwh, self_consumed_kwh, exported_kwh, imported_kwh")
        .eq("solar_installation_id", installation_id)
        .gte("date", start_date.isoformat())
        .lte("date", end_date.isoformat())
        .order("date", desc=False)
        .execute()
    )
    return result.data or []


def get_chart_data(installation_id: str, today: date, days_back: int = 14) -> List[Dict[str, Any]]:
    """Get production data for chart."""
    start_date = today - timedelta(days=days_back - 1)
    return get_production_data(installation_id, start_date, today)


def get_cleaning_reminder_days(system_size_kw: float) -> int:
    """Get days until next cleaning reminder based on system size."""
    if system_size_kw >= 15:
        return 30
    elif system_size_kw >= 10:
        return 35
    else:
        return 45


def estimate_savings(installation_id: str, production_data: List[Dict[str, Any]], user_id: str) -> Dict[str, Any]:
    """Estimate monthly savings from production data."""
    if not production_data:
        return {
            "monthly_savings": 0,
            "self_consumed_value": 0,
            "export_credit": 0,
        }

    total_production = sum(p["production_kwh"] for p in production_data)
    month_days = max(len(production_data), 1)
    daily_production = total_production / month_days

    system_size = (
        supabase.table("solar_installations")
        .select("system_size_kw, net_metering_enabled")
        .eq("id", installation_id)
        .single()
        .execute()
    ).data

    # Estimate self-consumed vs exported split (60/40 default)
    self_consumed_kwh = daily_production * 0.6
    exported_kwh = daily_production * 0.4

    effective_import_rate = get_effective_import_rate(installation_id, system_size.get("user_id", ""))

    self_consumed_value = self_consumed_kwh * effective_import_rate
    export_credit = exported_kwh * 27  # NEPRA export rate

    return {
        "monthly_savings": self_consumed_value + export_credit,
        "self_consumed_value": self_consumed_value,
        "export_credit": export_credit,
    }


def get_effective_import_rate(installation_id: str, user_id: str) -> float:
    """Get effective import rate for the user's electricity."""
    consumer_accounts = (
        supabase.table("consumer_accounts")
        .select("id, utility_type")
        .eq("user_id", user_id)
        .execute()
    ).data or []

    if not consumer_accounts:
        return 21.0  # Default fallback rate

    # Get the first electricity account
    electricity_account = next(
        (acc for acc in consumer_accounts if acc["utility_type"] == "electricity"),
        None,
    )
    if not electricity_account:
        return 21.0

    # Fetch current tariff
    from app.services.tariff import get_current_tariff
    try:
        tariff = get_current_tariff(electricity_account["id"])
        return tariff["effective_import_rate"]
    except Exception:
        return 21.0


def calculate_roi(installation_id: str, production_data: List[Dict[str, Any]], user_id: str) -> Dict[str, Any]:
    """Calculate ROI based on production and savings."""
    system_size = (
        supabase.table("solar_installations")
        .select("system_size_kw, system_cost_pkr, commissioning_date")
        .eq("id", installation_id)
        .single()
        .execute()
    ).data

    if not system_size or system_size["system_cost_pkr"] is None:
        return {
            "roi_percent": 0,
            "amount_paid_back": 0,
            "months_remaining": 0,
        }

    system_cost = float(system_size["system_cost_pkr"])
    commissioning_date = system_size["commissioning_date"]

    if not commissioning_date:
        return {
            "roi_percent": 0,
            "amount_paid_back": 0,
            "months_remaining": 0,
        }

    savings = estimate_savings(installation_id, production_data, user_id)
    monthly_savings = savings["monthly_savings"]

    # Calculate months elapsed
    today = date.today()
    commission_dt = date.fromisoformat(commissioning_date.split("T")[0])
    months_elapsed = (today.year - commission_dt.year) * 12 + (today.month - commission_dt.month)
    if months_elapsed < 0:
        months_elapsed = 0

    amount_paid_back = monthly_savings * months_elapsed
    roi_percent = (amount_paid_back / system_cost) * 100 if system_cost > 0 else 0

    months_remaining = 0
    if monthly_savings > 0 and system_cost > amount_paid_back:
        months_remaining = int((system_cost - amount_paid_back) / monthly_savings)

    return {
        "roi_percent": round(roi_percent, 1),
        "amount_paid_back": round(amount_paid_back, 2),
        "months_remaining": months_remaining,
    }


def get_health_status(installation_id: str, user_id: str, today: date) -> str:
    """Get health status for installation."""
    production_data = get_production_data(installation_id, today - timedelta(days=13), today)
    if not production_data:
        return "normal"

    today_production = next((p for p in production_data if p["date"] == today.isoformat()), None)
    if not today_production:
        return "normal"

    system_size = (
        supabase.table("solar_installations")
        .select("system_size_kw")
        .eq("id", installation_id)
        .single()
        .execute()
    ).data

    if not system_size:
        return "normal"

    # Check baseline drop (30% below sunny baseline)
    baseline_production = system_size["system_size_kw"] * 3.5
    if today_production["production_kwh"] / baseline_production < 0.7:
        return "warning"

    # Check zero production after 11 AM
    if today_production["production_kwh"] == 0 and today.hour >= 11:
        return "critical"

    installation = get_installation(installation_id, user_id)
    if installation.get("last_synced_at"):
        last_sync = date.fromisoformat(installation["last_synced_at"].split("T")[0])
        if (today - last_sync).days > 1:
            return "warning"

    return "normal"
