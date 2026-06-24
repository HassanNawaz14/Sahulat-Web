import calendar
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from postgrest import APIError

from app.core.auth import get_current_user
from app.core.supabase import supabase
from app.services.tariff import (
    _is_protected_consumer,
    compute_electricity_bill,
    compute_marginal_cost,
    get_active_tariffs,
    get_current_slab,
    get_cycle_start,
    get_next_slab,
)

router = APIRouter(prefix="/api/v1/consumption", tags=["consumption"])


# ─── Schemas ──────────────────────────────────────────────────────────────────


class MeterReadingCreate(BaseModel):
    consumer_account_id: str
    reading_date: str
    reading_value: float
    input_mode: str = "meter_reading"  # "meter_reading" or "units"
    notes: str | None = None


class MeterReadingResponse(BaseModel):
    id: str
    consumer_account_id: str
    reading_date: str
    reading_value: float
    units_since_last: float | None = None
    consumption_rate: float | None = None
    estimated_bill: float | None = None
    notes: str | None = None
    created_at: str | None = None


# ─── Helpers ────────────────────────────────────────────────────────────────────


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


def _get_latest_bill(consumer_account_id: str) -> dict | None:
    result = (
        supabase.table("bills")
        .select("*")
        .eq("consumer_account_id", consumer_account_id)
        .order("billing_month", desc=True)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


# ─── Endpoints ─────────────────────────────────────────────────────────────────


@router.post("/readings")
async def submit_reading(
    body: MeterReadingCreate,
    current_user: dict = Depends(get_current_user),
):
    try:
        return await _submit_reading_inner(body, current_user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"{type(e).__name__}: {e}")

async def _submit_reading_inner(
    body: MeterReadingCreate,
    current_user: dict,
):
    account = _verify_ownership(body.consumer_account_id, current_user["user_id"])

    # Fetch previous reading
    prev_result = (
        supabase.table("meter_readings")
        .select("*")
        .eq("consumer_account_id", body.consumer_account_id)
        .order("reading_date", desc=True)
        .limit(1)
        .execute()
    )
    prev = prev_result.data[0] if prev_result.data else None

    # Resolve reading_value and units_since_last based on input_mode
    units_since_last = None
    effective_reading_value = body.reading_value

    if body.input_mode == "units":
        # User entered units/kWh directly — compute cumulative meter reading
        units_since_last = round(body.reading_value, 2)
        if prev:
            effective_reading_value = round(
                float(prev["reading_value"]) + body.reading_value, 2
            )
    else:
        # meter_reading mode — user entered the number on the meter
        if prev and body.reading_value >= float(prev["reading_value"]):
            units_since_last = round(body.reading_value - float(prev["reading_value"]), 2)
        elif prev and body.reading_value < float(prev["reading_value"]):
            raise HTTPException(
                status_code=400,
                detail=f"Meter reading ({body.reading_value}) is lower than the previous reading ({float(prev['reading_value']):.0f}). The value should increase over time — check and try again.",
            )

    # Compute estimated bill for electricity accounts
    estimated_bill = None
    total_cycle_units = None
    old_trajectory = None
    new_trajectory = None
    if account["utility_type"] == "electricity":
        last_bill = _get_latest_bill(body.consumer_account_id)
        cycle_start = get_cycle_start(account, last_bill)
        category = "protected" if _is_protected_consumer(body.consumer_account_id) else "unprotected"

        # Fetch existing readings this cycle (before inserting new one)
        old_readings_result = (
            supabase.table("meter_readings")
            .select("*")
            .eq("consumer_account_id", body.consumer_account_id)
            .gte("reading_date", cycle_start.isoformat())
            .order("reading_date", desc=False)
            .execute()
        )
        old_readings = old_readings_result.data or []

        # Compute old trajectory (without this reading)
        if old_readings:
            old_trajectory = _compute_trajectory(account, cycle_start, old_readings, category)

        total_cycle_units = await _get_cycle_units(
            body.consumer_account_id, cycle_start, effective_reading_value
        )
        bill_est = compute_electricity_bill(total_cycle_units, account["provider_code"], category)
        estimated_bill = bill_est["total"]

    # Insert reading
    try:
        result = (
            supabase.table("meter_readings")
            .insert({
                "consumer_account_id": body.consumer_account_id,
                "user_id": current_user["user_id"],
                "reading_date": body.reading_date,
                "reading_value": effective_reading_value,
                "units_since_last": units_since_last,
                "estimated_bill": estimated_bill,
                "notes": body.notes or "",
            })
            .execute()
        )
    except APIError as e:
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            # Already have a reading at this date — user probably didn't advance the date picker.
            # Raise a clear error instead of silently overwriting the previous entry.
            raise HTTPException(
                status_code=409,
                detail="A reading already exists for this date. Please use a different date or delete the existing reading first.",
            )
        raise HTTPException(status_code=400, detail=str(e))

    # Check slab boundary
    current_slab = None
    units_to_next = None
    cost_if_crossed = None
    if total_cycle_units is not None:
        category = "protected" if _is_protected_consumer(body.consumer_account_id) else "unprotected"
        slabs = get_active_tariffs(account["provider_code"], category)
        current_slab = get_current_slab(total_cycle_units, slabs)
        if current_slab and current_slab["max"] is not None:
            next_s = get_next_slab(current_slab, slabs)
            if next_s:
                units_to_next = current_slab["max"] - total_cycle_units + 1
                cost_if_crossed = compute_marginal_cost(total_cycle_units, slabs)
                await _check_and_insert_slab_alert(
                    body.consumer_account_id,
                    current_user["user_id"],
                    units_to_next,
                    cost_if_crossed,
                )

    # Build trajectory_shift
    trajectory_shift = None
    if old_trajectory is not None and total_cycle_units is not None:
        new_trajectory = _compute_trajectory(
            account, cycle_start,
            old_readings + [{"units_since_last": units_since_last, "reading_value": effective_reading_value, "reading_date": body.reading_date}],
            category,
        )
        trajectory_shift = {"before": old_trajectory, "after": new_trajectory}

    return {
        "status": "success",
        "units_since_last": units_since_last,
        "estimated_bill": estimated_bill,
        "total_cycle_units": total_cycle_units,
        "trajectory_shift": trajectory_shift,
        "slab": {
            "current": current_slab,
            "units_to_next_boundary": units_to_next,
            "cost_if_crossed": cost_if_crossed,
        } if current_slab else None,
    }


@router.get("/readings/{consumer_account_id}")
async def get_reading_history(
    consumer_account_id: str,
    current_user: dict = Depends(get_current_user),
    limit: int = 30,
):
    account = _verify_ownership(consumer_account_id, current_user["user_id"])
    last_bill = _get_latest_bill(consumer_account_id)
    cycle_start = get_cycle_start(account, last_bill)

    result = (
        supabase.table("meter_readings")
        .select("*")
        .eq("consumer_account_id", consumer_account_id)
        .order("reading_date", desc=False)
        .limit(min(limit, 100))
        .execute()
    )
    rows = result.data or []
    enriched = []
    cumul_units = 0.0
    for i, row in enumerate(rows):
        raw = row["reading_date"]
        curr_date = raw if isinstance(raw, date) else date.fromisoformat(str(raw)[:10])

        # cumulative units up to this reading
        if i == 0:
            cumul_units = float(row["reading_value"])
        else:
            incr = row.get("units_since_last")
            cumul_units += float(incr) if incr is not None else 0

        days_from_start = (curr_date - cycle_start).days
        consumption_rate = round(cumul_units / days_from_start, 2) if days_from_start > 0 else None

        enriched.append({**row, "consumption_rate": consumption_rate})
    enriched.reverse()
    return {"readings": enriched}


@router.get("/summary/{consumer_account_id}")
async def get_consumption_summary(
    consumer_account_id: str,
    current_user: dict = Depends(get_current_user),
):
    account = _verify_ownership(consumer_account_id, current_user["user_id"])
    last_bill = _get_latest_bill(consumer_account_id)
    cycle_start = get_cycle_start(account, last_bill)
    today = date.today()

    # Get readings this cycle
    readings_result = (
        supabase.table("meter_readings")
        .select("*")
        .eq("consumer_account_id", consumer_account_id)
        .gte("reading_date", cycle_start.isoformat())
        .order("reading_date", desc=True)
        .execute()
    )
    readings = readings_result.data or []

    # Determine protected status
    is_protected = _is_protected_consumer(consumer_account_id) if account["utility_type"] == "electricity" else False
    category = "protected" if is_protected else "unprotected"

    # Extract units consumed from latest bill for input auto-fill
    bill_units_consumed = None
    if last_bill and last_bill.get("units_consumed") is not None:
        bill_units_consumed = float(last_bill["units_consumed"])

    # Compute previous cycle stats — use the bill from BEFORE this cycle started
    previous_daily_rate = None
    previous_total_units = None
    prev_bill_result = (
        supabase.table("bills")
        .select("*")
        .eq("consumer_account_id", consumer_account_id)
        .lt("billing_month", cycle_start.isoformat())
        .order("billing_month", desc=True)
        .limit(1)
        .execute()
    )
    prev_bill = prev_bill_result.data[0] if prev_bill_result.data else None
    if prev_bill and prev_bill.get("units_consumed") is not None:
        prev_units = float(prev_bill["units_consumed"])
        previous_total_units = prev_units
        previous_daily_rate = round(prev_units / 30, 2)

    # ── Build base response ────────────────────────────────────────────────
    traj = _compute_trajectory(account, cycle_start, readings, category, today) if readings else None

    response = {
        "consumer_account_id": consumer_account_id,
        "cycle_start": cycle_start.isoformat(),
        "total_units_so_far": traj["total_units"] if traj else 0,
        "daily_rate": traj["daily_rate"] if traj else 0,
        "days_elapsed": traj["days_elapsed"] if traj else 0,
        "days_remaining": traj["days_remaining"] if traj else 0,
        "projected_units": traj["projected_units"] if traj else 0,
        "estimated_bill": traj["estimated_bill"] if traj else 0,
        "bill_units_consumed": bill_units_consumed,
        "is_protected": is_protected,
        "readings_this_cycle": len(readings),
        "previous_total_units": previous_total_units,
        "previous_daily_rate": previous_daily_rate,
    }

    # Slab info (electricity only — gas/water have no slab structure in tariff table)
    if account["utility_type"] == "electricity":
        total_units = response["total_units_so_far"]
        slabs = get_active_tariffs(account["provider_code"], category)
        current_slab = get_current_slab(total_units, slabs)
        next_slab = get_next_slab(current_slab, slabs) if current_slab else None
        units_to_next = None
        if current_slab and current_slab["max"] is not None:
            units_to_next = max(0, current_slab["max"] - total_units + 1)
        response["current_slab"] = current_slab
        response["next_slab"] = {
            "threshold": next_slab["min"],
            "rate": next_slab["rate"],
            "units_away": units_to_next,
        } if next_slab and units_to_next is not None else None
    else:
        response["current_slab"] = None
        response["next_slab"] = None

    # Last reading
    if readings:
        sorted_asc = sorted(readings, key=lambda r: r["reading_date"])
        latest_r = sorted_asc[-1]
        response["last_reading"] = {
            "date": latest_r["reading_date"],
            "value": float(latest_r["reading_value"]),
        }
    else:
        response["last_reading"] = None

    # Latest reading snapshot (units/days/rate since last entry only)
    response["latest_reading_snapshot"] = _get_latest_snapshot(readings, account, category)

    # Consumption change vs previous month
    if previous_total_units is not None and previous_total_units > 0:
        change_pct = round((traj["total_units"] - previous_total_units) / previous_total_units * 100, 1) if traj else None
        response["consumption_change_pct"] = change_pct
        response["consumption_trend"] = "up" if change_pct and change_pct > 5 else ("down" if change_pct and change_pct < -5 else "stable")
    else:
        response["consumption_change_pct"] = None
        response["consumption_trend"] = None

    # Seasonal comparison — same month last year
    same_month_last_year_units = None
    last_year_same_month = cycle_start.replace(year=cycle_start.year - 1)
    if last_year_same_month <= date.today():
        try:
            last_year_result = (
                supabase.table("bills")
                .select("units_consumed")
                .eq("consumer_account_id", consumer_account_id)
                .eq("billing_month", last_year_same_month.isoformat())
                .single()
                .execute()
            )
            if last_year_result.data and last_year_result.data.get("units_consumed") is not None:
                same_month_last_year_units = float(last_year_result.data["units_consumed"])
        except APIError:
            pass
    response["same_month_last_year_units"] = same_month_last_year_units

    return response


@router.get("/trend/{consumer_account_id}")
async def get_consumption_trend(
    consumer_account_id: str,
    current_user: dict = Depends(get_current_user),
    months: int = 6,
):
    _verify_ownership(consumer_account_id, current_user["user_id"])
    six_months_ago = (date.today().replace(day=1) - relativedelta(months=months - 1)).isoformat()
    result = (
        supabase.table("bills")
        .select("billing_month, units_consumed, amount_payable, tariff_slab")
        .eq("consumer_account_id", consumer_account_id)
        .gte("billing_month", six_months_ago)
        .order("billing_month", desc=False)
        .execute()
    )
    return {"trend": result.data or []}


@router.get("/slab-alerts/{consumer_account_id}")
async def get_slab_alerts(
    consumer_account_id: str,
    current_user: dict = Depends(get_current_user),
):
    _verify_ownership(consumer_account_id, current_user["user_id"])
    result = (
        supabase.table("slab_alerts")
        .select("*")
        .eq("consumer_account_id", consumer_account_id)
        .order("alerted_at", desc=True)
        .limit(20)
        .execute()
    )
    return {"alerts": result.data or []}


# ─── Public helpers (consumable by other modules) ─────────────────────────────


def prune_readings_for_billing_month(consumer_account_id: str, billing_month: str):
    """Delete meter readings for a completed billing month only.

    Called from bills.py when a bill is fetched or marked paid.
    Skips the current active billing month so user readings aren't lost."""
    bill_month = datetime.strptime(billing_month, "%Y-%m-%d").date()
    current_month_start = date.today().replace(day=1)
    if bill_month >= current_month_start:
        return  # Don't prune the active cycle — user readings are still in progress
    next_month = (bill_month.replace(day=28) + timedelta(days=4)).replace(day=1)
    supabase.table("meter_readings")\
        .delete()\
        .eq("consumer_account_id", consumer_account_id)\
        .gte("reading_date", bill_month.isoformat())\
        .lt("reading_date", next_month.isoformat())\
        .execute()


# ─── Endpoints ─────────────────────────────────────────────────────────────────


@router.delete("/readings/{reading_id}")
async def delete_reading(
    reading_id: str,
    current_user: dict = Depends(get_current_user),
):
    result = (
        supabase.table("meter_readings")
        .select("id, user_id, consumer_account_id")
        .eq("id", reading_id)
        .single()
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Reading not found")
    if result.data["user_id"] != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    supabase.table("meter_readings").delete().eq("id", reading_id).execute()
    return {"status": "deleted"}


# ─── Internal ───────────────────────────────────────────────────────────────────


def _compute_trajectory(account: dict, cycle_start: date, readings: list, category: str, today: date | None = None) -> dict:
    """Compute cycle trajectory (total, daily rate, projection, bill) from a list of readings."""
    today = today or date.today()
    sorted_asc = sorted(readings, key=lambda r: r["reading_date"])
    first = sorted_asc[0]
    if first.get("units_since_last") is None or float(first["units_since_last"] or 0) == 0:
        total = float(first["reading_value"]) + sum(float(r.get("units_since_last") or 0) for r in sorted_asc[1:])
    else:
        total = sum(float(r.get("units_since_last") or 0) for r in readings)

    # Use the latest reading's date, not today's wall-clock time, so projection
    # reflects the user's actual consumption window.
    last_r = sorted_asc[-1]
    raw = last_r["reading_date"]
    last_date = date.fromisoformat(raw) if isinstance(raw, str) else raw
    days_elapsed = max(1, (last_date - cycle_start).days)
    _, total_days_in_month = calendar.monthrange(cycle_start.year, cycle_start.month)
    days_remaining = max(0, total_days_in_month - last_date.day)
    daily = round(total / days_elapsed, 2)
    projected = round(total + (daily * days_remaining), 2)
    bill = 0
    if account["utility_type"] == "electricity":
        bill_est = compute_electricity_bill(projected, account["provider_code"], category)
        bill = bill_est["total"]
    return {
        "total_units": total,
        "daily_rate": daily,
        "days_elapsed": days_elapsed,
        "days_remaining": days_remaining,
        "projected_units": projected,
        "estimated_bill": bill,
    }


def _get_latest_snapshot(readings: list, account: dict, category: str) -> dict | None:
    """Return only the latest reading's raw data — no difference computations."""
    if not readings:
        return None
    sorted_asc = sorted(readings, key=lambda r: r["reading_date"])
    latest_r = sorted_asc[-1]
    return {
        "reading_value": float(latest_r["reading_value"]),
        "reading_date": latest_r["reading_date"],
        "units_since_last": float(latest_r["units_since_last"] or 0),
    }


async def _get_cycle_units(
    consumer_account_id: str,
    cycle_start: date,
    current_reading_value: float | None = None,
) -> float:
    readings = (
        supabase.table("meter_readings")
        .select("reading_value, units_since_last")
        .eq("consumer_account_id", consumer_account_id)
        .gte("reading_date", cycle_start.isoformat())
        .order("reading_date", desc=False)
        .execute()
    )
    rows = readings.data or []
    if not rows:
        return current_reading_value or 0

    # Compute total from stored readings
    if rows[0].get("units_since_last") is not None and float(rows[0].get("units_since_last") or 0) > 0:
        total = sum(float(r["units_since_last"] or 0) for r in rows)
    else:
        total = float(rows[0]["reading_value"]) + sum(float(r.get("units_since_last") or 0) for r in rows[1:])

    # Include pending reading's delta (called before insert in submit_reading)
    if current_reading_value is not None:
        last_stored = float(rows[-1]["reading_value"])
        if current_reading_value >= last_stored:
            total += round(current_reading_value - last_stored, 2)

    return round(total, 2)


async def _check_and_insert_slab_alert(
    consumer_account_id: str,
    user_id: str,
    units_to_next: float,
    cost_if_crossed: float,
):
    ALERT_THRESHOLDS = [10, 20, 50]
    billing_period = date.today().replace(day=1).isoformat()

    for threshold in ALERT_THRESHOLDS:
        if units_to_next <= threshold:
            exists = (
                supabase.table("slab_alerts")
                .select("id")
                .eq("consumer_account_id", consumer_account_id)
                .eq("billing_period", billing_period)
                .eq("slab_threshold", threshold)
                .execute()
            )
            if exists.data:
                continue
            supabase.table("slab_alerts").insert({
                "consumer_account_id": consumer_account_id,
                "user_id": user_id,
                "billing_period": billing_period,
                "slab_threshold": threshold,
                "units_at_alert": units_to_next,
                "cost_if_crossed": cost_if_crossed,
            }).execute()
            break
