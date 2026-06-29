"""P11 Solar Dashboard Module (M6) — API endpoints."""

from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, field_validator

from app.core.auth import get_current_user
from app.core.security import encrypt, decrypt
from app.core.supabase import supabase
from app.services.solar.alerts import create_alert, get_user_alerts, mark_alert_read, mark_alert_dismissed
from app.services.solar.dashboard import get_dashboard_data, get_installations_list

router = APIRouter(prefix="/api/v1/solar", tags=["solar"])


# ─── Schemas ────────────────────────────────────────────────────────────────────


class SolarCreate(BaseModel):
    model_config = ConfigDict(str_to_lower=False)

    home_id: str | None = None
    inverter_brand: str
    inverter_model: str | None = None
    system_size_kw: float
    panel_count: int | None = None
    panel_wattage: int | None = None
    installation_date: date | None = None
    system_cost_pkr: float | None = None
    net_metering_enabled: bool = False
    net_metering_ref: str | None = None

    @field_validator("inverter_brand")
    @classmethod
    def valid_brand(cls, v: str) -> str:
        allowed = {"growatt", "solis", "huawei"}
        if v.lower() not in allowed:
            raise ValueError("inverter_brand must be one of: growatt, solis, huawei")
        return v.lower()

    @field_validator("system_size_kw")
    @classmethod
    def positive_size(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("system_size_kw must be positive")
        if v > 100:
            raise ValueError("system_size_kw must be ≤ 100.0")
        return v

    @field_validator("system_cost_pkr")
    @classmethod
    def positive_cost(cls, v: float | None) -> float | None:
        if v is not None and v <= 0:
            raise ValueError("system_cost_pkr must be positive")
        if v is not None and v > 99999999:
            raise ValueError("system_cost_pkr must be ≤ 99,999,999")
        return v

    @field_validator("panel_count")
    @classmethod
    def valid_panel_count(cls, v: int | None) -> int | None:
        if v is not None and (v < 1 or v > 10000):
            raise ValueError("panel_count must be between 1 and 10000")
        return v

    @field_validator("panel_wattage")
    @classmethod
    def valid_wattage(cls, v: int | None) -> int | None:
        if v is not None and (v < 1 or v > 1000):
            raise ValueError("panel_wattage must be between 1 and 1000")
        return v

    @field_validator("net_metering_ref")
    @classmethod
    def valid_ref(cls, v: str | None) -> str | None:
        if v is not None and len(v) > 100:
            raise ValueError("net_metering_ref must be ≤ 100 chars")
        return v


class InverterConnect(BaseModel):
    api_username: str
    api_password: str
    plant_id: str | None = None

    @field_validator("api_username")
    @classmethod
    def valid_username(cls, v: str) -> str:
        if len(v) > 255:
            raise ValueError("api_username must be ≤ 255 chars")
        return v

    @field_validator("api_password")
    @classmethod
    def valid_password(cls, v: str) -> str:
        if len(v) > 255:
            raise ValueError("api_password must be ≤ 255 chars")
        return v

    @field_validator("plant_id")
    @classmethod
    def valid_plant_id(cls, v: str | None) -> str | None:
        if v is not None and len(v) > 255:
            raise ValueError("plant_id must be ≤ 255 chars")
        return v


# ─── Endpoints ────────────────────────────────────────────────────────────────


@router.post("/installations", status_code=201)
async def create_solar_installation(
    body: SolarCreate,
    current_user: dict = Depends(get_current_user),
):
    """Create a new solar installation."""
    user_id = current_user["user_id"]

    existing = (
        supabase.table("solar_installations")
        .select("id")
        .eq("user_id", user_id)
        .execute()
    )
    if len(existing.data or []) >= 3:
        profile = (
            supabase.table("profiles")
            .select("premium")
            .eq("id", user_id)
            .single()
            .execute()
        )
        if not profile.data or not profile.data.get("premium"):
            raise HTTPException(
                status_code=403,
                detail="Free tier limit: max 3 solar installations. Upgrade to Premium.",
            )

    payload = {
        **body.model_dump(),
        "user_id": user_id,
        "inverter_brand": body.inverter_brand,
    }
    result = (
        supabase.table("solar_installations")
        .insert(payload)
        .execute()
    )
    return result.data[0] if result.data else {}


@router.post("/installations/{installation_id}/connect")
async def connect_inverter(
    installation_id: str,
    body: InverterConnect,
    current_user: dict = Depends(get_current_user),
):
    """Store encrypted credentials and test inverter adapter."""
    user_id = current_user["user_id"]

    installation = (
        supabase.table("solar_installations")
        .select("*")
        .eq("id", installation_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    if not installation.data:
        raise HTTPException(status_code=404, detail="Solar installation not found")

    from app.services.solar.base import SolarCredentials

    encrypted_username = encrypt(body.api_username)
    encrypted_password = encrypt(body.api_password)

    (
        supabase.table("solar_installations")
        .update({
            "api_username_encrypted": encrypted_username,
            "api_password_encrypted": encrypted_password,
            "api_token_encrypted": encrypt(body.plant_id or ""),
        })
        .eq("id", installation_id)
        .execute()
    )

    brand = installation.data.get("inverter_brand", "").lower()
    if brand == "growatt":
        from app.services.solar.growatt import GrowattAdapter
        adapter = GrowattAdapter()
    elif brand == "solis":
        from app.services.solar.solis import SolisAdapter
        adapter = SolisAdapter()
    elif brand == "huawei":
        from app.services.solar.huawei import HuaweiAdapter
        adapter = HuaweiAdapter()
    else:
        raise HTTPException(status_code=400, detail=f"Unknown inverter brand: {brand}")

    credentials = SolarCredentials(
        username=body.api_username,
        password=body.api_password,
        plant_id=body.plant_id,
    )
    try:
        result = await adapter.authenticate(credentials)
        if not result.success:
            raise HTTPException(status_code=502, detail=f"Authentication failed: {result.error or 'invalid credentials'}")

        today = date.today()
        production = await adapter.fetch_daily_production(installation.data, today)
        dashboard = await get_dashboard_data(installation_id, user_id)
        return {
            "status": "connected",
            "installation": dashboard["installation"],
            "dashboard": dashboard,
        }
    except HTTPException:
        raise
    except NotImplementedError:
        raise HTTPException(status_code=503, detail="Adapter not implemented for this brand yet")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Connection test failed: {str(e)}")


@router.get("/installations")
async def list_solar_installations(current_user: dict = Depends(get_current_user)):
    """List all user's solar installations."""
    user_id = current_user["user_id"]
    return get_installations_list(user_id)


@router.get("/dashboard/{installation_id}")
async def get_solar_dashboard(
    installation_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get full dashboard data for a specific installation."""
    user_id = current_user["user_id"]
    return get_dashboard_data(installation_id, user_id)


@router.get("/installations/{installation_id}/production")
async def get_solar_production(
    installation_id: str,
    start: str = Query(..., pattern=r"\d{4}-\d{2}-\d{2}"),
    end: str = Query(..., pattern=r"\d{4}-\d{2}-\d{2}"),
    current_user: dict = Depends(get_current_user),
):
    """Get production history for an installation."""
    user_id = current_user["user_id"]

    installation = (
        supabase.table("solar_installations")
        .select("id")
        .eq("id", installation_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    if not installation.data:
        raise HTTPException(status_code=404, detail="Solar installation not found")

    readings = (
        supabase.table("solar_daily_production")
        .select("date, production_kwh, self_consumed_kwh, exported_kwh, imported_kwh, peak_power_kw")
        .eq("solar_installation_id", installation_id)
        .gte("date", start)
        .lte("date", end)
        .order("date", desc=False)
        .execute()
    )
    return readings.data or []


@router.get("/alerts")
async def list_solar_alerts(
    installation_id: str | None = None,
    current_user: dict = Depends(get_current_user),
):
    """List solar alerts."""
    user_id = current_user["user_id"]
    return get_user_alerts(user_id, installation_id)


@router.put("/alerts/{alert_id}/read")
async def mark_alert_read(
    alert_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Mark alert as read."""
    user_id = current_user["user_id"]
    return mark_alert_read(alert_id, user_id)


@router.put("/alerts/{alert_id}/dismiss")
async def dismiss_alert(
    alert_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Dismiss alert."""
    user_id = current_user["user_id"]
    return mark_alert_dismissed(alert_id, user_id)


@router.put("/maintenance/{installation_id}")
async def mark_maintenance_done(
    installation_id: str,
    body: dict,
    current_user: dict = Depends(get_current_user),
):
    """Mark maintenance done and schedule next cleaning."""
    user_id = current_user["user_id"]

    last_maintenance_date = body.get("last_maintenance_date")
    if not last_maintenance_date:
        raise HTTPException(status_code=400, detail="last_maintenance_date is required")
    try:
        parsed_date = date.fromisoformat(last_maintenance_date)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid date format, use YYYY-MM-DD")

    (
        supabase.table("solar_installations")
        .update({"last_maintenance_at": parsed_date.isoformat()})
        .eq("id", installation_id)
        .eq("user_id", user_id)
        .execute()
    )

    system_size = (
        supabase.table("solar_installations")
        .select("system_size_kw")
        .eq("id", installation_id)
        .single()
        .execute()
    )
    system_size_kw = system_size.data["system_size_kw"] if system_size.data else 10.0

    from app.services.solar.alerts import get_cleaning_reminder_days
    days_until_cleaning = get_cleaning_reminder_days(system_size_kw)
    next_cleaning = parsed_date.replace(day=min(parsed_date.day + days_until_cleaning, 28))

    create_alert(
        installation_id,
        user_id,
        "cleaning_due",
        "info",
        f"Cleaning due in {days_until_cleaning} days",
        f"Schedule solar panel cleaning to maintain optimal performance. Next cleaning scheduled for {next_cleaning}.",
    )
    return {"status": "ok", "next_cleaning_due": next_cleaning.isoformat()}


@router.delete("/installations/{installation_id}")
async def delete_solar_installation(
    installation_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Delete a solar installation."""
    user_id = current_user["user_id"]

    result = (
        supabase.table("solar_installations")
        .select("id")
        .eq("id", installation_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Solar installation not found")

    (
        supabase.table("solar_installations")
        .delete()
        .eq("id", installation_id)
        .execute()
    )
    return {"status": "ok"}
