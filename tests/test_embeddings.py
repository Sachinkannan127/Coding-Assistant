import sys
from pathlib import Path
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.app.services.llm.embeddings import EmbeddingsService, embeddings_service


def test_embeddings_service_empty_input():
    """Verify empty/whitespace strings return zero vectors without calling client."""
    service = EmbeddingsService()
    vector = service.embed_query("")
    assert len(vector) == 768
    assert all(v == 0.0 for v in vector)

    vectors = service.embed_documents([])
    assert vectors == []


def test_embeddings_service_missing_api_key():
    """Verify ValueError is raised when GEMINI_API_KEY is missing."""
    service = EmbeddingsService()
    with patch("backend.app.services.llm.embeddings.settings.GEMINI_API_KEY", ""):
        with pytest.raises(ValueError) as exc_info:
            service.embed_query("test query")
        assert "GEMINI_API_KEY is missing or empty" in str(exc_info.value)


def test_embeddings_service_embed_query():
    """Verify query embedding returning 768-dim float vector."""
    service = EmbeddingsService()
    dummy_vec = [0.1] * 768

    mock_client = MagicMock()
    mock_client.embed_query.return_value = dummy_vec

    with patch("backend.app.services.llm.embeddings.settings.GEMINI_API_KEY", "dummy_key"), \
         patch.object(service, "_get_embeddings_client", return_value=mock_client):

        vec = service.embed_query("Sample code snippet")
        assert len(vec) == 768
        assert vec[0] == 0.1
        mock_client.embed_query.assert_called_once_with("Sample code snippet")


@pytest.mark.asyncio
async def test_embeddings_service_aembed_query():
    """Verify async query embedding."""
    service = EmbeddingsService()
    dummy_vec = [0.2] * 768

    mock_client = MagicMock()
    mock_client.aembed_query = AsyncMock(return_value=dummy_vec)

    with patch("backend.app.services.llm.embeddings.settings.GEMINI_API_KEY", "dummy_key"), \
         patch.object(service, "_get_embeddings_client", return_value=mock_client):

        vec = await service.aembed_query("Async query")
        assert len(vec) == 768
        assert vec[0] == 0.2
        mock_client.aembed_query.assert_called_once_with("Async query")
