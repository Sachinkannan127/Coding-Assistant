import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_auth_status_endpoint():
    """Verify /api/auth/status returns authentication status and 7-day refresh token validity."""
    response = client.get("/api/auth/status")
    assert response.status_code == 200
    data = response.json()
    assert "provider" in data
    assert data["refresh_token_validity_days"] == 7
    assert "require_auth" in data
    assert "clerk_configured" in data


def test_issue_and_refresh_tokens_7_days():
    """Verify issuing access/refresh tokens and refreshing access token with 7-day refresh token."""
    # 1. Issue tokens
    issue_res = client.post(
        "/api/auth/token",
        json={"user_id": "usr_test_123", "email": "test@codepilot.local"}
    )
    assert issue_res.status_code == 200
    issue_data = issue_res.json()
    assert "access_token" in issue_data
    assert "refresh_token" in issue_data
    assert issue_data["refresh_token_expires_in_days"] == 7

    access_token = issue_data["access_token"]
    refresh_token = issue_data["refresh_token"]

    # 2. Authenticate with Access Token
    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {access_token}"})
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["is_authenticated"] is True
    assert me_data["user_id"] == "usr_test_123"

    # 3. Refresh Access Token using 7-day Refresh Token
    refresh_res = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_res.status_code == 200
    refresh_data = refresh_res.json()
    assert "access_token" in refresh_data
    new_access_token = refresh_data["access_token"]
    assert new_access_token != ""

    # 4. Authenticate with new Access Token
    new_me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {new_access_token}"})
    assert new_me_res.status_code == 200
    assert new_me_res.json()["is_authenticated"] is True


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
    assert data["refresh_token_validity"] == "7 Days"
