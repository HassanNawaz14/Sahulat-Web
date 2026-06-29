"""Tests for P11 Solar Dashboard Module.

Run: python -m pytest backend/tests/test_solar.py -v
"""
import sys
sys.path.insert(0, "backend")

from datetime import date, datetime, timedelta

from app.services.solar.normalizer import (
    calculate_savings,
    calculate_roi,
    check_health_alerts,
    get_cleaning_reminder_days,
    calculate_sunny_baseline,
)
from app.services.solar.base import SolarProduction, BaseAdapter


# ─── Savings Unit Tests ─────────────────────────────────────────────────────


def test_savings_empty_data():
    result = calculate_savings([], 10.0, 21.0)
    assert result["monthly_savings"] == 0
    assert result["self_consumed_value"] == 0
    assert result["export_credit"] == 0


def test_savings_calculation():
    data = [{"production_kwh": 100.0, "date": "2025-06-01"}]
    result = calculate_savings(data, 10.0, 21.0)
    assert result["self_consumed_value"] > 0
    assert result["export_credit"] > 0
    assert result["monthly_savings"] == result["self_consumed_value"] + result["export_credit"]


def test_savings_no_net_metering():
    data = [{"production_kwh": 100.0, "date": "2025-06-01"}]
    result = calculate_savings(data, 10.0, 21.0, net_metering_enabled=False)
    assert result["export_credit"] == 0


def test_get_cleaning_reminder_large():
    assert get_cleaning_reminder_days(15.0) == 30
    assert get_cleaning_reminder_days(20.0) == 30


def test_get_cleaning_reminder_medium():
    assert get_cleaning_reminder_days(10.0) == 35
    assert get_cleaning_reminder_days(12.5) == 35


def test_get_cleaning_reminder_small():
    assert get_cleaning_reminder_days(5.0) == 45
    assert get_cleaning_reminder_days(9.9) == 45


# ─── ROI Unit Tests ─────────────────────────────────────────────────────────


def test_roi_full_payback():
    result = calculate_roi(100000, 5000, date.today() - timedelta(days=365 * 2))
    assert result["roi_percent"] >= 100
    assert result["months_remaining"] == 0


def test_roi_partial():
    commissioning = date.today().replace(year=date.today().year - 1)
    result = calculate_roi(120000, 5000, commissioning)
    assert 0 < result["roi_percent"] < 100
    assert result["months_remaining"] > 0


def test_roi_zero_cost():
    result = calculate_roi(0, 5000, date.today() - timedelta(days=365))
    assert result["roi_percent"] == 0


def test_roi_zero_savings():
    result = calculate_roi(100000, 0, date.today() - timedelta(days=365))
    assert result["roi_percent"] == 0
    assert result["months_remaining"] == 0


def test_roi_future_commissioning():
    future = date.today() + timedelta(days=30)
    result = calculate_roi(100000, 5000, future)
    assert result["months_remaining"] > 0
    assert result["amount_paid_back"] == 0


# ─── Health Alert Unit Tests ────────────────────────────────────────────────


def test_health_baseline_drop():
    today = date.today()
    data = [
        {"date": (today - timedelta(days=i)).isoformat(), "production_kwh": 5.0 if i == 0 else 40.0}
        for i in range(14)
    ]
    installation = {"system_size_kw": 10.0}
    alerts = check_health_alerts(installation, data, today)
    types = [a["type"] for a in alerts]
    assert "baseline_drop" in types


def test_health_no_alert_normal():
    today = date.today()
    data = [
        {"date": (today - timedelta(days=i)).isoformat(), "production_kwh": 40.0}
        for i in range(14)
    ]
    installation = {"system_size_kw": 10.0}
    alerts = check_health_alerts(installation, data, today)
    assert len([a for a in alerts if a["type"] == "baseline_drop"]) == 0


def test_health_zero_production():
    today = date.today()
    data = [
        {"date": (today - timedelta(days=i)).isoformat() if i > 0 else today.isoformat(),
         "production_kwh": 0.0 if i == 0 else 40.0}
        for i in range(14)
    ]
    installation = {"system_size_kw": 10.0}
    alerts = check_health_alerts(installation, data, today)
    types = [a["type"] for a in alerts]
    if datetime.now().hour >= 11:
        assert "zero_production" in types


def test_health_no_data():
    installation = {"system_size_kw": 10.0}
    alerts = check_health_alerts(installation, [], date.today())
    assert len(alerts) == 0


def test_sunny_baseline():
    data = [{"production_kwh": 40.0, "date": "x"}, {"production_kwh": 42.0, "date": "y"}]
    baseline = calculate_sunny_baseline(10.0, data)
    assert baseline >= 35.0


def test_sunny_baseline_no_sunny_days():
    data = [{"production_kwh": 10.0, "date": "x"}]
    baseline = calculate_sunny_baseline(10.0, data)
    assert baseline == 35.0


# ─── Base Adapter Tests ─────────────────────────────────────────────────────


def test_solar_production_class():
    prod = SolarProduction(
        date="2025-06-17",
        production_kwh=42.5,
        self_consumed_kwh=25.5,
        exported_kwh=17.0,
        imported_kwh=5.0,
        peak_power_kw=8.0,
    )
    assert prod.date == "2025-06-17"
    assert prod.production_kwh == 42.5
    assert prod.peak_power_kw == 8.0


def test_normalize_production():
    from app.services.solar.base import BaseAdapter

    class TestAdapter(BaseAdapter):
        async def authenticate(self, username, password, plant_id=None):
            pass
        async def fetch_daily_production(self, installation, target_date):
            pass
        async def fetch_range(self, installation, start_date, end_date):
            pass

    adapter = TestAdapter()
    raw = {"production_kwh": "42.5", "self_consumed_kwh": "25.5", "exported_kwh": "17.0", "peak_power_kw": "8.0"}
    result = adapter.normalize_production(raw, "2025-06-17")
    assert result.production_kwh == 42.5
    assert result.date == "2025-06-17"
