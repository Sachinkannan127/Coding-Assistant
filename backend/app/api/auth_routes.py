import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from backend.app.auth import (
    get_current_user,
    get_optional_user,
    create_access_token,
    create_refresh_token,
    decode_custom_token
)
from backend.app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication & User Session"])


class TokenIssueRequest(BaseModel):
    user_id: str
    email: Optional[str] = "user@codepilot.local"
    first_name: Optional[str] = "User"
    last_name: Optional[str] = ""


class RefreshTokenRequest(BaseModel):
    refresh_token: str


@router.post(
    "/token",
    status_code=status.HTTP_200_OK,
    summary="Issue Access & Refresh Tokens",
    response_description="Access Token (60 min) and Refresh Token (7 days)"
)
async def issue_tokens(body: TokenIssueRequest):
    """
    Issues a new Access Token (valid for 60 min) and Refresh Token (valid for 7 days).
    """
    user_data = {
        "sub": body.user_id,
        "user_id": body.user_id,
        "email": body.email,
        "first_name": body.first_name,
        "last_name": body.last_name
    }

    access_token = create_access_token(user_data)
    refresh_token = create_refresh_token(user_data)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in_seconds": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "refresh_token_expires_in_days": settings.REFRESH_TOKEN_EXPIRE_DAYS,
        "user": user_data
    }


@router.post(
    "/refresh",
    status_code=status.HTTP_200_OK,
    summary="Refresh Access Token using 7-Day Refresh Token",
    response_description="Newly issued Access Token"
)
async def refresh_access_token(body: RefreshTokenRequest):
    """
    Validates 7-day Refresh Token and issues a new Access Token.
    """
    payload = decode_custom_token(body.refresh_token, expected_type="refresh")

    user_data = {
        "sub": payload.get("sub") or payload.get("user_id"),
        "user_id": payload.get("user_id") or payload.get("sub"),
        "email": payload.get("email"),
        "first_name": payload.get("first_name", ""),
        "last_name": payload.get("last_name", "")
    }

    new_access_token = create_access_token(user_data)

    return {
        "access_token": new_access_token,
        "token_type": "bearer",
        "expires_in_seconds": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


@router.get(
    "/me",
    status_code=status.HTTP_200_OK,
    summary="Get Current Authenticated User Profile",
    response_description="Decoded User Context and Claims"
)
async def get_user_profile(user: Dict[str, Any] = Depends(get_current_user)):
    """
    Returns current user authentication status and profile claims extracted from JWT.
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
    response_description="Status of Authentication Provider"
)
async def auth_status(user: Dict[str, Any] = Depends(get_optional_user)):
    """
    Returns authentication configuration status and active session info if available.
    """
    return {
        "provider": "JWT + Clerk Hybrids",
        "require_auth": settings.REQUIRE_AUTH,
        "refresh_token_validity_days": settings.REFRESH_TOKEN_EXPIRE_DAYS,
        "clerk_configured": bool(settings.CLERK_PUBLISHABLE_KEY and settings.CLERK_PUBLISHABLE_KEY.strip().startswith("pk_")),
        "active_user_id": user.get("user_id") if user else None,
        "is_logged_in": user.get("is_authenticated", False) if user else False
    }


@router.get(
    "/token-info",
    status_code=status.HTTP_200_OK,
    summary="Inspect Active Access Token & Expiration",
    response_description="Metadata regarding the decoded Access Token"
)
async def token_info(user: Dict[str, Any] = Depends(get_current_user)):
    """
    Inspects active JWT Access Token claims, issued timestamp (iat), expiration (exp),
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
        "token_type": "Bearer Access Token",
        "refresh_token_validity": "7 Days"
    }
