import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import jwt
from jwt import PyJWKClient
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from backend.app.config import settings

logger = logging.getLogger(__name__)

# HTTP Bearer Scheme for Authorization header extraction
security_scheme = HTTPBearer(auto_error=False)

# In-memory cache for PyJWKClients keyed by JWKS URL
_jwks_clients: Dict[str, PyJWKClient] = {}


def get_jwks_client(jwks_url: str) -> PyJWKClient:
    """Retrieves or creates a cached PyJWKClient for a given JWKS URL."""
    if jwks_url not in _jwks_clients:
        logger.info(f"Initializing PyJWKClient for JWKS endpoint: {jwks_url}")
        _jwks_clients[jwks_url] = PyJWKClient(jwks_url, cache_keys=True)
    return _jwks_clients[jwks_url]


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Creates signed JWT Access Token."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "iat": now, "type": "access"})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(data: Dict[str, Any]) -> str:
    """Creates signed JWT Refresh Token with 7-day validity."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "iat": now, "type": "refresh"})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_custom_token(token: str, expected_type: str = "access") -> Dict[str, Any]:
    """Decodes custom HS256 JWT access or refresh token."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("type") != expected_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token type. Expected '{expected_type}' token.",
                headers={"WWW-Authenticate": "Bearer"}
            )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"{expected_type.capitalize()} token has expired.",
            headers={"WWW-Authenticate": "Bearer error=\"token_expired\""}
        )
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid {expected_type} token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"}
        )


def verify_clerk_token(token: str) -> Dict[str, Any]:
    """
    Verifies a Clerk JWT Access Token using RS256 JWKS signature verification.
    """
    try:
        unverified_headers = jwt.get_unverified_header(token)
        unverified_payload = jwt.decode(token, options={"verify_signature": False})

        kid = unverified_headers.get("kid")
        issuer = unverified_payload.get("iss", settings.CLERK_ISSUER_URL)

        jwks_url = settings.CLERK_JWKS_URL
        if not jwks_url:
            if issuer:
                jwks_url = f"{issuer.rstrip('/')}/.well-known/jwks.json"
            else:
                jwks_url = "https://api.clerk.com/v1/jwks"

        jwks_client = get_jwks_client(jwks_url)
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        decode_options = {
            "verify_signature": True,
            "verify_exp": True,
            "verify_iss": False,
            "verify_aud": False,
        }

        decoded = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options=decode_options
        )
        return decoded
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired. Please refresh your session.",
            headers={"WWW-Authenticate": "Bearer error=\"invalid_token\", error_description=\"token_expired\""}
        )
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer error=\"invalid_token\""}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to authenticate token",
            headers={"WWW-Authenticate": "Bearer"}
        )


def verify_any_token(token: str) -> Dict[str, Any]:
    """Tries verifying as custom HS256 JWT, falling back to Clerk JWKS RS256 token."""
    try:
        return decode_custom_token(token, expected_type="access")
    except HTTPException:
        return verify_clerk_token(token)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme)
) -> Dict[str, Any]:
    """
    FastAPI Dependency to enforce authentication.
    Extracts Bearer token, verifies JWT, and returns authenticated user details.
    """
    if not credentials or not credentials.credentials:
        if settings.REQUIRE_AUTH:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing Authorization Header. Please log in to access this resource.",
                headers={"WWW-Authenticate": "Bearer"}
            )
        return {
            "user_id": settings.GUEST_USER_ID,
            "email": "guest@codepilot.local",
            "first_name": "Guest",
            "last_name": "User",
            "is_authenticated": False,
            "claims": {}
        }

    token = credentials.credentials
    claims = verify_any_token(token)

    return {
        "user_id": claims.get("sub") or claims.get("user_id"),
        "email": claims.get("email") or claims.get("primary_email_address"),
        "first_name": claims.get("first_name", ""),
        "last_name": claims.get("last_name", ""),
        "username": claims.get("username"),
        "picture": claims.get("image_url") or claims.get("picture"),
        "is_authenticated": True,
        "claims": claims
    }


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme)
) -> Optional[Dict[str, Any]]:
    """
    FastAPI Dependency for optional authentication.
    Returns decoded user if token is present and valid, otherwise returns None.
    """
    if not credentials or not credentials.credentials:
        return None

    try:
        token = credentials.credentials
        claims = verify_any_token(token)
        return {
            "user_id": claims.get("sub") or claims.get("user_id"),
            "email": claims.get("email"),
            "first_name": claims.get("first_name", ""),
            "last_name": claims.get("last_name", ""),
            "is_authenticated": True,
            "claims": claims
        }
    except (HTTPException, jwt.PyJWTError, Exception) as err:
        logger.debug(f"Optional token validation skipped: {err}")
        return None
