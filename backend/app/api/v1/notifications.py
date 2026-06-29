"""P19 Notifications & Alerts — API endpoints."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.auth import get_current_user
from app.core.supabase import supabase
from app.services.notifications.preferences import (
    get_user_preferences,
    seed_default_preferences,
    upsert_preference,
)
from app.services.notifications.webpush import push_service

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


# ─── Schemas ──────────────────────────────────────────────────────────────────


class PushSubscriptionBody(BaseModel):
    endpoint: str
    p256dh: str
    auth: str
    user_agent: str | None = None


class PreferenceItem(BaseModel):
    category: str
    enabled: bool = True
    channels: dict = {"push": True, "sms": False}


class UpdatePreferencesBody(BaseModel):
    preferences: list[PreferenceItem]


# ─── Endpoints ────────────────────────────────────────────────────────────────


@router.post("/subscribe")
async def subscribe_push(
    body: PushSubscriptionBody,
    current_user: dict = Depends(get_current_user),
):
    """Store a push subscription for the current user."""
    user_id = current_user["user_id"]

    # Check for existing subscription by endpoint
    existing = (
        supabase.table("push_subscriptions")
        .select("id")
        .eq("endpoint", body.endpoint)
        .maybe_single()
        .execute()
    )

    payload = {
        "user_id": user_id,
        "endpoint": body.endpoint,
        "p256dh": body.p256dh,
        "auth": body.auth,
        "user_agent": body.user_agent,
        "is_active": True,
        "last_used_at": datetime.utcnow().isoformat(),
    }

    if existing.data:
        supabase.table("push_subscriptions").update(payload).eq("id", existing.data["id"]).execute()
    else:
        supabase.table("push_subscriptions").insert(payload).execute()

    return {"status": "ok"}


@router.post("/unsubscribe")
async def unsubscribe_push(
    body: PushSubscriptionBody,
    current_user: dict = Depends(get_current_user),
):
    """Remove a push subscription."""
    user_id = current_user["user_id"]
    supabase.table("push_subscriptions").update({"is_active": False}).eq(
        "endpoint", body.endpoint
    ).eq("user_id", user_id).execute()
    return {"status": "ok"}


@router.get("/preferences")
async def list_preferences(current_user: dict = Depends(get_current_user)):
    """Get all notification preferences for the current user."""
    user_id = current_user["user_id"]
    seed_default_preferences(user_id)
    return {"preferences": get_user_preferences(user_id)}


@router.put("/preferences")
async def update_preferences(
    body: UpdatePreferencesBody,
    current_user: dict = Depends(get_current_user),
):
    """Update notification preferences."""
    user_id = current_user["user_id"]
    results = []
    for pref in body.preferences:
        result = upsert_preference(
            user_id=user_id,
            category=pref.category,
            enabled=pref.enabled,
            channels=pref.channels,
        )
        results.append(result)
    return {"preferences": results}


@router.post("/test")
async def send_test_notification(current_user: dict = Depends(get_current_user)):
    """Send a test notification to the current user's active subscriptions."""
    user_id = current_user["user_id"]

    if not push_service.is_configured():
        raise HTTPException(503, detail="Web Push not configured — set VAPID keys")

    result = (
        supabase.table("push_subscriptions")
        .select("*")
        .eq("user_id", user_id)
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
            "user_id": user_id,
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
                supabase.table("push_subscriptions").update({"is_active": False}).eq(
                    "id", sub["id"]
                ).execute()

    return {"status": "ok", "sent": sent, "failed": failed}
