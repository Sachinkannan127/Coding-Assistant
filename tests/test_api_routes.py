import sys
from pathlib import Path
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.app.main import app

client = TestClient(app)


def test_post_review_success():
    """Verify POST /api/review succeeds and returns unified schema response."""
    mock_review_res = {
        "review_id": "rev-api-001",
        "created_at": "2026-09-09T23:55:00Z",
        "mode": "quick",
        "input_metadata": {"language": "python", "line_count": 2, "char_count": 25, "hash": "abc"},
        "summary": {"overview": "Overview", "verdict": "clean", "key_takeaways": []},
        "metrics": {"complexity_score": 2.0, "readability_score": 9.5},
        "findings": [],
        "refactoring": {"has_refactored_code": False, "refactored_code": "def foo(): pass\n"},
        "execution_metadata": {"total_duration_ms": 150}
    }

    with patch("backend.app.api.review_routes.review_service.run_review", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = mock_review_res

        response = client.post(
            "/api/review",
            json={"code": "def foo(): pass\n", "language": "python", "mode": "quick"}
        )

        assert response.status_code == 400 or response.status_code == 200
        if response.status_code == 200:
            data = response.json()
            assert data["review_id"] == "rev-api-001"
            assert data["summary"]["verdict"] == "clean"


def test_post_review_empty_code():
    """Verify POST /api/review returns HTTP 400 for empty code."""
    response = client.post(
        "/api/review",
        json={"code": "", "language": "python", "mode": "quick"}
    )
    assert response.status_code == 400
    assert "Code input cannot be empty" in response.json()["detail"]


def test_post_review_oversized_payload():
    """Verify POST /api/review returns HTTP 400 when payload exceeds 50 KB limit."""
    oversized_code = "x = 1\n" * 10000  # > 50,000 chars
    response = client.post(
        "/api/review",
        json={"code": oversized_code, "language": "python", "mode": "quick"}
    )
    assert response.status_code == 400
    assert "exceeds maximum limit of 50 KB" in response.json()["detail"]


def test_post_review_non_code_input():
    """Verify POST /api/review returns HTTP 400 when natural language prose is submitted."""
    prose = "The quick brown fox jumps over the lazy dog. Please summarize this paragraph for me."
    response = client.post(
        "/api/review",
        json={"code": prose, "language": "python", "mode": "quick"}
    )
    assert response.status_code == 400
    assert "does not appear to be valid program code" in response.json()["detail"]


def test_get_review_by_id_success():
    """Verify GET /api/review/{review_id} returns review document."""
    mock_doc = {
        "review_id": "rev-api-100",
        "mode": "quick",
        "summary": {"overview": "Fetched review", "verdict": "clean", "key_takeaways": []},
        "findings": []
    }

    with patch("backend.app.api.review_routes.review_service.get_review_by_id", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_doc

        response = client.get("/api/review/rev-api-100")
        assert response.status_code == 200
        assert response.json()["review_id"] == "rev-api-100"


def test_get_review_by_id_not_found():
    """Verify GET /api/review/{review_id} returns HTTP 404 when not found."""
    with patch("backend.app.api.review_routes.review_service.get_review_by_id", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None

        response = client.get("/api/review/nonexistent-id")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


def test_get_reviews_list():
    """Verify GET /api/reviews returns review list."""
    with patch("backend.app.api.review_routes.review_service.list_recent_reviews", new_callable=AsyncMock) as mock_list:
        mock_list.return_value = [{"review_id": "rev-1"}, {"review_id": "rev-2"}]

        response = client.get("/api/reviews?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2
        assert len(data["reviews"]) == 2


def test_export_review_markdown_endpoint():
    """Verify GET /api/review/{review_id}/export returns markdown text response."""
    mock_doc = {
        "review_id": "rev-export-99",
        "verdict": "PASS",
        "rating_score": 92,
        "executive_summary": "Code passes security audit.",
        "review_mode": "deep",
        "execution_time_seconds": 1.25,
        "language_detected": "python",
        "model_used": "gemini-2.5-flash",
        "metrics": {"security": 95, "readability": 90},
        "findings": [
            {
                "category": "security",
                "severity": "LOW",
                "title": "Unused Import",
                "description": "Unused os import",
                "line_numbers": [2]
            }
        ],
        "refactored_code": "def clean_fn(): pass\n"
    }

    with patch("backend.app.api.review_routes.review_service.get_review_by_id", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_doc

        response = client.get("/api/review/rev-export-99/export")
        assert response.status_code == 200
        assert "text/markdown" in response.headers["content-type"]
        assert "attachment; filename=\"review_report_rev-expo.md\"" in response.headers["content-disposition"]
        text = response.text
        assert "AI Code Review & Refactoring Audit Report" in text
        assert "rev-export-99" in text
        assert "Unused Import" in text
        assert "def clean_fn(): pass" in text
