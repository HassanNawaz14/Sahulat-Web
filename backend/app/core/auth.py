import logging
from functools import lru_cache
from typing import Any

import httpx
from fastapi import Depends, HTTPException, Header
from jose import jwk, jwt
from jose.exceptions import JWTError, ExpiredSignatureError

from app.core.config import settings

logger = logging.getLogger("sahulat.auth")

JWKS_URL = f"{settings.supabase_url}/auth/v1/.well-known/jwks.json"


@lru_cache(maxsize=1)
def _get_jwks_key() -> dict[str, Any] | None:
    """Fetch and cache the JWKS signing key from Supabase."""
    try:
        resp = httpx.get(JWKS_URL, timeout=10)
        resp.raise_for_status()
        keys = resp.json().get("keys", [])
        if keys:
            return keys[0]
    except Exception as e:
        logger.warning("Failed to fetch JWKS: %s", e)
    return None


def _verify_token(token: str) -> dict[str, Any]:
    """Verify a Supabase JWT using JWKS (ES256) or fallback to HS256."""
    # Try ES256 with JWKS key first
    jwk_data = _get_jwks_key()
    if jwk_data:
        try:
            key = jwk.construct(jwk_data)
            return jwt.decode(token, key, algorithms=["ES256"], audience="authenticated")
        except ExpiredSignatureError:
            raise
        except JWTError as e:
            logger.debug("ES256 verification failed: %s", e)

    # Fallback to HS256 with JWT secret
    try:
        return jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
    except ExpiredSignatureError:
        raise
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


async def get_current_user(authorization: str = Header(...)) -> dict:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.removeprefix("Bearer ")
    try:
        payload = _verify_token(token)
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except HTTPException:
        raise
    except Exception as e:
        logger.warning("Token verification failed: %s", e)
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token: missing user identity")
    return {
        "user_id": user_id,
        "email": payload.get("email"),
        "phone": payload.get("phone"),
    }


async def get_admin_user(current_user: dict = Depends(get_current_user)) -> dict:
    admin_ids = [uid.strip() for uid in settings.admin_user_ids.split(",") if uid.strip()]
    if current_user["user_id"] not in admin_ids:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


async def enforce_home_limit(user_id: str, db) -> None:
    result = db.table("profiles").select("premium").eq("id", user_id).execute()
    if result.data and result.data[0].get("premium"):
        return
    count_result = db.table("homes").select("id", count="exact").eq("user_id", user_id).execute()
    if count_result.count is not None and count_result.count >= 5:
        raise HTTPException(
            status_code=403,
            detail="Free tier limit reached: max 5 homes. Upgrade to Premium.",
        )
