"""Notification preference management for P19."""

from datetime import datetime, timezone

from app.core.supabase import supabase

RATE_LIMITS = {
    "bill_due": 2,
    "outage": 2,
    "slab": 1,
    "community": 3,
    "budget": 2,
    "solar": 1,
}

DEFAULT_CATEGORIES = [
    "bill_due",
    "outage",
    "slab",
    "budget",
    "solar",
    "community",
]


def get_user_preferences(user_id: str) -> list[dict]:
    """Get all notification preferences for a user."""
    result = (
        supabase.table("notification_preferences")
        .select("*")
        .eq("user_id", user_id)
        .order("category")
        .execute()
    )
    return result.data or []


def get_preference(user_id: str, category: str) -> dict | None:
    """Get a single notification preference by category."""
    result = (
        supabase.table("notification_preferences")
        .select("*")
        .eq("user_id", user_id)
        .eq("category", category)
        .maybe_single()
        .execute()
    )
    return result.data


def upsert_preference(user_id: str, category: str, enabled: bool, channels: dict | None = None) -> dict:
    """Upsert a single notification preference."""
    payload = {
        "user_id": user_id,
        "category": category,
        "enabled": enabled,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    if channels is not None:
        payload["channels"] = channels

    result = (
        supabase.table("notification_preferences")
        .upsert(payload, on_conflict=["user_id", "category"])
        .execute()
    )
    return result.data[0] if result.data else {}


def seed_default_preferences(user_id: str):
    """Seed default notification preferences for a new user."""
    existing = get_user_preferences(user_id)
    existing_categories = {p["category"] for p in existing}

    to_insert = [
        {"user_id": user_id, "category": cat, "enabled": True, "channels": {"push": True, "sms": False}}
        for cat in DEFAULT_CATEGORIES
        if cat not in existing_categories
    ]

    if to_insert:
        supabase.table("notification_preferences").insert(to_insert).execute()


def is_enabled(user_id: str, category: str) -> bool:
    """Check if a notification category is enabled for a user."""
    pref = get_preference(user_id, category)
    return pref["enabled"] if pref else True


def is_rate_limited(user_id: str, category: str) -> bool:
    """Check if user has exceeded the daily notification limit for a category."""
    from datetime import datetime, timezone

    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    max_per_day = RATE_LIMITS.get(category, 2)

    result = (
        supabase.table("notification_events")
        .select("id", count="exact")
        .eq("user_id", user_id)
        .eq("category", category)
        .eq("event_type", "sent")
        .gte("created_at", today_start)
        .execute()
    )
    count = result.count or 0
    return count >= max_per_day
