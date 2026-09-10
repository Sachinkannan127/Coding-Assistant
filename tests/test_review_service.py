import sys
from pathlib import Path
import pytest
from unittest.mock import AsyncMock, patch

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.app.services.review_service import review_service, CodeValidationError


@pytest.mark.asyncio
async def test_review_service_quick_mode():
    """Verify ReviewService execution in Quick Scan mode."""
    mock_workflow_output = {
        "overview": "Quick review overview",
        "verdict": "clean",
        "key_takeaways": ["Takeaway 1"],
        "complexity_score": 3.5,
        "readability_score": 9.0,
        "maintainability_index": "A",
        "cyclomatic_complexity_est": "Low",
        "findings": [],
        "refactored_code": "def process():\n    return True\n",
        "diff_summary": "Clean code",
        "validation_status": "passed"
    }

    with patch("backend.app.services.review_service.run_review_workflow", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = mock_workflow_output

        res = await review_service.run_review(
            code="def process():\n    return True\n",
            language="python",
            mode="quick"
        )

        assert res["mode"] == "quick"
        assert res["summary"]["verdict"] == "clean"
        assert res["input_metadata"]["language"] == "python"
        assert res["language_detected"] == "python"
        assert res["execution_metadata"]["rag_context_used"] is False
        assert res["execution_metadata"]["total_duration_ms"] >= 0
        mock_run.assert_called_once()


@pytest.mark.asyncio
async def test_review_service_deep_mode():
    """Verify ReviewService execution in Deep Review mode with RAG context."""
    mock_workflow_output = {
        "overview": "Deep audit overview",
        "verdict": "minor_issues",
        "key_takeaways": ["Check null pointer"],
        "complexity_score": 6.0,
        "readability_score": 7.5,
        "maintainability_index": "B",
        "cyclomatic_complexity_est": "Moderate",
        "findings": [
            {
                "id": "find-1", "category": "bug", "severity": "medium",
                "title": "Null check", "description": "Null access",
                "line_start": 2, "line_end": 2, "code_snippet": "obj.val",
                "suggestion": "Add null check", "cwe_or_rule_id": "CWE-476"
            }
        ],
        "refactored_code": "def safe_process(obj):\n    return obj.val if obj else None\n",
        "diff_summary": "Added null check",
        "validation_status": "passed"
    }

    with patch("backend.app.services.review_service.run_review_workflow", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = mock_workflow_output

        res = await review_service.run_review(
            code="def safe_process(obj):\n    return obj.val\n",
            language="python",
            mode="deep"
        )

        assert res["mode"] == "deep"
        assert res["summary"]["verdict"] == "minor_issues"
        assert len(res["findings"]) == 1
        assert res["refactoring"]["has_refactored_code"] is True
        assert res["execution_metadata"]["rag_context_used"] is True


@pytest.mark.asyncio
async def test_review_service_invalid_input():
    """Verify CodeValidationError is raised for empty code or plain text."""
    with pytest.raises(CodeValidationError):
        await review_service.run_review(code="", mode="quick")

    with pytest.raises(CodeValidationError):
        await review_service.run_review(code="This is just plain English text.", mode="deep")
