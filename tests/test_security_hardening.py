import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.config import settings, sanitize_credentials
from backend.app.middleware.security_middleware import RateLimiterMiddleware

client = TestClient(app)


def test_security_response_headers():
    """Verify presence of standard OWASP security response headers."""
    response = client.get("/health")
    assert response.status_code == 200
    headers = response.headers

    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert headers.get("X-XSS-Protection") == "1; mode=block"
    assert "max-age=" in headers.get("Strict-Transport-Security", "")
    assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "default-src 'self'" in headers.get("Content-Security-Policy", "")


def test_rate_limiter_throttling():
    """Verify rate limiter blocks burst requests exceeding limit with HTTP 429."""
    limiter_app = TestClient(app)
    
    # We patch settings.RATE_LIMIT_PER_MINUTE to 3 for instant testing
    with patch.object(settings, "ENABLE_RATE_LIMITING", True):
        # We need to clear any request state in rate limiter middleware if needed
        # Perform 3 requests (within limit)
        for _ in range(3):
            with patch("backend.app.services.review_service.run_review_workflow", new=AsyncMock(return_value={"overview": "ok"})):
                res = client.post("/api/review", json={"code": "x = 1", "language": "python", "mode": "quick"})
                # Should either be 200 or 429 depending on previous tests, so we test isolated middleware instance

    # Isolated test of RateLimiterMiddleware logic
    middleware = RateLimiterMiddleware(app=None, rate_limit_per_minute=2)
    middleware.requests.clear()
    
    # Simulate client requests
    mock_request = MagicMock()
    mock_request.url.path = "/api/review"
    mock_request.client.host = "192.168.1.100"

    # Request 1 & 2 pass
    async def dummy_next(req):
        return Response(content="ok", status_code=200)

    import asyncio
    r1 = asyncio.run(middleware.dispatch(mock_request, dummy_next))
    r2 = asyncio.run(middleware.dispatch(mock_request, dummy_next))
    assert r1.status_code == 200
    assert r2.status_code == 200

    # Request 3 fails with 429
    r3 = asyncio.run(middleware.dispatch(mock_request, dummy_next))
    assert r3.status_code == 429
    assert r3.headers["Retry-After"] == "60"


from unittest.mock import MagicMock
from starlette.responses import Response


def test_credential_masking():
    """Verify credential sanitizer redacts sensitive API keys and secrets."""
    mock_secret = "AIzaSySecretApiKey123456"
    
    with patch.object(settings, "GEMINI_API_KEY", mock_secret):
        raw_error_text = f"Connection failed to Gemini using key {mock_secret} at endpoint."
        clean_text = sanitize_credentials(raw_error_text)
        
        assert mock_secret not in clean_text
        assert "[REDACTED_API_KEY]" in clean_text


def test_payload_limit_enforcement():
    """Verify code payload exceeding limit is blocked safely."""
    oversized_code = "print('hello')\n" * 5000
    response = client.post("/api/review", json={
        "code": oversized_code,
        "language": "python",
        "mode": "quick"
    })
    assert response.status_code == 400
    assert "exceeds" in response.json()["detail"].lower() or "50" in response.json()["detail"]


def test_cors_headers():
    """Verify CORS middleware headers on preflight requests."""
    response = client.options(
        "/api/review",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type"
        }
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") in ["http://localhost:3000", "*"]
