import logging
from typing import List, Optional
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from backend.app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingsService:
    """
    Embeddings Service for vector search and RAG retriever.
    Uses Google Gemini text-embedding-004 to produce 768-dimensional dense vector embeddings.
    """

    MODEL_NAME = "models/text-embedding-004"
    DIMENSIONS = 768

    def __init__(self, model_name: str = MODEL_NAME):
        self.model_name = model_name

    def _get_embeddings_client(self) -> GoogleGenerativeAIEmbeddings:
        api_key = settings.GEMINI_API_KEY.strip()
        if not api_key:
            raise ValueError("GEMINI_API_KEY is missing or empty. Cannot initialize embeddings service.")
        return GoogleGenerativeAIEmbeddings(
            model=self.model_name,
            google_api_key=api_key
        )

    def embed_query(self, text: str) -> List[float]:
        """Generate embedding vector for a search query string."""
        if not text or not text.strip():
            return [0.0] * self.DIMENSIONS
        client = self._get_embeddings_client()
        return client.embed_query(text)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embedding vectors for a list of document strings."""
        if not texts:
            return []
        client = self._get_embeddings_client()
        return client.embed_documents(texts)

    async def aembed_query(self, text: str) -> List[float]:
        """Asynchronously generate embedding vector for a search query string."""
        if not text or not text.strip():
            return [0.0] * self.DIMENSIONS
        client = self._get_embeddings_client()
        return await client.aembed_query(text)

    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        """Asynchronously generate embedding vectors for a list of document strings."""
        if not texts:
            return []
        client = self._get_embeddings_client()
        return await client.aembed_documents(texts)


embeddings_service = EmbeddingsService()
