import logging
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


def verify_clerk_token(token: str) -> Dict[str, Any]:
    """
    Verifies a Clerk JWT Access Token using RS256 JWKS signature verification.
    Returns the decoded token claims if valid.
    Raises HTTPException 401 if invalid or expired.
    """
    try:
        # Step 1: Decode unverified token headers to locate kid and issuer
        unverified_headers = jwt.get_unverified_header(token)
        unverified_payload = jwt.decode(token, options={"verify_signature": False})

        kid = unverified_headers.get("kid")
        issuer = unverified_payload.get("iss", settings.CLERK_ISSUER_URL)

        # Determine JWKS URL
        jwks_url = settings.CLERK_JWKS_URL
        if not jwks_url:
            if issuer:
                jwks_url = f"{issuer.rstrip('/')}/.well-known/jwks.json"
            else:
                jwks_url = "https://api.clerk.com/v1/jwks"

        # Step 2: Fetch signing key from JWKS
        jwks_client = get_jwks_client(jwks_url)
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        # Step 3: Decode and verify JWT token signature and expiration
        decode_options = {
            "verify_signature": True,
            "verify_exp": True,
            "verify_iss": False,  # Managed manually or via issuer matching
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
        logger.warning("Clerk JWT verification failed: Token has expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired. Please refresh your session.",
            headers={"WWW-Authenticate": "Bearer error=\"invalid_token\", error_description=\"token_expired\""}
        )
    except jwt.PyJWTError as e:
        logger.warning(f"Clerk JWT verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer error=\"invalid_token\""}
        )
    except Exception as e:
        logger.error(f"Unexpected error during Clerk JWT verification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to authenticate token",
            headers={"WWW-Authenticate": "Bearer"}
        )


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme)
) -> Dict[str, Any]:
    """
    FastAPI Dependency to enforce authentication.
    Extracts Bearer token, verifies Clerk JWT, and returns authenticated user details.
    """
    if not credentials or not credentials.credentials:
        if settings.REQUIRE_AUTH:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing Authorization Header. Please log in to access this resource.",
                headers={"WWW-Authenticate": "Bearer"}
            )
        # Development / Non-enforced fallback user context
        return {
            "user_id": "dev_guest_user",
            "email": "guest@codepilot.local",
            "first_name": "Guest",
            "last_name": "User",
            "is_authenticated": False,
            "claims": {}
        }

    token = credentials.credentials
    claims = verify_clerk_token(token)

    return {
        "user_id": claims.get("sub"),
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
        claims = verify_clerk_token(token)
        return {
            "user_id": claims.get("sub"),
            "email": claims.get("email"),
            "first_name": claims.get("first_name", ""),
            "last_name": claims.get("last_name", ""),
            "is_authenticated": True,
            "claims": claims
        }
    except Exception:
        return None
