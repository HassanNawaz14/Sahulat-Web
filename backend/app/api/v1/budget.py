from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, field_validator

from app.core.auth import get_current_user
from app.core.supabase import supabase
from app.services.budget.calculator import (
    calculate_budget_status,
    get_monthly_summary,
    seed_default_categories,
)

router = APIRouter(prefix="/api/v1/budget", tags=["budget"])


# ─── Schemas ──────────────────────────────────────────────────────────────────


class CategoryCreate(BaseModel):
    code: str
    label: str
    monthly_limit: Optional[float] = None

    @field_validator("code")
    @classmethod
    def valid_code(cls, v: str):
        if not v or len(v) > 50:
            raise ValueError("code must be 1-50 characters")
        return v

    @field_validator("label")
    @classmethod
    def valid_label(cls, v: str):
        if not v or len(v) > 100:
            raise ValueError("label must be 1-100 characters")
        return v


class CategoryLimitUpdate(BaseModel):
    monthly_limit: float


class ExpenseCreate(BaseModel):
    category_id: str
    home_id: Optional[str] = None
    amount: float
    expense_date: str
    description: Optional[str] = None
    is_recurring: bool = False
    recurrence_day: Optional[int] = None

    @field_validator("amount")
    @classmethod
    def positive_amount(cls, v: float):
        if v <= 0:
            raise ValueError("amount must be positive")
        return v

    @field_validator("expense_date")
    @classmethod
    def valid_date(cls, v: str):
        try:
            datetime.strptime(v, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("expense_date must be YYYY-MM-DD")
        return v

    @field_validator("recurrence_day")
    @classmethod
    def valid_day(cls, v: Optional[int]):
        if v is not None and (v < 1 or v > 31):
            raise ValueError("recurrence_day must be 1-31")
        return v


# ─── Endpoints ────────────────────────────────────────────────────────────────


@router.get("/summary")
async def budget_summary(
    month: str = Query(..., pattern=r"^\d{4}-\d{2}$"),
    current_user: dict = Depends(get_current_user),
):
    return get_monthly_summary(current_user["user_id"], month)


@router.get("/categories")
async def list_categories(current_user: dict = Depends(get_current_user)):
    seed_default_categories(current_user["user_id"])
    result = (
        supabase.table("budget_categories")
        .select("*")
        .eq("user_id", current_user["user_id"])
        .order("created_at")
        .execute()
    )
    return result.data or []


@router.post("/categories", status_code=201)
async def create_category(
    body: CategoryCreate,
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["user_id"]

    existing = (
        supabase.table("budget_categories")
        .select("id")
        .eq("user_id", user_id)
        .eq("code", body.code)
        .execute()
    )
    if existing.data:
        raise HTTPException(409, detail=f"Category '{body.code}' already exists")

    custom_count = (
        supabase.table("budget_categories")
        .select("id", count="exact")
        .eq("user_id", user_id)
        .eq("is_custom", True)
        .execute()
    )
    if custom_count.count is not None and custom_count.count >= 15:
        raise HTTPException(400, detail="Max 15 custom categories per user")

    result = (
        supabase.table("budget_categories")
        .insert({
            "user_id": user_id,
            "code": body.code,
            "label": body.label,
            "monthly_limit": body.monthly_limit,
            "is_custom": True,
        })
        .execute()
    )
    return result.data[0] if result.data else {}


@router.put("/categories/{category_id}/limit")
async def update_category_limit(
    category_id: str,
    body: CategoryLimitUpdate,
    current_user: dict = Depends(get_current_user),
):
    cat = (
        supabase.table("budget_categories")
        .select("id")
        .eq("id", category_id)
        .eq("user_id", current_user["user_id"])
        .single()
        .execute()
    )
    if not cat.data:
        raise HTTPException(404, detail="Category not found")

    result = (
        supabase.table("budget_categories")
        .update({"monthly_limit": body.monthly_limit, "updated_at": datetime.now(timezone.utc).isoformat()})
        .eq("id", category_id)
        .execute()
    )
    return result.data[0] if result.data else {}


@router.post("/expenses", status_code=201)
async def create_expense(
    body: ExpenseCreate,
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["user_id"]

    cat = (
        supabase.table("budget_categories")
        .select("id")
        .eq("id", body.category_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    if not cat.data:
        raise HTTPException(404, detail="Category not found or does not belong to you")

    payload = {
        "user_id": user_id,
        "category_id": body.category_id,
        "home_id": body.home_id,
        "amount": body.amount,
        "expense_date": body.expense_date,
        "description": body.description,
        "is_recurring": body.is_recurring,
        "recurrence_day": body.recurrence_day,
    }
    result = supabase.table("budget_expenses").insert(payload).execute()
    return result.data[0] if result.data else {}


@router.get("/expenses")
async def list_expenses(
    month: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}$"),
    category_id: Optional[str] = None,
    limit: int = Query(50, le=100),
    cursor: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["user_id"]
    query = (
        supabase.table("budget_expenses")
        .select("*, budget_categories!inner(code, label)")
        .eq("user_id", user_id)
        .order("expense_date", desc=True)
        .limit(limit + 1)
    )

    if month:
        query = query.gte("expense_date", f"{month}-01")
        query = query.lte("expense_date", f"{month}-31")
    if category_id:
        query = query.eq("category_id", category_id)
    if cursor:
        query = query.lt("expense_date", cursor)

    result = query.execute()
    items = result.data or []
    has_more = len(items) > limit
    if has_more:
        items = items[:limit]

    mapped = []
    for item in items:
        cat = item.get("budget_categories") or {}
        mapped.append({
            "id": item["id"],
            "category_code": cat.get("code", ""),
            "category_label": cat.get("label", ""),
            "amount": float(item["amount"]),
            "expense_date": item["expense_date"],
            "description": item.get("description"),
            "is_recurring": item.get("is_recurring", False),
        })

    return {
        "items": mapped,
        "next_cursor": items[-1]["expense_date"] if has_more else None,
    }


@router.delete("/expenses/{expense_id}")
async def delete_expense(
    expense_id: str,
    current_user: dict = Depends(get_current_user),
):
    result = (
        supabase.table("budget_expenses")
        .select("id")
        .eq("id", expense_id)
        .eq("user_id", current_user["user_id"])
        .execute()
    )
    if not result.data:
        raise HTTPException(404, detail="Expense not found")

    supabase.table("budget_expenses").delete().eq("id", expense_id).execute()
    return {"status": "ok"}
