from fastapi import FastAPI, BackgroundTasks
from fastapi.routing import APIRoute
import pytz
from datetime import datetime

from app.core.auth import get_current_user
from app.core.supabase import supabase
from app.core.config import settings
from app.services.notifications.scheduler import (
    get_users_with_upcoming_bills,
    get_users_with_bills_due_today,
    get_users_at_budget_threshold,
)
from app.services.notifications.preferences import get_user_preferences, seed_default_preferences
from app.services.notifications.scheduler import check_and_send_notifications
from app.services.notifications.templates import render_template

app = FastAPI()

# Schedule notification checks at specific times
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Create scheduler
from app.core.config import settings

app.add_event_handler("startup", start_scheduler)

# ─── Helper functions ─────────────────────────────────────────────────────────────

async def check_bill_due_notifications():
    """Check bills due in 3 days and today, send notifications."""
    # Bills due in 3 days
    upcoming = get_users_with_upcoming_bills(days_ahead=3)
    user_ids_3d = list({b["user_id"] for b in upcoming})

    def kwargs_fn_3d(uid: str):
        user_bills = [b for b in upcoming if b["user_id"] == uid]
        if not user_bills:
            return None
        bill = user_bills[0]
        return {
            "provider": bill.get("provider_code", "").upper(),
            "amount": str(bill.get("amount_payable", 0)),
            "due_date": bill.get("due_date", ""),
        }

    check_and_send_notifications("bill_due_3_days", user_ids_3d, kwargs_fn_3d, rate_limit_per_day=2)

    # Bills due today
    due_today = get_users_with_bills_due_today()
    user_ids_today = list({b["user_id"] for b in due_today})

    def kwargs_fn_today(uid: str):
        user_bills = [b for b in due_today if b["user_id"] == uid]
        if not user_bills:
            return None
        bill = user_bills[0]
        return {
            "provider": bill.get("provider_code", "").upper(),
            "amount": str(bill.get("amount_payable", 0)),
        }

    check_and_send_notifications("bill_due_today", user_ids_today, kwargs_fn_today, rate_limit_per_day=2)


async def check_outage_notifications():
    """Check for outages starting in 15 minutes."""
    from app.services.notifications.scheduler import get_users_with_upcoming_outages

    users = get_users_with_upcoming_outages(minutes_ahead=15)
    user_ids = list({u["user_id"] for u in users})

    def kwargs_fn(uid: str):
        users_for_uid = [u for u in users if u["user_id"] == uid]
        if not users_for_uid:
            return None
        u = users_for_uid[0]
        return {
            "feeder_name": u.get("feeder_name", ""),
            "start_time": u.get("start_time", ""),
            "end_time": u.get("end_time", ""),
        }

    check_and_send_notifications("scheduled_outage_15_min", user_ids, kwargs_fn, rate_limit_per_day=1)


async def check_slab_boundary():
    """Check slab boundary users for notifications."""
    from app.services.notifications.scheduler import get_users_at_budget_threshold

    warning_users = get_users_at_budget_threshold(0.8)

    def kwargs_fn_80(uid: str):
        matches = [u for u in warning_users if u["user_id"] == uid]
        if not matches:
            return None
        m = matches[0]
        return {"percent": str(m["percent"]), "category": m["category"]}

    warning_ids = list({u["user_id"] for u in warning_users})
    check_and_send_notifications("slab_boundary", warning_ids, kwargs_fn_80, rate_limit_per_day=1)


# ─── Scheduled Jobs ─────────────────────────────────────────────────────────────────

async def schedule_notification_jobs():
    """Schedule notification jobs with proper timing."""
    from datetime import datetime, time, timedelta

    from app.core.supabase import supabase

    scheduler = AsyncIOScheduler()

    # Bill due notifications - daily at 08:00 PKT
    async def run_bill_due():
        await check_bill_due_notifications()
        await log_job_run("bill_due")

    async def run_budget_alerts():
        await check_budget_alerts()
        await log_job_run("budget_alerts")

    async def run_slab_boundary():
        await check_slab_boundary()
        await log_job_run("slab_boundary")

    async def run_outage_notifications():
        await check_outage_notifications()
        await log_job_run("outage")

    # Convert PKT times to UTC for scheduling
    def pakt_to_utc(hour, minute=0):
        pakt = pytz.timezone("Asia/Karachi")
        utc = pytz.UTC

        today = datetime.now(pakt)
        target = today.replace(hour=hour, minute=minute, second=0, microsecond=0)
        target_utc = target.astimezone(utc)

        # Schedule for today if it hasn't passed, otherwise tomorrow
        now_utc = datetime.now(utc)
        if target_utc > now_utc:
            return target_utc
        else:
            tomorrow = target_utc + timedelta(days=1)
            return tomorrow

    # Schedule bill due notifications (daily at 08:00 PKT)
    next_bill_due = pakt_to_utc(8)
    scheduler.add_job(run_bill_due, trigger='date', run_date=next_bill_due)

    # Schedule budget alerts (daily at 21:00 PKT)
    next_budget_alerts = pakt_to_utc(21)
    scheduler.add_job(run_budget_alerts, trigger='date', run_date=next_budget_alerts)

    # Schedule slab boundary (daily at 20:00 PKT)
    next_slab_boundary = pakt_to_utc(20)
    scheduler.add_job(run_slab_boundary, trigger='date', run_date=next_slab_boundary)

    # Schedule outage notifications (every 15 minutes)
    def next_15_minutes():
        now = datetime.utcnow()
        minute = ((now.minute // 15) + 1) * 15
        if minute >= 60:
            next_time = now.replace(hour=now.hour + 1, minute=0, second=0)
        else:
            next_time = now.replace(minute=minute, second=0)
        return next_time

    next_outage = next_15_minutes()
    scheduler.add_job(run_outage_notifications, trigger='date', run_date=next_outage)

    await scheduler.start()


async def log_job_run(job_name: str):
    """Log a job run to the database."""
    supabase.table("scraper_run_log").insert({
        "job_type": "notification",
        "target_id": job_name,
        "status": "success",
    }).execute()


def start_scheduler():
    """Initialize and start the scheduler."""
    import asyncio

    async def _start():
        await schedule_notification_jobs()

    asyncio.create_task(_start())


# ─── API Endpoints ───────────────────────────────────────────────────────────────

from fastapi import APIRouter, Depends, HTTPException
from fastapi import Request
from typing import List
from app.core.config import settings

router = APIRouter(prefix="/api/v1")


@router.get("/notifications/budget-summary")
async def get_budget_summary(
    month: str,
    current_user: dict = Depends(get_current_user)
):
    """Get budget summary for a specific month."""
    from app.services.budget.calculator import get_monthly_summary

    summary = get_monthly_summary(current_user["user_id"], month)

    # Override notification preferences for budget alerts
    prefs = get_user_preferences(current_user["user_id"]) or []
    prefs_dict = {p["category"]: p for p in prefs}

    for category in summary["categories"]:
        if prefs_dict.get("budget", {}).get("enabled"):
            status = calculate_budget_status(category["actual"], category["limit"])
            category["budget_status"] = status

    return summary


@router.get("/notifications/preferences")
async def list_notification_preferences(current_user: dict = Depends(get_current_user)):
    """Get notification preferences for the current user."""
    seed_default_preferences(current_user["user_id"])
    prefs = get_user_preferences(current_user["user_id"]) or []
    return {"preferences": prefs}


@router.post("/notifications/preferences")
async def update_notification_preferences(
    body: List[dict],
    current_user: dict = Depends(get_current_user)
):
    """Update notification preferences."""
    from app.services.notifications.preferences import upsert_preference

    results = []
    for pref in body:
        result = upsert_preference(
            user_id=current_user["user_id"],
            category=pref["category"],
            enabled=pref.get("enabled", True),
            channels=pref.get("channels", {"push": True, "sms": False})
        )
        results.append(result)

    return {"preferences": results}


@router.post("/notifications/test")
async def send_test_notification(current_user: dict = Depends(get_current_user)):
    """Send a test notification to the user."""
    from app.services.notifications.webpush import push_service
    from app.core.config import settings

    if not push_service.is_configured():
        raise HTTPException(503, detail="Web Push not configured — set VAPID keys")

    result = (
        supabase.table("push_subscriptions")
        .select("*")
        .eq("user_id", current_user["user_id"])
        .eq("is_active", True)
        .execute()
    )
    subscriptions = result.data or []
    if not subscriptions:
        raise HTTPException(404, detail="No active push subscriptions found. Subscribe first.")

    test_payload = {
        "title": "Sahulat Test Notification",
        "body": "Your notification settings are working correctly!",
        "url": "/settings/notifications",
    }

    sent = 0
    failed = 0
    for sub in subscriptions:
        sub_info = {
            "endpoint": sub["endpoint"],
            "keys": {"p256dh": sub["p256dh"], "auth": sub["auth"]},
        }
        result = push_service.send_notification(sub_info, test_payload)
        
        supabase.table("notification_events").insert({
            "user_id": current_user["user_id"],
            "category": "test",
            "event_type": "sent" if result.success else "failed",
            "title": test_payload["title"],
            "body": test_payload["body"],
            "url": test_payload["url"],
            "error_message": result.error,
            "push_subscription_id": sub["id"],
        }).execute()

        if result.success:
            sent += 1
            supabase.table("push_subscriptions").update(
                {"last_used_at": datetime.utcnow().isoformat()}
            ).eq("id", sub["id"]).execute()
        else:
            failed += 1
            if result.status_code in (404, 410):
                supabase.table("push_subscriptions").update({
                    "is_active": False
                }).eq("id", sub["id"]).execute()

    return {"status": "ok", "sent": sent, "failed": failed}