import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_cors_preflight_and_headers():
    """Verify CORS preflight OPTIONS request and Access-Control-Allow-Origin header matching."""
    origin = "https://code-pilot.vercel.app"

    # Test preflight OPTIONS request on /health
    options_res = client.options(
        "/health",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET"
        }
    )
    assert options_res.status_code in [200, 204]
    assert options_res.headers.get("access-control-allow-origin") == origin

    # Test GET /health with Origin header
    get_res = client.get("/health", headers={"Origin": origin})
    assert get_res.status_code == 200
    assert get_res.headers.get("access-control-allow-origin") == origin
