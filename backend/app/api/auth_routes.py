import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, status
from backend.app.auth import get_current_user, get_optional_user
from backend.app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication & User Session"])


@router.get(
    "/me",
    status_code=status.HTTP_200_OK,
    summary="Get Current Authenticated User Profile",
    response_description="Decoded Clerk User Context and Claims"
)
async def get_user_profile(user: Dict[str, Any] = Depends(get_current_user)):
    """
    Returns current user authentication status and profile claims extracted from Clerk JWT.
    """
    return {
        "status": "authenticated" if user.get("is_authenticated") else "guest",
        "user_id": user.get("user_id"),
        "email": user.get("email"),
        "first_name": user.get("first_name"),
        "last_name": user.get("last_name"),
        "picture": user.get("picture"),
        "is_authenticated": user.get("is_authenticated"),
        "claims": user.get("claims", {})
    }


@router.get(
    "/status",
    status_code=status.HTTP_200_OK,
    summary="Check Authentication System Status",
    response_description="Status of Clerk Authentication Provider"
)
async def auth_status(user: Dict[str, Any] = Depends(get_optional_user)):
    """
    Returns authentication configuration status and active session info if available.
    """
    return {
        "provider": "Clerk",
        "require_auth": settings.REQUIRE_AUTH,
        "clerk_configured": bool(settings.CLERK_PUBLISHABLE_KEY and "placeholder" not in settings.CLERK_PUBLISHABLE_KEY),
        "active_user_id": user.get("user_id") if user else None,
        "is_logged_in": user.get("is_authenticated", False) if user else False
    }


@router.get(
    "/token-info",
    status_code=status.HTTP_200_OK,
    summary="Inspect Active Access Token & Expiration",
    response_description="Metadata regarding the decoded Clerk Access Token"
)
async def token_info(user: Dict[str, Any] = Depends(get_current_user)):
    """
    Inspects active Clerk JWT Access Token claims, issued timestamp (iat), expiration (exp),
    and remaining time-to-live (ttl_seconds).
    """
    claims = user.get("claims", {})
    import time
    now = int(time.time())
    exp = claims.get("exp")
    iat = claims.get("iat")

    return {
        "user_id": user.get("user_id"),
        "is_authenticated": user.get("is_authenticated"),
        "issued_at": iat,
        "expires_at": exp,
        "ttl_seconds": (exp - now) if exp else None,
        "token_type": "Bearer Access Token (Clerk RS256 JWT)",
        "refresh_token_strategy": "Managed automatically client-side by Clerk Session Cookie / useAuth().getToken({ skipCache: true })"
    }

