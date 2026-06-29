"""Solar alert evaluation engine."""

from datetime import date, timedelta
from typing import Any, List, Optional

from app.core.supabase import supabase


def get_user_alerts(user_id: str, installation_id: str | None = None) -> List[Dict[str, Any]]:
    """Get alerts for a user, optionally filtered by installation."""
    query = (
        supabase.table("solar_alerts")
        .select("*")
        .eq("user_id", user_id)
        .eq("is_dismissed", False)
        .order("created_at", desc=True)
    )
    if installation_id:
        query = query.eq("solar_installation_id", installation_id)
    result = query.execute()
    return result.data or []


def get_user_alerts_for_installation(installation_id: str, user_id: str) -> List[Dict[str, Any]]:
    """Get alerts for a specific installation (user-scoped)."""
    result = (
        supabase.table("solar_alerts")
        .select("*")
        .eq("solar_installation_id", installation_id)
        .eq("user_id", user_id)
        .eq("is_dismissed", False)
        .order("created_at", desc=True)
        .execute()
    )
    return result.data or []


def create_alert(
    installation_id: str,
    user_id: str,
    alert_type: str,
    severity: str,
    title: str,
    message: str,
    production_kwh: Optional[float] = None,
    baseline_kwh: Optional[float] = None,
) -> Dict[str, Any]:
    """Create a new alert."""
    payload = {
        "solar_installation_id": installation_id,
        "user_id": user_id,
        "alert_type": alert_type,
        "severity": severity,
        "title": title,
        "message": message,
        "production_kwh": production_kwh,
        "baseline_kwh": baseline_kwh,
    }

    result = (
        supabase.table("solar_alerts")
        .insert(payload)
        .execute()
    )
    return result.data[0] if result.data else {}


def mark_alert_read(alert_id: str, user_id: str) -> Dict[str, Any]:
    """Mark alert as read."""
    result = (
        supabase.table("solar_alerts")
        .update({"is_read": True})
        .eq("id", alert_id)
        .eq("user_id", user_id)
        .execute()
    )
    return result.data[0] if result.data else {}


def mark_alert_dismissed(alert_id: str, user_id: str) -> Dict[str, Any]:
    """Dismiss alert."""
    result = (
        supabase.table("solar_alerts")
        .update({"is_dismissed": True})
        .eq("id", alert_id)
        .eq("user_id", user_id)
        .execute()
    )
    return result.data[0] if result.data else {}


def check_health_alerts(
    installation_id: str,
    user_id: str,
    today: date,
    system_size_kw: float,
    last_14_days_production: List[Dict[str, Any]],
    hours_since_last_sync: int,
) -> List[Dict[str, Any]]:
    """Check for health alerts based on current conditions."""
    alerts_to_create = []

    if last_14_days_production:
        base_production = calculate_sunny_baseline(system_size_kw, last_14_days_production)
        if base_production > 0 and last_14_days_production[-1]["production_kwh"] / base_production < 0.7:
            alerts_to_create.append(
                create_alert(
                    installation_id,
                    user_id,
                    "baseline_drop",
                    "warning" if last_14_days_production[-1]["production_kwh"] / base_production > 0.3 else "critical",
                    f"Production drop to {last_14_days_production[-1]['production_kwh']} kWh",
                    f"Production is {((1 - last_14_days_production[-1]['production_kwh'] / base_production) * 100):.0f}% below sunny baseline",
                    production_kwh=last_14_days_production[-1]["production_kwh"],
                    baseline_kwh=base_production,
                )
            )

    if last_14_days_production:
        today_production = next((p for p in last_14_days_production if p["date"] == today.isoformat()), None)
        if today_production and today_production["production_kwh"] == 0 and today.hour >= 11:
            alerts_to_create.append(
                create_alert(
                    installation_id,
                    user_id,
                    "zero_production",
                    "critical",
                    "Zero production recorded",
                    f"No production recorded after 11:00 AM on {today.isoformat()}",
                    production_kwh=0,
                )
            )

    if hours_since_last_sync > 24:
        alerts_to_create.append(
            create_alert(
                installation_id,
                user_id,
                "inverter_disconnected",
                "warning",
                "Inverter disconnected",
                f"Inverter connection lost {hours_since_last_sync} hours ago",
            )
        )

    return alerts_to_create


def calculate_sunny_baseline(system_size_kw: float, last_14_days_production: List[Dict[str, Any]]) -> float:
    """Calculate sunny-day production baseline."""
    if not last_14_days_production:
        return system_size_kw * 3.5

    total = 0
    count = 0
    for p in last_14_days_production:
        if p["production_kwh"] >= system_size_kw * 3.5:
            total += p["production_kwh"]
            count += 1

    if count == 0:
        return system_size_kw * 3.5

    return total / count


def cleanup_old_alerts():
    """Clean up old resolved alerts."""
    # Resolve alerts that are no longer relevant
    supabase.table("solar_alerts").update({"resolved_at": date.today().isoformat()}).eq("resolved_at", None).execute()


def get_cleaning_reminder_days(system_size_kw: float) -> int:
    """Get days until next cleaning reminder based on system size."""
    if system_size_kw >= 15:
        return 30
    elif system_size_kw >= 10:
        return 35
    else:
        return 45
