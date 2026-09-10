import os
from pathlib import Path
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)
ROOT_DIR = Path(__file__).resolve().parent.parent


def test_dockerfile_backend_exists():
    """Verify presence and structure of Dockerfile.backend."""
    dockerfile = ROOT_DIR / "Dockerfile.backend"
    assert dockerfile.exists()
    content = dockerfile.read_text(encoding="utf-8")
    assert "FROM python:3.11-slim" in content
    assert "EXPOSE 8000" in content
    assert "uvicorn" in content


def test_dockerfile_frontend_exists():
    """Verify presence and structure of Dockerfile.frontend."""
    dockerfile = ROOT_DIR / "Dockerfile.frontend"
    assert dockerfile.exists()
    content = dockerfile.read_text(encoding="utf-8")
    assert "FROM node:18-alpine" in content
    assert "EXPOSE 3000" in content
    assert "npm run build" in content


def test_docker_compose_config():
    """Verify docker-compose.yml structure and services."""
    compose_file = ROOT_DIR / "docker-compose.yml"
    assert compose_file.exists()
    content = compose_file.read_text(encoding="utf-8")

    assert "services:" in content
    assert "backend:" in content
    assert "frontend:" in content
    assert "8000:8000" in content
    assert "3000:3000" in content
    assert "healthcheck:" in content


def test_dockerignore_exists():
    """Verify presence of .dockerignore file."""
    dockerignore = ROOT_DIR / ".dockerignore"
    assert dockerignore.exists()
    content = dockerignore.read_text(encoding="utf-8")
    assert ".env" in content
    assert "node_modules" in content
    assert "venv" in content


def test_production_health_endpoint():
    """Verify backend health endpoint in production mode."""
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "version" in data
