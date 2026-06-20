from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from postgrest import APIError

from app.core.auth import get_current_user
from app.core.supabase import supabase
from app.scrapers.registry import SCRAPER_REGISTRY, get_scraper

router = APIRouter(prefix="/api/v1", tags=["bills"])

# ─── Schemas ──────────────────────────────────────────────────────────────────


class ConsumerAccountCreate(BaseModel):
    home_id: str | None = None
    utility_type: str
    provider_code: str
    consumer_number: str
    account_label: str | None = None

    @field_validator("utility_type")
    @classmethod
    def validate_utility_type(cls, v: str) -> str:
        allowed = {"electricity", "gas", "water", "internet"}
        if v not in allowed:
            raise ValueError(f"utility_type must be one of: {allowed}")
        return v

    @field_validator("provider_code")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        if v in SCRAPER_REGISTRY:
            return v
        raise ValueError(f"Unsupported or unknown provider_code: {v}")


class ConsumerAccountUpdate(BaseModel):
    home_id: str | None = None
    account_label: str | None = None


class BillStatusUpdate(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = {"unpaid", "paid", "overdue"}
        if v not in allowed:
            raise ValueError(f"status must be one of: {allowed}")
        return v


# ─── Helper ────────────────────────────────────────────────────────────────────


def _verify_ownership(account_id: str, user_id: str) -> dict:
    try:
        result = (
            supabase.table("consumer_accounts")
            .select("*")
            .eq("id", account_id)
            .eq("user_id", user_id)
            .single()
            .execute()
        )
    except APIError:
        raise HTTPException(status_code=404, detail="Consumer account not found")
    if not result.data:
        raise HTTPException(status_code=404, detail="Consumer account not found")
    return result.data


def _parse_billing_month(issue_date_str: str | None) -> str:
    if not issue_date_str:
        return date.today().replace(day=1).isoformat()
    for fmt in ("%d %b %y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            d = datetime.strptime(issue_date_str, fmt).date()
            return d.replace(day=1).isoformat()
        except ValueError:
            continue
    return date.today().replace(day=1).isoformat()


def _encrypt(text: str) -> str:
    return text


def _decrypt(text: str) -> str:
    return text


# ─── Consumer Account Endpoints ───────────────────────────────────────────────


@router.get("/consumer-accounts")
async def list_consumer_accounts(current_user: dict = Depends(get_current_user)):
    result = (
        supabase.table("consumer_accounts")
        .select("*")
        .eq("user_id", current_user["user_id"])
        .order("created_at", desc=True)
        .execute()
    )
    return {"consumer_accounts": result.data or []}


@router.post("/consumer-accounts")
async def create_consumer_account(
    body: ConsumerAccountCreate,
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["user_id"]

    existing = (
        supabase.table("consumer_accounts")
        .select("id")
        .eq("user_id", user_id)
        .eq("utility_type", body.utility_type)
        .eq("provider_code", body.provider_code)
        .eq("consumer_number", _encrypt(body.consumer_number))
        .execute()
    )
    if existing.data:
        raise HTTPException(
            status_code=409,
            detail="This consumer number is already linked to your account",
        )

    account_count = (
        supabase.table("consumer_accounts")
        .select("id", count="exact")
        .eq("user_id", user_id)
        .eq("is_active", True)
        .execute()
    )
    if account_count.count and account_count.count >= 10:
        try:
            profile = (
                supabase.table("profiles")
                .select("premium")
                .eq("id", user_id)
                .single()
                .execute()
            )
        except APIError:
            profile = type('obj', (object,), {'data': None})()
        if not profile.data or not profile.data.get("premium"):
            raise HTTPException(
                status_code=403,
                detail="Free tier limit: max 10 consumer accounts. Upgrade to Premium.",
            )

    if body.home_id:
        try:
            home = (
                supabase.table("homes")
                .select("id")
                .eq("id", body.home_id)
                .eq("user_id", user_id)
                .single()
                .execute()
            )
        except APIError:
            raise HTTPException(status_code=404, detail="Home not found")
        if not home.data:
            raise HTTPException(status_code=404, detail="Home not found")

    result = (
        supabase.table("consumer_accounts")
        .insert({
            "user_id": user_id,
            "home_id": body.home_id,
            "utility_type": body.utility_type,
            "provider_code": body.provider_code,
            "consumer_number": _encrypt(body.consumer_number),
            "account_label": body.account_label or "",
        })
        .execute()
    )
    return {"consumer_account": result.data[0]}


@router.patch("/consumer-accounts/{account_id}")
async def update_consumer_account(
    account_id: str,
    body: ConsumerAccountUpdate,
    current_user: dict = Depends(get_current_user),
):
    _verify_ownership(account_id, current_user["user_id"])
    update_data = body.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    result = (
        supabase.table("consumer_accounts")
        .update(update_data)
        .eq("id", account_id)
        .eq("user_id", current_user["user_id"])
        .execute()
    )
    return {"consumer_account": result.data[0]}


@router.delete("/consumer-accounts/{account_id}")
async def delete_consumer_account(
    account_id: str,
    current_user: dict = Depends(get_current_user),
):
    _verify_ownership(account_id, current_user["user_id"])
    supabase.table("consumer_accounts").update({"is_active": False}).eq(
        "id", account_id
    ).eq("user_id", current_user["user_id"]).execute()
    return {"message": "Consumer account deactivated"}


# ─── Bill Endpoints ───────────────────────────────────────────────────────────


@router.post("/bills/fetch/{consumer_account_id}")
async def fetch_bill(
    consumer_account_id: str,
    current_user: dict = Depends(get_current_user),
):
    account = _verify_ownership(consumer_account_id, current_user["user_id"])
    provider = account["provider_code"]

    if provider not in SCRAPER_REGISTRY:
        raise HTTPException(status_code=400, detail=f"No scraper for {provider}")

    scraper = get_scraper(provider)
    consumer_number = _decrypt(account["consumer_number"])

    try:
        bill_data = await scraper.fetch_bill(consumer_number)
    except Exception as e:
        error_type = type(e).__name__
        if error_type == "InvalidConsumerNumberError":
            raise HTTPException(status_code=422, detail="Invalid consumer number format")
        elif error_type == "PortalUnreachableError":
            raise HTTPException(status_code=503, detail="Utility portal temporarily unavailable")
        elif error_type == "NoBillFoundError":
            return {"status": "no_bill", "message": "No pending bill found"}
        elif error_type == "ParsingFailedError":
            raise HTTPException(status_code=502, detail="Bill data parsing failed — portal may have changed")
        elif error_type == "CaptchaDetectedError":
            raise HTTPException(status_code=503, detail="Captcha detected — manual check required")
        else:
            raise HTTPException(status_code=500, detail=f"Bill fetch failed: {str(e)}")

    billing_month = _parse_billing_month(bill_data.issue_date)

    existing = (
        supabase.table("bills")
        .select("id")
        .eq("consumer_account_id", consumer_account_id)
        .eq("billing_month", billing_month)
        .execute()
    )

    bill_payload = {
        "consumer_account_id": consumer_account_id,
        "user_id": current_user["user_id"],
        "billing_month": billing_month,
        "issue_date": bill_data.issue_date,
        "due_date": bill_data.due_date,
        "amount_payable": bill_data.amount_payable,
        "units_consumed": bill_data.units_consumed,
        "previous_reading": bill_data.previous_reading,
        "current_reading": bill_data.current_reading,
        "arrears": bill_data.arrears,
        "taxes": bill_data.taxes,
        "surcharges": bill_data.surcharges,
        "meter_rent": bill_data.meter_rent,
        "fc_surcharge": bill_data.fc_surcharge,
        "tariff_slab": bill_data.tariff_slab,
        "raw_data": bill_data.raw_data,
    }

    if existing.data:
        bill_payload["updated_at"] = datetime.utcnow().isoformat()
        result = (
            supabase.table("bills")
            .update(bill_payload)
            .eq("id", existing.data[0]["id"])
            .execute()
        )
    else:
        result = supabase.table("bills").insert(bill_payload).execute()

    supabase.table("consumer_accounts").update(
        {"last_fetched_at": datetime.utcnow().isoformat()}
    ).eq("id", consumer_account_id).execute()

    return {
        "status": "success",
        "bill": result.data[0] if result.data else None,
    }


@router.get("/bills/{consumer_account_id}/latest")
async def get_latest_bill(
    consumer_account_id: str,
    current_user: dict = Depends(get_current_user),
):
    _verify_ownership(consumer_account_id, current_user["user_id"])
    result = (
        supabase.table("bills")
        .select("*")
        .eq("consumer_account_id", consumer_account_id)
        .order("billing_month", desc=True)
        .limit(1)
        .execute()
    )
    if not result.data:
        return {"bill": None}
    return {"bill": result.data[0]}


@router.get("/bills/{consumer_account_id}/history")
async def get_bill_history(
    consumer_account_id: str,
    months: int = 6,
    current_user: dict = Depends(get_current_user),
):
    _verify_ownership(consumer_account_id, current_user["user_id"])
    result = (
        supabase.table("bills")
        .select(
            "id, billing_month, amount_payable, units_consumed, status, "
            "issue_date, due_date"
        )
        .eq("consumer_account_id", consumer_account_id)
        .order("billing_month", desc=True)
        .limit(min(months, 24))
        .execute()
    )
    return {
        "consumer_account_id": consumer_account_id,
        "history": result.data or [],
    }


@router.patch("/bills/{bill_id}/status")
async def update_bill_status(
    bill_id: str,
    body: BillStatusUpdate,
    current_user: dict = Depends(get_current_user),
):
    try:
        existing = (
            supabase.table("bills")
            .select("id, user_id")
            .eq("id", bill_id)
            .single()
            .execute()
        )
    except APIError:
        raise HTTPException(status_code=404, detail="Bill not found")
    if not existing.data:
        raise HTTPException(status_code=404, detail="Bill not found")
    if existing.data["user_id"] != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Not authorized to update this bill")

    result = (
        supabase.table("bills")
        .update({"status": body.status, "updated_at": datetime.utcnow().isoformat()})
        .eq("id", bill_id)
        .execute()
    )
    return {"bill": result.data[0]}


@router.get("/bills/summary")
async def get_bills_summary(current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]

    accounts_result = (
        supabase.table("consumer_accounts")
        .select("id, utility_type, provider_code, account_label")
        .eq("user_id", user_id)
        .eq("is_active", True)
        .execute()
    )
    accounts = accounts_result.data or []

    total = 0.0
    breakdown = []
    for acc in accounts:
        bill_result = (
            supabase.table("bills")
            .select("amount_payable, billing_month, status, due_date")
            .eq("consumer_account_id", acc["id"])
            .order("billing_month", desc=True)
            .limit(1)
            .execute()
        )
        latest_bill = bill_result.data[0] if bill_result.data else None
        if latest_bill:
            total += float(latest_bill["amount_payable"])
            breakdown.append({
                "consumer_account_id": acc["id"],
                "utility_type": acc["utility_type"],
                "provider_code": acc["provider_code"],
                "label": acc["account_label"] or acc["provider_code"].upper(),
                "amount": float(latest_bill["amount_payable"]),
                "billing_month": latest_bill["billing_month"],
                "status": latest_bill["status"],
                "due_date": latest_bill["due_date"],
            })

    return {
        "total_this_month": round(total, 2),
        "account_count": len(accounts),
        "breakdown": breakdown,
    }
