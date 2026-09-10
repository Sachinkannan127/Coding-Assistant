import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)

MOCK_WORKFLOW_OUTPUT = {
    "review_id": "rev_e2e_test_123",
    "overview": "E2E Test Overview: Standard Python code snippet.",
    "verdict": "minor_issues",
    "key_takeaways": ["Add type hints", "Validate null parameters"],
    "complexity_score": 4.5,
    "readability_score": 8.5,
    "maintainability_index": "A",
    "cyclomatic_complexity_est": "Low",
    "findings": [
        {
            "id": "find-001",
            "category": "bug",
            "severity": "medium",
            "title": "Potential Null Dereference",
            "description": "User parameter may be None",
            "line_start": 2,
            "line_end": 2,
            "code_snippet": "user.profile.name",
            "suggestion": "Check if user and user.profile are non-null",
            "cwe_or_rule_id": "CWE-476"
        }
    ],
    "refactored_code": "def get_user_name(user):\n    if user and hasattr(user, 'profile'):\n        return user.profile.name\n    return None\n",
    "diff_summary": "Added defensive check",
    "validation_status": "passed"
}


def test_health_check_e2e():
    """Verify backend health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.parametrize("language,mode", [
    ("python", "quick"),
    ("javascript", "quick"),
    ("typescript", "deep"),
    ("java", "deep"),
    ("cpp", "quick"),
    ("go", "deep"),
    ("rust", "quick"),
])

def test_post_review_multi_language_e2e(language, mode):
    """Verify end-to-end review request across multiple programming languages and modes."""
    code_samples = {
        "python": "def add(a, b):\n    return a + b\n",
        "javascript": "function add(a, b) { return a + b; }",
        "typescript": "const add = (a: number, b: number): number => a + b;",
        "java": "public class Add { public int add(int a, int b) { return a + b; } }",
        "cpp": "int add(int a, int b) { return a + b; }",
        "go": "package main\nfunc add(a int, b int) int { return a + b }",
        "rust": "fn add(a: i32, b: i32) -> i32 { a + b }"
    }

    with patch("backend.app.services.review_service.run_review_workflow", new=AsyncMock(return_value=MOCK_WORKFLOW_OUTPUT)):
        response = client.post("/api/review", json={
            "code": code_samples[language],
            "language": language,
            "mode": mode
        })

    assert response.status_code == 200
    res = response.json()
    assert "review_id" in res
    assert res["mode"] == mode
    assert res["input_metadata"]["language"] in [language, "python", "javascript", "typescript", "java", "cpp", "go", "rust"]
    assert "summary" in res
    assert "metrics" in res
    assert "findings" in res
    assert "refactoring" in res
    assert "execution_metadata" in res


def test_review_e2e_empty_code_rejection():
    """Verify rejection of empty code input with HTTP 400."""
    response = client.post("/api/review", json={
        "code": "   \n\t  ",
        "language": "python",
        "mode": "quick"
    })
    assert response.status_code == 400
    assert "cannot be empty" in response.json()["detail"].lower()


def test_review_e2e_non_code_text_rejection():
    """Verify rejection of non-code natural language text with HTTP 400."""
    response = client.post("/api/review", json={
        "code": "Hello! Please write a nice blog post about sunny weather and coffee.",
        "language": "python",
        "mode": "quick"
    })
    assert response.status_code == 400
    assert "program code" in response.json()["detail"].lower()


def test_review_e2e_payload_size_limit_rejection():
    """Verify rejection of code inputs exceeding 50KB size limit."""
    huge_code = "# Comment\n" + ("x = 1\n" * 9000)
    response = client.post("/api/review", json={
        "code": huge_code,
        "language": "python",
        "mode": "quick"
    })
    assert response.status_code == 400
    assert "exceeds" in response.json()["detail"].lower() or "50" in response.json()["detail"]


def test_review_e2e_export_markdown_generation():
    """Verify export endpoint returns downloadable Markdown file."""
    mock_review_dict = {
        "review_id": "rev_e2e_test_123",
        "created_at": "2026-09-10T00:00:00Z",
        "mode": "quick",
        "input_metadata": {"language": "python", "line_count": 1, "char_count": 15, "hash": "abc"},
        "summary": MOCK_WORKFLOW_OUTPUT,
        "metrics": {"complexity_score": 4.5, "readability_score": 8.5, "maintainability_index": "A", "cyclomatic_complexity_est": "Low"},
        "findings": MOCK_WORKFLOW_OUTPUT["findings"],
        "refactoring": {"has_refactored_code": True, "refactored_code": MOCK_WORKFLOW_OUTPUT["refactored_code"], "diff_summary": "Defensive check", "validation_status": "passed", "validation_notes": "AST check passed"},
        "execution_metadata": {"total_duration_ms": 150, "llm_provider_used": "gemini", "fallback_triggered": False, "rag_context_used": False, "rag_sources": []}
    }

    with patch("backend.app.services.review_service.review_service.get_review_by_id", new=AsyncMock(return_value=mock_review_dict)):
        export_res = client.get("/api/review/rev_e2e_test_123/export")
        assert export_res.status_code == 200
        assert export_res.headers["content-type"].startswith("text/markdown")
        assert "attachment; filename=" in export_res.headers["content-disposition"]
        assert "review_report_rev_e2e_.md" in export_res.headers["content-disposition"]
        content = export_res.text
        assert "Code Review" in content
