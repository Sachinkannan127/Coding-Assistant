import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_auth_status_endpoint():
    """Verify /api/auth/status returns Clerk authentication status."""
    response = client.get("/api/auth/status")
    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "Clerk"
    assert "require_auth" in data
    assert "clerk_configured" in data


def test_auth_me_unauthenticated():
    """Verify /api/auth/me returns guest/unauthenticated user context when no token is supplied."""
    response = client.get("/api/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "is_authenticated" in data


def test_auth_me_invalid_token():
    """Verify /api/auth/me rejects invalid Bearer token with HTTP 401 Unauthorized."""
    response = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid_jwt_token_payload"})
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data


def test_token_info_endpoint():
    """Verify /api/auth/token-info returns token metadata for current session."""
    response = client.get("/api/auth/token-info")
    assert response.status_code == 200
    data = response.json()
    assert "token_type" in data
    assert "refresh_token_strategy" in data

