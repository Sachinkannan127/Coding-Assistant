import sys
from pathlib import Path
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.app.services.rag_service import RAGService, SEED_KNOWLEDGE_DOCS
from backend.app.models.review_schemas import RAGDocument
from backend.app.graph.nodes import rag_retrieval_node


@pytest.mark.asyncio
async def test_rag_service_graceful_fallback():
    """Verify RAGService gracefully returns seed fallback docs when vector search is unindexed or fails."""
    service = RAGService()

    # Mock embeddings to raise exception simulating missing API key or unindexed DB
    with patch("backend.app.services.rag_service.embeddings_service.aembed_query", side_effect=ValueError("Embedding API offline")):
        docs = await service.retrieve_knowledge(query_code="def insecure(): pass", language="python", limit=2)
        assert len(docs) == 2
        assert any("OWASP" in d or "NULL Pointer" in d or "Clean Code" in d for d in docs)


@pytest.mark.asyncio
async def test_rag_service_vector_search_success():
    """Verify RAGService returns formatted documents when vector search succeeds."""
    mock_doc = RAGDocument(
        doc_id="rag-test-1",
        title="Custom Test Rule",
        category="security",
        language="python",
        content="Use secure hashing."
    )
    mock_repo = MagicMock()
    mock_repo.vector_search = AsyncMock(return_value=[mock_doc])

    service = RAGService(repo=mock_repo)

    with patch("backend.app.services.rag_service.embeddings_service.aembed_query", new_callable=AsyncMock) as mock_embed:
        mock_embed.return_value = [0.1] * 768

        results = await service.retrieve_knowledge(query_code="import hashlib", language="python", limit=1)

        assert len(results) == 1
        assert "[Custom Test Rule]: Use secure hashing." in results[0]
        mock_embed.assert_called_once()
        mock_repo.vector_search.assert_called_once()


@pytest.mark.asyncio
async def test_rag_retrieval_node_integration():
    """Verify graph rag_retrieval_node invokes RAGService and updates state context."""
    state = {
        "review_id": "rev-rag-1",
        "original_code": "def process(): pass",
        "language": "python",
        "mode": "deep"
    }

    with patch("backend.app.graph.nodes.rag_service.retrieve_knowledge", new_callable=AsyncMock) as mock_retrieve:
        mock_retrieve.return_value = ["[OWASP]: Secure input"]

        res = await rag_retrieval_node(state)

        assert "rag_context" in res
        assert res["rag_context"] == ["[OWASP]: Secure input"]
        mock_retrieve.assert_called_once_with(query_code="def process(): pass", language="python")
