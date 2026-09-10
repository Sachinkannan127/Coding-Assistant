import os
from pathlib import Path
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.config import settings

client = TestClient(app)
ROOT_DIR = Path(__file__).resolve().parent.parent


def test_v1_system_version():
    """Verify system title, version tag (1.0.0), and environment configuration."""
    assert settings.APP_VERSION == "1.0.0"
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["version"] == "1.0.0"
    assert data["status"] == "ok"


def test_v1_openapi_documentation_endpoints():
    """Verify OpenAPI schema and Swagger UI documentation endpoints."""
    res_root = client.get("/")
    assert res_root.status_code == 200
    assert res_root.json()["docs_url"] == "/docs"

    res_openapi = client.get("/openapi.json")
    assert res_openapi.status_code == 200
    openapi_data = res_openapi.json()
    assert openapi_data["info"]["version"] == "1.0.0"
    assert "/api/review" in openapi_data["paths"]
    assert "/api/review/stream" in openapi_data["paths"]
    assert "/api/review/{review_id}/export" in openapi_data["paths"]


def test_v1_documentation_files_exist():
    """Verify presence of comprehensive system documentation files in docs/."""
    docs_dir = ROOT_DIR / "docs"
    assert (docs_dir / "requirements.md").exists()
    assert (docs_dir / "architecture.md").exists()
    assert (docs_dir / "agent-design.md").exists()


def test_v1_readme_roadmap_completion():
    """Verify all 23 phase milestones (Phase 0 through Phase 22) are marked complete in README.md."""
    readme_file = ROOT_DIR / "README.md"
    assert readme_file.exists()
    content = readme_file.read_text(encoding="utf-8")

    # Verify all 23 phases are checked [x]
    for phase_num in range(23):
        assert f"- [x] **Phase {phase_num}**" in content
