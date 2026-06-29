"""Normalizing and calculating solar production."""

from datetime import date, datetime
from typing import Any, Dict


def calculate_savings(
    production_data: list[Dict[str, Any]],
    system_size_kw: float,
    effective_import_rate: float,
    net_metering_enabled: bool = True,
) -> Dict[str, Any]:
    """Calculate monthly savings from production data."""
    if not production_data:
        return {
            "monthly_savings": 0,
            "self_consumed_value": 0,
            "export_credit": 0,
        }

    # Calculate total production for the current month
    month_days = 30
    daily_production = sum(p["production_kwh"] for p in production_data) / month_days

    # Split between self-consumed and exported (60/40 default)
    self_consumed_kwh = daily_production * 0.6
    exported_kwh = daily_production * 0.4

    # Calculate values
    self_consumed_value = self_consumed_kwh * effective_import_rate
    export_credit = exported_kwh * 27 if net_metering_enabled else 0

    return {
        "monthly_savings": self_consumed_value + export_credit,
        "self_consumed_value": self_consumed_value,
        "export_credit": export_credit,
    }


def get_cleaning_reminder_days(system_size_kw: float) -> int:
    """Get days until next cleaning reminder based on system size."""
    if system_size_kw >= 15:
        return 30
    elif system_size_kw >= 10:
        return 35
    else:
        return 45


def check_health_alerts(
    installation: Dict[str, Any],
    last_14_days_production: list[Dict[str, Any]],
    today: date,
) -> list[Dict[str, Any]]:
    """Check for health alerts based on production data."""
    alerts = []

    if not last_14_days_production:
        return alerts

    system_size_kw = installation.get("system_size_kw", 10)
    base_production = calculate_sunny_baseline(system_size_kw, last_14_days_production)

    # Check baseline drop (30% below sunny baseline)
    today_production = next((p for p in last_14_days_production if p["date"] == today.isoformat()), None)
    if today_production and base_production > 0:
        production_ratio = today_production["production_kwh"] / base_production
        if production_ratio < 0.7:
            alerts.append(
                {
                    "type": "baseline_drop",
                    "severity": "warning" if production_ratio > 0.3 else "critical",
                    "message": f"Production dropped by {(1 - production_ratio) * 100:.0f}% below baseline",
                    "production_kwh": today_production["production_kwh"],
                    "baseline_kwh": base_production,
                }
            )

    if today_production and today_production["production_kwh"] == 0 and datetime.now().hour >= 11:
        alerts.append(
            {
                "type": "zero_production",
                "severity": "critical",
                "message": f"No production recorded after 11:00 AM on {today.isoformat()}",
                "production_kwh": 0,
            }
        )

    return alerts


def calculate_sunny_baseline(system_size_kw: float, production_data: list[Dict[str, Any]]) -> float:
    """Calculate average production on sunny days (production >= system_size_kw * 3.5)."""
    sunny_days = [p for p in production_data if p["production_kwh"] >= system_size_kw * 3.5]
    if not sunny_days:
        return system_size_kw * 3.5

    return sum(p["production_kwh"] for p in sunny_days) / len(sunny_days)


def calculate_roi(
    system_cost_pkr: float,
    monthly_savings: float,
    commissioning_date: date,
) -> Dict[str, Any]:
    """Calculate ROI based on system cost and monthly savings."""
    today = date.today()

    months_elapsed = (today.year - commissioning_date.year) * 12 + (today.month - commissioning_date.month)
    if months_elapsed < 0:
        months_elapsed = 0

    amount_paid_back = monthly_savings * months_elapsed
    roi_percent = (amount_paid_back / system_cost_pkr * 100) if system_cost_pkr > 0 else 0

    months_remaining = 0
    if monthly_savings > 0 and system_cost_pkr > amount_paid_back:
        months_remaining = int((system_cost_pkr - amount_paid_back) / monthly_savings)

    return {
        "roi_percent": round(roi_percent, 1),
        "amount_paid_back": round(amount_paid_back, 2),
        "months_remaining": months_remaining,
    }
