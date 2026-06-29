"""Unit tests for P19 Notifications & Alerts System.

Run: python -m pytest backend/tests/test_notifications.py -v
"""
import sys
sys.path.insert(0, "backend")

from app.services.notifications.templates import (
    NOTIFICATION_TEMPLATES,
    render_template,
)
from app.services.notifications.preferences import (
    DEFAULT_CATEGORIES,
    is_rate_limited,
)


# ─── Template Tests ──────────────────────────────────────────────────────────


def test_notification_templates_count():
    assert len(NOTIFICATION_TEMPLATES) == 10


def test_required_categories_exist():
    required = {
        "bill_due_3_days",
        "bill_due_today",
        "scheduled_outage_15_min",
        "slab_boundary",
        "budget_80_percent",
        "budget_exceeded",
        "nearby_outage_verified",
        "solar_underperformance",
    }
    assert required.issubset(NOTIFICATION_TEMPLATES.keys())


def test_render_bill_due_3_days():
    result = render_template(
        "bill_due_3_days",
        provider="LESCO",
        amount="4,280",
        due_date="2025-07-15",
    )
    assert "LESCO" in result["body"]
    assert "4,280" in result["body"]
    assert "2025-07-15" in result["body"]
    assert result["url"] == "/bills"
    assert len(result["title"]) > 0


def test_render_bill_due_today():
    result = render_template(
        "bill_due_today",
        provider="SNGPL",
        amount="1,200",
    )
    assert "SNGPL" in result["body"]
    assert "1,200" in result["body"]
    assert result["url"] == "/bills"


def test_render_outage_alert():
    result = render_template(
        "scheduled_outage_15_min",
        feeder_name="DHA R-BLOCK",
        start_time="10:00",
        end_time="11:00",
    )
    assert "DHA R-BLOCK" in result["body"]
    assert "10:00" in result["body"]
    assert result["url"] == "/outages"


def test_render_slab_boundary():
    result = render_template(
        "slab_boundary",
        units="290",
        remaining="10",
        rate="20.15",
    )
    assert "290" in result["body"]
    assert "20.15" in result["body"]
    assert result["url"] == "/consumption"


def test_render_budget_80_percent():
    result = render_template(
        "budget_80_percent",
        percent="85",
        category="Electricity",
    )
    assert "85%" in result["body"]
    assert "Electricity" in result["body"]
    assert result["url"] == "/budget"


def test_render_budget_exceeded():
    result = render_template(
        "budget_exceeded",
        category="Gas",
    )
    assert "Gas" in result["body"]
    assert result["url"] == "/budget"


def test_render_nearby_outage():
    result = render_template(
        "nearby_outage_verified",
        count="5",
        utility="electricity",
        area="Gulberg",
    )
    assert "5" in result["body"]
    assert "electricity" in result["body"]
    assert result["url"] == "/outages"


def test_render_solar_underperformance():
    result = render_template(
        "solar_underperformance",
        percent="30",
    )
    assert "30%" in result["body"]
    assert result["url"] == "/solar"


def test_render_unknown_category():
    import pytest
    with pytest.raises(ValueError, match="Unknown notification category"):
        render_template("nonexistent_category")


# ─── Default Categories ──────────────────────────────────────────────────────


def test_default_categories():
    assert "bill_due" in DEFAULT_CATEGORIES
    assert "outage" in DEFAULT_CATEGORIES
    assert "slab" in DEFAULT_CATEGORIES
    assert "budget" in DEFAULT_CATEGORIES
    assert "solar" in DEFAULT_CATEGORIES
    assert "community" in DEFAULT_CATEGORIES
    assert len(DEFAULT_CATEGORIES) == 6


# ─── Web Push Service ────────────────────────────────────────────────────────


def test_webpush_configured():
    from app.services.notifications.webpush import WebPushService
    svc = WebPushService()
    assert svc.is_configured() is True  # VAPID keys are now set in .env


def test_batch_result_counts():
    from app.services.notifications.webpush import BatchResult, NotificationResult
    results = [
        NotificationResult(success=True, status_code=201),
        NotificationResult(success=False, error="fail"),
        NotificationResult(success=True, status_code=201),
    ]
    batch = BatchResult(results=results)
    assert batch.success_count == 2
    assert batch.failure_count == 1


# ─── Scheduler ────────────────────────────────────────────────────────────────


def test_scheduler_exports():
    """Verify scheduler module can import its key functions."""
    from app.services.notifications.scheduler import (
        check_and_send_notifications,
        get_active_subscriptions,
        mark_subscription_inactive,
        log_notification_event,
    )
    assert callable(check_and_send_notifications)
    assert callable(get_active_subscriptions)
    assert callable(mark_subscription_inactive)
    assert callable(log_notification_event)


# ─── API Contract ─────────────────────────────────────────────────────────────


def test_api_endpoints_exist():
    """Verify the notifications router has the expected number of endpoints."""
    from app.api.v1.notifications import router
    # subscribe, unsubscribe, GET preferences, PUT preferences, test
    assert len(router.routes) == 5
