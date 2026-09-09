import sys
from pathlib import Path
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.app.services.review_service import ReviewService
from backend.app.models.review_schemas import CodeReviewDocument, InputMetadata, Summary, Metrics, Finding, Refactoring, ExecutionMetadata


@pytest.mark.asyncio
async def test_review_persistence_success():
    """Verify ReviewService persists CodeReviewDocument and Finding objects to MongoDB repository."""
    mock_repo = MagicMock()
    mock_repo.create_review = AsyncMock()
    mock_repo.save_findings = AsyncMock()

    service = ReviewService(repo=mock_repo)

    mock_workflow_output = {
        "overview": "Overview",
        "verdict": "clean",
        "key_takeaways": [],
        "complexity_score": 3.0,
        "readability_score": 9.0,
        "findings": [
            {
                "id": "find-001", "category": "bug", "severity": "medium",
                "title": "Bug", "description": "Desc", "line_start": 1, "line_end": 1,
                "code_snippet": "x", "suggestion": "fix"
            }
        ]
    }

    with patch("backend.app.services.review_service.run_review_workflow", new_callable=AsyncMock) as mock_graph:
        mock_graph.return_value = mock_workflow_output

        res = await service.run_review(code="x = 10\n", language="python", mode="quick")

        assert res["review_id"] is not None
        mock_repo.create_review.assert_called_once()
        mock_repo.save_findings.assert_called_once()


@pytest.mark.asyncio
async def test_review_persistence_offline_fallback():
    """Verify ReviewService gracefully completes review response when MongoDB raises connection error."""
    mock_repo = MagicMock()
    mock_repo.create_review = AsyncMock(side_effect=RuntimeError("MongoDB Connection Refused"))

    service = ReviewService(repo=mock_repo)

    with patch("backend.app.services.review_service.run_review_workflow", new_callable=AsyncMock) as mock_graph:
        mock_graph.return_value = {"overview": "Offline review", "verdict": "clean"}

        res = await service.run_review(code="y = 20\n", language="python", mode="quick")

        assert res["summary"]["overview"] == "Offline review"
        mock_repo.create_review.assert_called_once()


@pytest.mark.asyncio
async def test_get_review_by_id_and_list():
    """Verify get_review_by_id and list_recent_reviews retrieval methods."""
    mock_doc = CodeReviewDocument(
        review_id="rev-123",
        mode="quick",
        original_code="print(1)",
        input_metadata=InputMetadata(language="python", line_count=1, char_count=8, hash="abc"),
        summary=Summary(overview="Overview", verdict="clean", key_takeaways=[]),
        metrics=Metrics(complexity_score=1.0, readability_score=10.0),
        findings=[],
        refactoring=Refactoring(),
        execution_metadata=ExecutionMetadata()
    )
    mock_repo = MagicMock()
    mock_repo.get_review_by_id = AsyncMock(return_value=mock_doc)
    mock_repo.get_findings_by_review_id = AsyncMock(return_value=[])
    mock_repo.list_reviews = AsyncMock(return_value=[mock_doc])

    service = ReviewService(repo=mock_repo)

    doc_res = await service.get_review_by_id("rev-123")
    assert doc_res["review_id"] == "rev-123"

    list_res = await service.list_recent_reviews(limit=10)
    assert len(list_res) == 1
    assert list_res[0]["review_id"] == "rev-123"
