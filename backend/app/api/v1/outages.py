from datetime import date, datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, field_validator

from app.core.auth import get_current_user
from app.core.supabase import supabase
from app.scrapers.common.feeder_area_map import FEEDER_AREA_MAP, default_city
from app.services import compute_confidence

router = APIRouter(prefix="/api/v1", tags=["outages"])

# ─── Schemas ──────────────────────────────────────────────────────────────────


class CommunityReportCreate(BaseModel):
    utility_type: str
    provider_code: Optional[str] = None
    home_id: Optional[str] = None
    report_type: str = "electricity_outage"
    severity: str = "medium"
    note: Optional[str] = None

    @field_validator("utility_type")
    @classmethod
    def valid_utility(cls, v: str):
        if v not in ("electricity", "gas", "water", "internet"):
            raise ValueError("utility_type must be electricity, gas, water, or internet")
        return v

    @field_validator("severity")
    @classmethod
    def valid_severity(cls, v: str):
        if v not in ("low", "medium", "high"):
            raise ValueError("severity must be low, medium, or high")
        return v

    @field_validator("report_type")
    @classmethod
    def valid_report_type(cls, v: str):
        allowed = (
            "electricity_outage", "voltage_issue", "gas_low_pressure",
            "gas_outage", "water_shortage", "dirty_water",
            "internet_down", "bill_issue", "restored",
        )
        if v not in allowed:
            raise ValueError(f"report_type must be one of {allowed}")
        return v

    @field_validator("note")
    @classmethod
    def note_length(cls, v: Optional[str]):
        if v and len(v) > 200:
            raise ValueError("note must be 200 characters or less")
        return v


class FeederUpdate(BaseModel):
    consumer_account_id: str
    feeder_name: str


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _outage_status(start_time: str, end_time: str) -> str:
    now = datetime.now(timezone.utc)
    start = datetime.fromisoformat(start_time)
    end = datetime.fromisoformat(end_time)
    if now > end:
        return "expired"
    if now >= start and now <= end:
        return "active"
    return "upcoming"


# ─── Endpoints ────────────────────────────────────────────────────────────────


@router.get("/outages/schedule/{consumer_account_id}")
async def get_schedule(
    consumer_account_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get scheduled outages for the next 3 days for the user's area/feeder."""
    # 1. Get account with home details
    account = (
        supabase.table("consumer_accounts")
        .select("*, homes!left(*)")
        .eq("id", consumer_account_id)
        .eq("user_id", current_user["user_id"])
        .execute()
    )
    if not account.data:
        raise HTTPException(404, "Consumer account not found")

    acc = account.data[0]
    home = acc.get("homes") or {}
    feeder_name = home.get("feeder_name") or ""
    city = home.get("city") or acc.get("city") or default_city(acc["provider_code"])
    area = home.get("area") or ""

    today = date.today()
    dates = [today, today + timedelta(days=1), today + timedelta(days=2)]

    # 2. Query by feeder_name if set, otherwise by area
    all_schedules = []
    if feeder_name:
        feeder_results = (
            supabase.table("outage_schedules")
            .select("*")
            .eq("provider_code", acc["provider_code"])
            .eq("feeder_name", feeder_name)
            .gte("schedule_date", today.isoformat())
            .lte("schedule_date", dates[2].isoformat())
            .order("schedule_date")
            .execute()
        )
        all_schedules = feeder_results.data or []

    if not all_schedules and area:
        area_slug = area.strip().lower().replace(" ", "-")
        area_results = (
            supabase.table("outage_schedules")
            .select("*")
            .eq("provider_code", acc["provider_code"])
            .contains("area_tags", [area_slug])
            .gte("schedule_date", today.isoformat())
            .lte("schedule_date", dates[2].isoformat())
            .order("schedule_date")
            .execute()
        )
        all_schedules = area_results.data or []

    # 3. Group by date and compute status
    grouped: dict[str, list[dict]] = {"today": [], "tomorrow": [], "day_after": []}
    current_outage = None
    next_outage = None

    for sched in all_schedules:
        slots = sched.get("slots") or []
        for slot in slots:
            start_str = slot.get("start", "")
            end_str = slot.get("end", "")
            if not start_str or not end_str:
                continue

            status = _outage_status(start_str, end_str)
            entry = {
                "id": sched["id"],
                "provider_code": sched["provider_code"],
                "feeder_name": sched["feeder_name"],
                "start_time": start_str,
                "end_time": end_str,
                "outage_type": "scheduled",
                "confidence_score": float(sched.get("confidence_score") or 0.82),
                "status": status,
            }

            sched_date = sched.get("schedule_date", "")
            if sched_date == today.isoformat():
                grouped["today"].append(entry)
            elif sched_date == dates[1].isoformat():
                grouped["tomorrow"].append(entry)
            else:
                grouped["day_after"].append(entry)

            if status == "active" and current_outage is None:
                current_outage = entry
            if status == "upcoming" and next_outage is None:
                next_outage = entry

    return {
        **grouped,
        "current_outage": current_outage,
        "next_outage": next_outage,
        "feeder_name": feeder_name,
        "feeder_set": bool(feeder_name),
    }


@router.get("/outages/community")
async def get_community_reports(
    city: Optional[str] = Query(None),
    area: Optional[str] = Query(None),
    utility_type: Optional[str] = Query(None, alias="utility_type"),
    current_user: dict = Depends(get_current_user),
):
    """Get active community outage reports, optionally filtered by city/area."""
    query = (
        supabase.table("community_outage_reports")
        .select("*")
        .or_("expires_at.is.null,expires_at.gt.now()")
        .eq("is_restored", False)
    )

    if city:
        query = query.eq("city", city)
    if area:
        query = query.eq("area_slug", area.strip().lower().replace(" ", "-"))
    if utility_type:
        query = query.eq("utility_type", utility_type)

    result = query.order("created_at", desc=True).limit(50).execute()
    reports = result.data or []

    # Cluster by city + area_slug + utility_type
    clusters: dict[str, dict] = {}
    for r in reports:
        key = f"{r['city']}|{r['area_slug']}|{r['utility_type']}"
        if key not in clusters:
            clusters[key] = {
                "id": r["id"],
                "utility_type": r["utility_type"],
                "report_type": r.get("report_type", "electricity_outage"),
                "city": r["city"],
                "area": r["area"],
                "severity": r.get("severity", "medium"),
                "status": "active",
                "confidence_score": compute_confidence(1),
                "report_count": 1,
                "created_at": r["created_at"],
                "expires_at": r.get("expires_at"),
            }
        else:
            clusters[key]["report_count"] += 1
            # Update confidence
            clusters[key]["confidence_score"] = compute_confidence(clusters[key]["report_count"])

    return {"reports": list(clusters.values())}


@router.post("/outages/reports")
async def create_report(
    body: CommunityReportCreate,
    current_user: dict = Depends(get_current_user),
):
    """Submit a community outage report."""
    user_id = current_user["user_id"]

    # 1. Rate limit: max 1 report per user per utility per 30 minutes
    thirty_min_ago = (datetime.utcnow() - timedelta(minutes=30)).isoformat()
    recent = (
        supabase.table("community_outage_reports")
        .select("id")
        .eq("user_id", user_id)
        .eq("utility_type", body.utility_type)
        .gte("created_at", thirty_min_ago)
        .execute()
    )
    if recent.data and len(recent.data) >= 1:
        raise HTTPException(429, f"You already reported a {body.utility_type} outage in the last 30 minutes")

    # 2. Get city and area from home or profile
    city = ""
    area = ""
    area_slug = ""
    provider_code = body.provider_code or ""

    if body.home_id:
        home = supabase.table("homes").select("city, area").eq("id", body.home_id).eq("user_id", user_id).execute()
        if home.data:
            city = home.data[0].get("city") or ""
            area = home.data[0].get("area") or ""

    if not city:
        profile = supabase.table("profiles").select("city, area").eq("id", user_id).execute()
        if profile.data:
            city = profile.data[0].get("city") or ""
            area = profile.data[0].get("area") or ""

    if not city:
        raise HTTPException(400, "Please set your city and area in profile settings first")

    area_slug = area.strip().lower().replace(" ", "-") if area else "unknown"

    # 3. Insert report
    expires_at = (datetime.utcnow() + timedelta(hours=3)).isoformat()
    result = (
        supabase.table("community_outage_reports")
        .insert({
            "user_id": user_id,
            "utility_type": body.utility_type,
            "provider_code": provider_code or None,
            "home_id": body.home_id or None,
            "city": city,
            "area": area,
            "area_slug": area_slug,
            "report_type": body.report_type,
            "severity": body.severity,
            "description": body.note or None,
            "expires_at": expires_at,
        })
        .execute()
    )

    if not result.data:
        raise HTTPException(500, "Failed to create report")

    report = result.data[0]

    # 4. Compute confidence score based on other active reports in same area
    same_area = (
        supabase.table("community_outage_reports")
        .select("id")
        .eq("city", city)
        .eq("area_slug", area_slug)
        .eq("utility_type", body.utility_type)
        .eq("is_restored", False)
        .execute()
    )
    report_count = len(same_area.data or [])
    confidence = compute_confidence(report_count)

    return {
        "id": report["id"],
        "status": "active",
        "confidence_score": confidence,
        "expires_at": expires_at,
    }


@router.post("/outages/reports/{report_id}/restore")
async def restore_report(
    report_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Mark a community outage report as restored."""
    report = (
        supabase.table("community_outage_reports")
        .select("*")
        .eq("id", report_id)
        .eq("user_id", current_user["user_id"])
        .execute()
    )
    if not report.data:
        raise HTTPException(404, "Report not found or not owned by you")

    result = (
        supabase.table("community_outage_reports")
        .update({
            "is_restored": True,
            "restored_at": datetime.utcnow().isoformat(),
        })
        .eq("id", report_id)
        .execute()
    )

    return {"status": "restored", "restored_at": result.data[0]["restored_at"] if result.data else None}


@router.patch("/outages/feeder")
async def set_feeder(
    body: FeederUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Set the feeder name on the user's home associated with a consumer account."""
    account = (
        supabase.table("consumer_accounts")
        .select("home_id")
        .eq("id", body.consumer_account_id)
        .eq("user_id", current_user["user_id"])
        .execute()
    )
    if not account.data:
        raise HTTPException(404, "Consumer account not found")

    home_id = account.data[0].get("home_id")
    if not home_id:
        raise HTTPException(400, "Consumer account is not linked to a home")

    supabase.table("homes").update({
        "feeder_name": body.feeder_name,
        "updated_at": datetime.utcnow().isoformat(),
    }).eq("id", home_id).execute()

    return {"status": "ok", "feeder_name": body.feeder_name}


@router.get("/outages/feeders")
async def search_feeders(
    provider_code: str = Query(...),
    city: Optional[str] = Query(None),
    q: Optional[str] = Query(None, min_length=1),
):
    """Autocomplete feeders by provider and city."""
    # Query the outage_schedules table for distinct feeder_name/feeder_code
    query = (
        supabase.table("outage_schedules")
        .select("feeder_code, feeder_name")
        .eq("provider_code", provider_code)
    )

    if city:
        query = query.eq("city", city)

    result = query.execute()
    feeders = result.data or []

    # Deduplicate
    seen: set[str] = set()
    unique_feeders = []
    for f in feeders:
        key = f["feeder_name"]
        if key in seen:
            continue
        seen.add(key)
        if q:
            if q.lower() in key.lower() or q.lower() in (f.get("feeder_code") or "").lower():
                unique_feeders.append(f)
        else:
            unique_feeders.append(f)

    return {"feeders": unique_feeders[:50]}
