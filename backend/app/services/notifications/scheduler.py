"""Notification scheduler — generic check-and-send logic for P19."""

import logging
from datetime import datetime, timezone
from typing import Callable

from app.core.supabase import supabase
from app.services.notifications.preferences import is_enabled, is_rate_limited
from app.services.notifications.templates import render_template
from app.services.notifications.webpush import push_service

logger = logging.getLogger("sahulat.notifications.scheduler")


def get_active_subscriptions(user_id: str) -> list[dict]:
    """Get all active push subscriptions for a user."""
    result = (
        supabase.table("push_subscriptions")
        .select("endpoint, p256dh, auth")
        .eq("user_id", user_id)
        .eq("is_active", True)
        .execute()
    )
    return [
        {
            "endpoint": sub["endpoint"],
            "keys": {
                "p256dh": sub["p256dh"],
                "auth": sub["auth"],
            },
        }
        for sub in (result.data or [])
    ]


def mark_subscription_inactive(endpoint: str):
    """Mark a push subscription as inactive (called on 404/410)."""
    supabase.table("push_subscriptions").update({"is_active": False}).eq("endpoint", endpoint).execute()


def log_notification_event(
    user_id: str,
    category: str,
    event_type: str,
    title: str | None = None,
    body: str | None = None,
    url: str | None = None,
    error_message: str | None = None,
    push_subscription_id: str | None = None,
):
    """Log a notification event to the database."""
    supabase.table("notification_events").insert({
        "user_id": user_id,
        "category": category,
        "event_type": event_type,
        "title": title,
        "body": body,
        "url": url,
        "error_message": error_message,
        "push_subscription_id": push_subscription_id,
    }).execute()


def check_and_send_notifications(
    category: str,
    eligible_user_ids: list[str],
    template_kwargs_fn: Callable[[str], dict | None],
    rate_limit_per_day: int = 2,
):
    """Generic notification dispatch.

    Args:
        category: Notification category (e.g. 'bill_due', 'outage')
        eligible_user_ids: List of user IDs to consider
        template_kwargs_fn: Callable(user_id) -> dict of template kwargs or None to skip
        rate_limit_per_day: Max notifications per day for this category
    """
    if not push_service.is_configured():
        logger.warning("Web Push not configured — skipping %s notifications", category)
        return

    for user_id in eligible_user_ids:
        try:
            if not is_enabled(user_id, category):
                continue

            if is_rate_limited(user_id, category, rate_limit_per_day):
                continue

            kwargs = template_kwargs_fn(user_id)
            if kwargs is None:
                continue

            payload = render_template(category, **kwargs)

            subscriptions = get_active_subscriptions(user_id)
            if not subscriptions:
                continue

            # Send one at a time so we can map results back to endpoints
            for sub in subscriptions:
                sub_result = push_service.send_notification(sub, payload)
                event_type = "sent" if sub_result.success else "failed"
                log_notification_event(
                    user_id=user_id,
                    category=category,
                    event_type=event_type,
                    title=payload["title"],
                    body=payload["body"],
                    url=payload["url"],
                    error_message=sub_result.error,
                )

                if not sub_result.success and sub_result.status_code in (404, 410):
                    mark_subscription_inactive(sub["endpoint"])

            logger.info(
                "Sent %d %s notification(s) for user %s",
                len(subscriptions),
                category,
                user_id,
            )

        except Exception as e:
            logger.error("Failed to send %s notification for user %s: %s", category, user_id, e)
            log_notification_event(
                user_id=user_id,
                category=category,
                event_type="failed",
                error_message=str(e),
            )


def get_users_with_upcoming_bills(days_ahead: int = 3) -> list[dict]:
    """Find users with bills due in N days."""
    from datetime import date, timedelta

    target_date = (date.today() + timedelta(days=days_ahead)).isoformat()
    result = (
        supabase.table("bills")
        .select("user_id, amount_payable, due_date, consumer_accounts!inner(provider_code)")
        .eq("status", "unpaid")
        .eq("due_date", target_date)
        .execute()
    )
    rows = result.data or []
    # Extract provider_code from consumer_accounts joined data
    for row in rows:
        ca = row.get("consumer_accounts") or {}
        row["provider_code"] = ca.get("provider_code", "")
    return rows


def get_users_with_bills_due_today() -> list[dict]:
    """Find users with bills due today."""
    from datetime import date

    today = date.today().isoformat()
    result = (
        supabase.table("bills")
        .select("user_id, amount_payable, due_date, consumer_accounts!inner(provider_code)")
        .eq("status", "unpaid")
        .eq("due_date", today)
        .execute()
    )
    rows = result.data or []
    for row in rows:
        ca = row.get("consumer_accounts") or {}
        row["provider_code"] = ca.get("provider_code", "")
    return rows


def get_users_at_budget_threshold(threshold: float = 0.8) -> list[dict]:
    """Find users who have crossed a budget threshold (0.8 = 80%, 1.0 = 100%)."""
    from app.services.budget.calculator import get_monthly_summary

    now = datetime.now(timezone.utc)
    month = now.strftime("%Y-%m")

    profiles = supabase.table("profiles").select("id").execute()
    results = []
    for p in (profiles.data or []):
        try:
            summary = get_monthly_summary(p["id"], month)
            for cat in summary.get("categories", []):
                if cat["limit"] > 0:
                    ratio = cat["actual"] / cat["limit"]
                    if threshold == 0.8 and 0.8 <= ratio < 1.0:
                        results.append({
                            "user_id": p["id"],
                            "category": cat["label"],
                            "percent": round(ratio * 100),
                        })
                    elif threshold == 1.0 and ratio >= 1.0:
                        results.append({
                            "user_id": p["id"],
                            "category": cat["label"],
                            "percent": round(ratio * 100),
                        })
        except Exception:
            continue
    return results


def get_users_with_upcoming_outages(minutes_ahead: int = 15) -> list[dict]:
    """Find users with scheduled outages starting within N minutes."""
    from datetime import datetime, timedelta

    now = datetime.now(timezone.utc)
    window_start = now.isoformat()
    window_end = (now + timedelta(minutes=minutes_ahead)).isoformat()

    # Get outage schedules with their feeder names
    schedules = (
        supabase.table("outage_schedules")
        .select("feeder_name, start_time, end_time, schedule_date")
        .gte("schedule_date", now.date().isoformat())
        .execute()
    )
    # Match against user feeders to find affected users
    results = []
    for sch in (schedules.data or []):
        feeder_name = sch.get("feeder_name", "")
        if not feeder_name:
            continue
        # Find users who have this feeder set up
        user_feeders = (
            supabase.table("consumer_accounts")
            .select("user_id")
            .eq("feeder_name", feeder_name)
            .eq("is_active", True)
            .execute()
        )
        for uf in (user_feeders.data or []):
            results.append({
                "user_id": uf["user_id"],
                "feeder_name": feeder_name,
                "start_time": sch.get("start_time", ""),
                "end_time": sch.get("end_time", ""),
            })
    return results
