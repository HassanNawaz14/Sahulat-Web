from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from postgrest import APIError

from app.core.auth import get_current_user, enforce_home_limit
from app.core.supabase import supabase

router = APIRouter(prefix="/auth", tags=["auth"])


class UpdateProfileRequest(BaseModel):
    full_name: str | None = None
    city: str | None = None
    area: str | None = None
    preferred_lang: str | None = None
    avatar_url: str | None = None


class CreateHomeRequest(BaseModel):
    name: str
    address: str | None = None
    city: str
    area: str | None = None


class UpdateHomeRequest(BaseModel):
    name: str | None = None
    address: str | None = None
    city: str | None = None
    area: str | None = None
    is_default: bool | None = None


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]
    try:
        profile = supabase.table("profiles").select("*").eq("id", user_id).single().execute()
    except APIError:
        profile = type('obj', (object,), {'data': None})()
    homes = supabase.table("homes").select("*").eq("user_id", user_id).execute()
    return {
        "profile": profile.data if profile.data else None,
        "homes": homes.data if homes.data else [],
    }


@router.patch("/profile")
async def update_profile(
    body: UpdateProfileRequest,
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["user_id"]
    update_data = body.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    result = supabase.table("profiles").update(update_data).eq("id", user_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"profile": result.data[0]}


@router.post("/onboarding/complete")
async def complete_onboarding(
    body: UpdateProfileRequest,
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["user_id"]
    if not body.city or not body.full_name:
        raise HTTPException(status_code=400, detail="full_name and city are required")
    update_data = body.model_dump(exclude_none=True)
    profile = supabase.table("profiles").update(update_data).eq("id", user_id).execute()
    if not profile.data:
        raise HTTPException(status_code=404, detail="Profile not found")
    homes_result = (
        supabase.table("homes")
        .insert({
            "user_id": user_id,
            "name": "Home",
            "city": body.city,
            "area": body.area or "",
            "is_default": True,
        })
        .execute()
    )
    return {
        "profile": profile.data[0],
        "home": homes_result.data[0] if homes_result.data else None,
    }


@router.post("/delete-account")
async def delete_account(current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]
    supabase.auth.admin.delete_user(user_id)
    return {"message": "Account deleted"}


@router.get("/homes")
async def list_homes(current_user: dict = Depends(get_current_user)):
    result = supabase.table("homes").select("*").eq("user_id", current_user["user_id"]).execute()
    return {"homes": result.data or []}


@router.post("/homes")
async def create_home(
    body: CreateHomeRequest,
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["user_id"]
    await enforce_home_limit(user_id, supabase)
    existing_default = (
        supabase.table("homes")
        .select("id")
        .eq("user_id", user_id)
        .eq("is_default", True)
        .execute()
    )
    is_default = len(existing_default.data) == 0
    result = (
        supabase.table("homes")
        .insert({
            "user_id": user_id,
            "name": body.name,
            "address": body.address or "",
            "city": body.city,
            "area": body.area or "",
            "is_default": is_default,
        })
        .execute()
    )
    return {"home": result.data[0]}


@router.patch("/homes/{home_id}")
async def update_home(
    home_id: str,
    body: UpdateHomeRequest,
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["user_id"]
    update_data = body.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    if "is_default" in update_data and update_data["is_default"]:
        supabase.table("homes").update({"is_default": False}).eq("user_id", user_id).eq("is_default", True).execute()
    result = (
        supabase.table("homes")
        .update(update_data)
        .eq("id", home_id)
        .eq("user_id", user_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Home not found")
    return {"home": result.data[0]}


@router.delete("/homes/{home_id}")
async def delete_home(
    home_id: str,
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["user_id"]
    result = supabase.table("homes").delete().eq("id", home_id).eq("user_id", user_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Home not found")
    return {"message": "Home deleted"}
