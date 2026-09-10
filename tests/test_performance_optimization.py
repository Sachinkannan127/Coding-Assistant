import pytest
import time
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.rag_service import rag_service, RAGCacheManager

client = TestClient(app)


def test_rag_cache_manager_ttl_and_hits():
    """Verify RAGCacheManager hit/miss logic and TTL expiration."""
    cache = RAGCacheManager(ttl_seconds=1.0)
    cache.clear()

    code = "def add(a, b): return a + b"
    lang = "python"
    limit = 3

    # Initial Miss
    res1 = cache.get(code, lang, limit)
    assert res1 is None
    assert cache.misses == 1

    # Set value
    cache.set(code, lang, limit, ["Doc 1", "Doc 2"])

    # Hit
    res2 = cache.get(code, lang, limit)
    assert res2 == ["Doc 1", "Doc 2"]
    assert cache.hits == 1

    # Wait for TTL expiry (> 1.0s)
    time.sleep(1.1)
    res3 = cache.get(code, lang, limit)
    assert res3 is None
    assert cache.misses == 2


@pytest.mark.asyncio
async def test_rag_service_caching_integration():
    """Verify RAGService returns cached knowledge on repeated calls without hitting embeddings service."""
    rag_service.cache.clear()
    
    code = "def sample(): pass"
    lang = "python"

    with patch.object(rag_service, "repo") as mock_repo:
        mock_repo.vector_search = AsyncMock(return_value=[])

        # Call 1 (Miss - populates cache)
        docs1 = await rag_service.retrieve_knowledge(query_code=code, language=lang)
        assert len(docs1) > 0

        # Call 2 (Hit - returns cached result)
        docs2 = await rag_service.retrieve_knowledge(query_code=code, language=lang)
        assert docs1 == docs2
        assert rag_service.cache.hits >= 1


def test_post_review_stream_sse_endpoint():
    """Verify POST /api/review/stream endpoint streams SSE progress events and payload result."""
    mock_workflow_output = {
        "review_id": "rev_stream_test",
        "overview": "Stream Test Overview",
        "verdict": "clean",
        "key_takeaways": [],
        "complexity_score": 5.0,
        "readability_score": 8.0,
        "maintainability_index": "A",
        "cyclomatic_complexity_est": "Low",
        "findings": [],
        "refactored_code": "def sample(): pass",
        "diff_summary": "No changes.",
        "validation_status": "passed"
    }

    with patch("backend.app.services.review_service.run_review_workflow", new=AsyncMock(return_value=mock_workflow_output)):
        response = client.post(
            "/api/review/stream",
            json={
                "code": "def sample(): pass",
                "language": "python",
                "mode": "quick"
            }
        )

    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    text = response.text
    assert "event\": \"status\"" in text or "status\": \"started\"" in text
    assert "event\": \"progress\"" in text
    assert "event\": \"result\"" in text
    assert "Stream Test Overview" in text
