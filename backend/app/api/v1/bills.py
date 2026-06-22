import asyncio
import base64
import time
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from postgrest import APIError

from app.core.auth import get_current_user
from app.core.supabase import supabase
from app.scrapers.base import (
    CaptchaDetectedError,
    InvalidConsumerNumberError,
    NoBillFoundError,
    ParsingFailedError,
    PortalUnreachableError,
    ScrapedBill,
)
from app.core.security import decrypt, encrypt, parse_billing_month
from app.scrapers.registry import SCRAPER_REGISTRY, get_scraper
from app.api.v1.consumption import prune_readings_for_billing_month

# ─── Captcha Session Store ───────────────────────────────────────────────────

CAPTCHA_SESSION_TTL = 300  # 5 minutes
captcha_sessions: dict[str, dict] = {}


def _create_captcha_session(data: dict) -> str:
    session_id = str(uuid.uuid4())
    data["created_at"] = time.time()
    captcha_sessions[session_id] = data
    return session_id


def _get_captcha_session(session_id: str) -> dict | None:
    session = captcha_sessions.get(session_id)
    if not session:
        return None
    if time.time() - session["created_at"] > CAPTCHA_SESSION_TTL:
        del captcha_sessions[session_id]
        return None
    return session


async def _cleanup_expired_sessions():
    now = time.time()
    expired = [sid for sid, s in captcha_sessions.items() if now - s["created_at"] > CAPTCHA_SESSION_TTL]
    for sid in expired:
        sess = captcha_sessions.pop(sid, None)
        if sess:
            cl = sess.get("client")
            if cl:
                await cl.aclose()


async def _close_captcha_session(captcha_id: str):
    if captcha_id in captcha_sessions:
        sess = captcha_sessions.pop(captcha_id, None)
        if sess:
            cl = sess.get("client")
            if cl:
                await cl.aclose()


def _is_missing_column_error(error: Exception, column_name: str) -> bool:
    message = " ".join(
        str(part)
        for part in (
            getattr(error, "message", ""),
            getattr(error, "details", ""),
            getattr(error, "hint", ""),
            str(error),
        )
        if part
    ).lower()
    needle = f'column "{column_name.lower()}" does not exist'
    return needle in message or f"column {column_name.lower()} does not exist" in message

router = APIRouter(prefix="/api/v1", tags=["bills"])

# ─── Coming Soon Signups ───────────────────────────────────────────────────────


class ComingSoonSignup(BaseModel):
    provider_code: str


@router.post("/coming-soon-signup")
async def coming_soon_signup(
    body: ComingSoonSignup,
    current_user: dict = Depends(get_current_user),
):
    try:
        existing = (
            supabase.table("coming_soon_signups")
            .select("id")
            .eq("user_id", current_user["user_id"])
            .eq("provider_code", body.provider_code)
            .execute()
        )
        if existing.data:
            return {"message": "You're already signed up for notifications", "signup": existing.data[0]}

        result = (
            supabase.table("coming_soon_signups")
            .insert({
                "user_id": current_user["user_id"],
                "provider_code": body.provider_code,
            })
            .execute()
        )
        return {"message": "We'll notify you when this provider becomes available", "signup": result.data[0]}
    except APIError:
        return {"message": "Coming soon signup is not available yet"}


@router.get("/coming-soon-signups")
async def list_coming_soon_signups(current_user: dict = Depends(get_current_user)):
    try:
        result = (
            supabase.table("coming_soon_signups")
            .select("provider_code")
            .eq("user_id", current_user["user_id"])
            .execute()
        )
        return {"signups": [r["provider_code"] for r in (result.data or [])]}
    except APIError:
        return {"signups": []}

# ─── Schemas ──────────────────────────────────────────────────────────────────


class ConsumerAccountCreate(BaseModel):
    home_id: str | None = None
    utility_type: str
    provider_code: str
    consumer_number: str
    provider_reference: str | None = None
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
    provider_reference: str | None = None
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


class CaptchaSolveRequest(BaseModel):
    captcha_id: str
    captcha_solution: str


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
    except APIError as e:
        code = getattr(e, "code", None)
        if code not in ("404", "406"):
            raise
        raise HTTPException(status_code=404, detail="Consumer account not found")
    if not result.data:
        raise HTTPException(status_code=404, detail="Consumer account not found")
    return result.data


# ─── Consumer Account Endpoints ───────────────────────────────────────────────


@router.get("/consumer-accounts")
async def list_consumer_accounts(current_user: dict = Depends(get_current_user)):
    result = (
        supabase.table("consumer_accounts")
        .select("*")
        .eq("user_id", current_user["user_id"])
        .eq("is_active", True)
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
    encrypted_consumer_number = encrypt(body.consumer_number)
    encrypted_provider_reference = (
        encrypt(body.provider_reference.strip())
        if body.provider_reference and body.provider_reference.strip()
        else None
    )

    existing = (
        supabase.table("consumer_accounts")
        .select("id, is_active")
        .eq("user_id", user_id)
        .eq("utility_type", body.utility_type)
        .eq("provider_code", body.provider_code)
        .eq("consumer_number", encrypted_consumer_number)
        .execute()
    )
    if existing.data:
        record = existing.data[0]
        if record["is_active"]:
            raise HTTPException(
                status_code=409,
                detail="This consumer number is already linked to your account",
            )
        is_reactivation = True
        existing_id = record["id"]
    else:
        is_reactivation = False

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

    if is_reactivation:
        update_data = {"is_active": True, "updated_at": datetime.utcnow().isoformat()}
        if body.account_label is not None:
            update_data["account_label"] = body.account_label
        if body.home_id is not None:
            update_data["home_id"] = body.home_id
        if body.provider_reference is not None:
            update_data["provider_reference"] = encrypted_provider_reference
        try:
            result = (
                supabase.table("consumer_accounts")
                .update(update_data)
                .eq("id", existing_id)
                .execute()
            )
        except APIError as e:
            if "provider_reference" in update_data and _is_missing_column_error(e, "provider_reference"):
                update_data.pop("provider_reference", None)
                if not update_data:
                    raise HTTPException(status_code=400, detail="No fields to update")
                result = (
                    supabase.table("consumer_accounts")
                    .update(update_data)
                    .eq("id", existing_id)
                    .execute()
                )
            else:
                raise
    else:
        insert_data = {
            "user_id": user_id,
            "home_id": body.home_id,
            "utility_type": body.utility_type,
            "provider_code": body.provider_code,
            "consumer_number": encrypted_consumer_number,
            "account_label": body.account_label or "",
        }
        if encrypted_provider_reference is not None:
            insert_data["provider_reference"] = encrypted_provider_reference
        try:
            result = (
                supabase.table("consumer_accounts")
                .insert(insert_data)
                .execute()
            )
        except APIError as e:
            if encrypted_provider_reference is not None and _is_missing_column_error(e, "provider_reference"):
                insert_data.pop("provider_reference", None)
                result = (
                    supabase.table("consumer_accounts")
                    .insert(insert_data)
                    .execute()
                )
            elif getattr(e, "code", None) == "23505":
                raise HTTPException(
                    status_code=409,
                    detail="This consumer number is already linked to your account",
                )
            else:
                raise
    return {"consumer_account": result.data[0]}


@router.patch("/consumer-accounts/{account_id}")
async def update_consumer_account(
    account_id: str,
    body: ConsumerAccountUpdate,
    current_user: dict = Depends(get_current_user),
):
    _verify_ownership(account_id, current_user["user_id"])
    update_data = body.model_dump(exclude_none=True)
    if "provider_reference" in update_data:
        ref = (update_data["provider_reference"] or "").strip()
        update_data["provider_reference"] = encrypt(ref) if ref else None
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    try:
        result = (
            supabase.table("consumer_accounts")
            .update(update_data)
            .eq("id", account_id)
            .eq("user_id", current_user["user_id"])
            .execute()
        )
    except APIError as e:
        if "provider_reference" in update_data and _is_missing_column_error(e, "provider_reference"):
            update_data.pop("provider_reference", None)
            if not update_data:
                raise HTTPException(status_code=400, detail="No fields to update")
            result = (
                supabase.table("consumer_accounts")
                .update(update_data)
                .eq("id", account_id)
                .eq("user_id", current_user["user_id"])
                .execute()
            )
        else:
            raise
    return {"consumer_account": result.data[0]}


@router.delete("/consumer-accounts/{account_id}")
async def delete_consumer_account(
    account_id: str,
    current_user: dict = Depends(get_current_user),
):
    _verify_ownership(account_id, current_user["user_id"])
    supabase.table("consumer_accounts").delete().eq(
        "id", account_id
    ).eq("user_id", current_user["user_id"]).execute()
    return {"message": "Consumer account permanently deleted"}


# ─── Bill Storage Helper ──────────────────────────────────────────────────────


def _store_bill_data(consumer_account_id: str, user_id: str, bill_data: ScrapedBill) -> dict:
    billing_month = parse_billing_month(bill_data.issue_date, bill_data.due_date)
    existing = (
        supabase.table("bills")
        .select("id")
        .eq("consumer_account_id", consumer_account_id)
        .eq("billing_month", billing_month)
        .execute()
    )
    bill_payload = {
        "consumer_account_id": consumer_account_id,
        "user_id": user_id,
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
        result = supabase.table("bills").update(bill_payload).eq("id", existing.data[0]["id"]).execute()
    else:
        result = supabase.table("bills").insert(bill_payload).execute()
    supabase.table("consumer_accounts").update(
        {"last_fetched_at": datetime.utcnow().isoformat()}
    ).eq("id", consumer_account_id).execute()

    # Prune meter readings for this billing month — the bill now captures them
    try:
        prune_readings_for_billing_month(consumer_account_id, billing_month)
    except Exception:
        pass  # non-critical; don't fail the bill fetch

    return result.data[0] if result.data else None


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
    consumer_number = decrypt(account["consumer_number"])
    provider_reference = decrypt(account.get("provider_reference") or "")

    # Helper to create captcha challenge and session
    async def _do_captcha_challenge():
        await _cleanup_expired_sessions()
        if not hasattr(scraper, "prepare_captcha"):
            raise HTTPException(status_code=503, detail="Captcha required but provider does not support captcha challenge flow")
        try:
            challenge = await scraper.prepare_captcha(consumer_number, provider_reference or None)
        except Exception as ce:
            raise HTTPException(status_code=503, detail=f"Captcha required but challenge setup failed: {ce}")
        captcha_id = _create_captcha_session({
            "consumer_account_id": consumer_account_id,
            "user_id": current_user["user_id"],
            "provider_code": provider,
            "client": challenge["client"],
            "csrf_token": challenge["csrf_token"],
            "consumer_number": challenge["consumer_number"],
            "provider_reference": provider_reference,
            "area_code": challenge["area_code"],
            "local_no": challenge["local_no"],
        })
        return {
            "status": "captcha_required",
            "captcha_id": captcha_id,
            "captcha_image": challenge["captcha_image"],
        }

    # Providers that always require captcha (e.g. PTCL): skip fetch_bill entirely.
    # This avoids triggering PTCL anti-bot from rapid failed POST attempts.
    if getattr(scraper, "requires_captcha", False):
        await asyncio.sleep(2)
        return await _do_captcha_challenge()

    try:
        bill_data = await scraper.fetch_bill(consumer_number)
    except InvalidConsumerNumberError as e:
        raise HTTPException(status_code=422, detail=str(e) or "Invalid consumer number format")
    except PortalUnreachableError as e:
        raise HTTPException(status_code=503, detail=str(e) or "Utility portal temporarily unavailable")
    except NoBillFoundError as e:
        return {"status": "no_bill", "message": str(e) or "No pending bill found"}
    except ParsingFailedError as e:
        raise HTTPException(status_code=502, detail=str(e) or "Bill data parsing failed — portal may have changed")
    except CaptchaDetectedError:
        return await _do_captcha_challenge()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bill fetch failed: {str(e)}")

    bill_record = _store_bill_data(consumer_account_id, current_user["user_id"], bill_data)
    return {"status": "success", "bill": bill_record}


@router.post("/bills/fetch/{consumer_account_id}/captcha-solve")
async def captcha_solve(
    consumer_account_id: str,
    body: CaptchaSolveRequest,
    current_user: dict = Depends(get_current_user),
):
    _verify_ownership(consumer_account_id, current_user["user_id"])
    await _cleanup_expired_sessions()

    session = _get_captcha_session(body.captcha_id)
    if not session:
        raise HTTPException(status_code=404, detail="Captcha session expired or invalid. Please fetch again.")

    if session["consumer_account_id"] != consumer_account_id:
        raise HTTPException(status_code=400, detail="Captcha session does not match this account")

    scraper = get_scraper(session["provider_code"])
    if not hasattr(scraper, "complete_fetch"):
        raise HTTPException(status_code=500, detail="Provider does not support captcha solve")

    try:
        bill_data = await scraper.complete_fetch(
            client=session["client"],
            consumer_number=session["consumer_number"],
            csrf_token=session["csrf_token"],
            captcha_solution=body.captcha_solution,
            account_id=session.get("provider_reference") or None,
        )
    except CaptchaDetectedError as e:
        if hasattr(scraper, "refresh_captcha"):
            try:
                new_image = await scraper.refresh_captcha(session["client"])
                session["created_at"] = time.time()
                return {
                    "status": "captcha_required",
                    "captcha_id": body.captcha_id,
                    "captcha_image": new_image,
                }
            except Exception:
                await _close_captcha_session(body.captcha_id)
                raise HTTPException(status_code=400, detail=str(e) or "Incorrect captcha. Please try again.")
        await _close_captcha_session(body.captcha_id)
        raise HTTPException(status_code=400, detail=str(e) or "Incorrect captcha. Please try again.")
    except NoBillFoundError as e:
        await _close_captcha_session(body.captcha_id)
        return {"status": "no_bill", "message": str(e) or "No pending bill found"}
    except (InvalidConsumerNumberError, ParsingFailedError, PortalUnreachableError) as e:
        await _close_captcha_session(body.captcha_id)
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        await _close_captcha_session(body.captcha_id)
        raise HTTPException(status_code=500, detail=f"Bill fetch failed: {str(e)}")

    await _close_captcha_session(body.captcha_id)
    bill_record = _store_bill_data(consumer_account_id, current_user["user_id"], bill_data)
    return {"status": "success", "bill": bill_record}


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
            .select("id, user_id, consumer_account_id, billing_month")
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

    # Prune readings for this billing month when bill is paid
    if body.status == "paid":
        billing_month = existing.data.get("billing_month")
        consumer_account_id = existing.data.get("consumer_account_id")
        if billing_month and consumer_account_id:
            try:
                prune_readings_for_billing_month(consumer_account_id, billing_month)
            except Exception:
                pass  # non-critical

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
