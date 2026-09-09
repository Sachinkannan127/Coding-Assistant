import sys
from pathlib import Path
from fastapi.testclient import TestClient

# Ensure root directory is in sys.path for importing backend
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.app.main import app

client = TestClient(app)

def test_root_endpoint():
    """Verify GET / returns HTTP 200 OK with expected landing page schema."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["app_name"] == "AI Code Review & Refactoring Platform"
    assert "version" in data
    assert data["docs_url"] == "/docs"
    assert data["health_url"] == "/health"

def test_health_endpoint():
    """Verify GET /health returns HTTP 200 OK with expected status schema."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "app_name" in data
    assert "version" in data
    assert "environment" in data
    assert "database" in data
    assert "timestamp" in data

