from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import get_current_user
from app.core.supabase import supabase
from app.services.estimators.electricity import estimate_electricity
from app.services.estimators.gas import estimate_gas
from app.services.estimators.water import estimate_water
from app.services.estimators.schemas import (
    ElectricityEstimateInput,
    GasEstimateInput,
    WaterEstimateInput,
    EstimateResult,
)
from app.services.tariff import compute_electricity_bill, get_cycle_start

router = APIRouter(prefix="/api/v1/estimates", tags=["estimates"])


@router.post("/electricity", response_model=EstimateResult)
async def estimate_electricity_route(body: ElectricityEstimateInput):
    return estimate_electricity(body)


@router.post("/gas", response_model=EstimateResult)
async def estimate_gas_route(body: GasEstimateInput):
    return estimate_gas(body)


@router.post("/water", response_model=EstimateResult)
async def estimate_water_route(body: WaterEstimateInput):
    return estimate_water(body)


@router.post("/from-consumption/{consumer_account_id}", response_model=EstimateResult)
async def estimate_from_consumption(
    consumer_account_id: str,
    current_user: dict = Depends(get_current_user),
):
    result = (
        supabase.table("consumer_accounts")
        .select("*")
        .eq("id", consumer_account_id)
        .eq("user_id", current_user["user_id"])
        .single()
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Consumer account not found")
    account = result.data

    if account["utility_type"] == "water":
        raise HTTPException(
            status_code=400,
            detail="Water estimation from readings is not available (flat-rate billing).",
        )

    readings_result = (
        supabase.table("meter_readings")
        .select("reading_value, reading_date")
        .eq("consumer_account_id", consumer_account_id)
        .order("reading_date", desc=True)
        .limit(2)
        .execute()
    )
    readings = readings_result.data or []
    if len(readings) < 2:
        raise HTTPException(
            status_code=400,
            detail="Need at least 2 meter readings to estimate from consumption",
        )

    latest = float(readings[0]["reading_value"])
    prev = float(readings[1]["reading_value"])
    if latest <= prev:
        raise HTTPException(status_code=400, detail="Latest reading must be greater than previous reading")

    units = latest - prev

    if account["utility_type"] == "gas":
        inp = GasEstimateInput(provider_code=account["provider_code"], consumption_mmbtu=units)
        return estimate_gas(inp)

    # Electricity
    category = "protected" if account.get("protected_customer") else "unprotected"
    raw = compute_electricity_bill(units, account["provider_code"], category)

    from app.services.estimators.schemas import SlabLine
    from datetime import date

    breakdown = [
        SlabLine(label=s["slab"], units=s["units"], rate=s["rate"], amount=s["cost"])
        for s in raw["slabs"]
    ]

    taxes = raw["fc_surcharge"] + raw["gst"]
    total = raw["energy_charges"] + taxes + raw["meter_rent"]
    today = date.today()
    tariff_version = f"{today.year}-Q{(today.month - 1) // 3 + 1}"

    return EstimateResult(
        provider_code=account["provider_code"],
        utility_type="electricity",
        units=units,
        estimated_total=round(total, 2),
        tariff_version=tariff_version,
        breakdown=breakdown,
        taxes=round(taxes, 2),
        slab_warning=None,
    )
