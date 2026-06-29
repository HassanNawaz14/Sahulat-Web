"""Unit tests for P10 Budget Manager.

Run: python -m pytest backend/tests/test_budget.py -v
"""
import sys
sys.path.insert(0, "backend")

import pydantic
from app.services.budget.calculator import (
    calculate_budget_status,
    DEFAULT_BUDGET_CATEGORIES,
    UTILITY_CATEGORIES,
)
from app.api.v1.budget import CategoryCreate, ExpenseCreate, CategoryLimitUpdate


# ─── calculate_budget_status ──────────────────────────────────────────────────


def test_calculate_budget_status_safe():
    assert calculate_budget_status(0, 100) == "safe"
    assert calculate_budget_status(50, 100) == "safe"
    assert calculate_budget_status(79.9, 100) == "safe"


def test_calculate_budget_status_warning():
    assert calculate_budget_status(80, 100) == "warning"
    assert calculate_budget_status(90, 100) == "warning"
    assert calculate_budget_status(99.9, 100) == "warning"


def test_calculate_budget_status_exceeded():
    assert calculate_budget_status(100, 100) == "exceeded"
    assert calculate_budget_status(150, 100) == "exceeded"
    assert calculate_budget_status(999, 100) == "exceeded"


def test_calculate_budget_status_zero_limit():
    assert calculate_budget_status(0, 0) == "safe"
    assert calculate_budget_status(100, 0) == "safe"


# ─── Schema Validation ────────────────────────────────────────────────────────


def test_category_create_schema_valid():
    cat = CategoryCreate(code="custom_bill", label="Custom Bill", monthly_limit=5000)
    assert cat.code == "custom_bill"
    assert cat.label == "Custom Bill"
    assert cat.monthly_limit == 5000


def test_category_create_schema_minimal():
    cat = CategoryCreate(code="test", label="Test")
    assert cat.monthly_limit is None


def test_category_create_schema_empty_code():
    try:
        CategoryCreate(code="", label="Test")
        assert False, "Should have raised ValidationError"
    except pydantic.ValidationError:
        pass


def test_category_create_schema_long_code():
    try:
        CategoryCreate(code="a" * 51, label="Test")
        assert False, "Should have raised ValidationError"
    except pydantic.ValidationError:
        pass


def test_category_create_schema_long_label():
    try:
        CategoryCreate(code="test", label="a" * 101)
        assert False, "Should have raised ValidationError"
    except pydantic.ValidationError:
        pass


def test_category_limit_update_schema():
    body = CategoryLimitUpdate(monthly_limit=10000)
    assert body.monthly_limit == 10000


def test_expense_create_schema_valid():
    exp = ExpenseCreate(
        category_id="uuid-here",
        amount=700,
        expense_date="2025-06-05",
        description="Cable bill",
        is_recurring=True,
        recurrence_day=5,
    )
    assert exp.amount == 700
    assert exp.recurrence_day == 5
    assert exp.is_recurring is True


def test_expense_create_schema_negative_amount():
    try:
        ExpenseCreate(
            category_id="uuid",
            amount=-100,
            expense_date="2025-06-05",
        )
        assert False, "Should have raised ValidationError"
    except pydantic.ValidationError:
        pass


def test_expense_create_schema_zero_amount():
    try:
        ExpenseCreate(
            category_id="uuid",
            amount=0,
            expense_date="2025-06-05",
        )
        assert False, "Should have raised ValidationError"
    except pydantic.ValidationError:
        pass


def test_expense_create_schema_invalid_date():
    try:
        ExpenseCreate(
            category_id="uuid",
            amount=500,
            expense_date="not-a-date",
        )
        assert False, "Should have raised ValidationError"
    except pydantic.ValidationError:
        pass


def test_expense_create_schema_invalid_recurrence_day():
    try:
        ExpenseCreate(
            category_id="uuid",
            amount=500,
            expense_date="2025-06-05",
            is_recurring=True,
            recurrence_day=32,
        )
        assert False, "Should have raised ValidationError"
    except pydantic.ValidationError:
        pass

    try:
        ExpenseCreate(
            category_id="uuid",
            amount=500,
            expense_date="2025-06-05",
            is_recurring=True,
            recurrence_day=0,
        )
        assert False, "Should have raised ValidationError"
    except pydantic.ValidationError:
        pass


# ─── Default Categories ───────────────────────────────────────────────────────


def test_default_categories_count():
    assert len(DEFAULT_BUDGET_CATEGORIES) == 10


def test_default_categories_content():
    codes = {c["code"] for c in DEFAULT_BUDGET_CATEGORIES}
    assert "electricity" in codes
    assert "gas" in codes
    assert "water" in codes
    assert "internet" in codes
    assert "cable_tv" in codes
    assert "mobile_data" in codes
    assert "groceries" in codes
    assert "education" in codes
    assert "other" in codes


def test_utility_categories_set():
    assert "electricity" in UTILITY_CATEGORIES
    assert "gas" in UTILITY_CATEGORIES
    assert "water" in UTILITY_CATEGORIES
    assert "internet" in UTILITY_CATEGORIES
    assert "cable_tv" not in UTILITY_CATEGORIES
    assert "groceries" not in UTILITY_CATEGORIES


def test_default_category_labels_match_plan():
    labels = {c["label"] for c in DEFAULT_BUDGET_CATEGORIES}
    expected = {
        "Electricity", "Gas", "Water", "Internet",
        "Cable TV", "Mobile Data", "Solar Maintenance",
        "Groceries", "Education", "Other",
    }
    assert labels == expected


# ─── Integration Helpers (interface contract) ─────────────────────────────────


def test_tariff_engine_importable():
    from app.services.tariff import compute_electricity_bill
    result = compute_electricity_bill(100, "lesco", "unprotected")
    assert "total" in result
    assert result["total"] > 0


def test_estimate_from_readings_signature():
    from app.services.budget.calculator import _estimate_from_readings, _last_bill_total
    assert callable(_estimate_from_readings)
    assert callable(_last_bill_total)
