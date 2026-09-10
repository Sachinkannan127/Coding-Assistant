import time
import hashlib
import logging
from typing import List, Dict, Tuple, Optional
from backend.app.models.review_schemas import RAGDocument
from backend.app.db.repositories.rag_repository import RAGRepository
from backend.app.services.llm.embeddings import embeddings_service

logger = logging.getLogger(__name__)


# Default Seed / Fallback Knowledge Documents
SEED_KNOWLEDGE_DOCS = [
    RAGDocument(
        doc_id="rag-owasp-001",
        title="OWASP Top 10 API Security Guidelines",
        category="security",
        language="general",
        content="Prevent Injection (CWE-89) by using parameterized queries or ORM models. Validate all user input boundaries and avoid string concatenation in raw SQL or system commands."
    ),
    RAGDocument(
        doc_id="rag-cwe-476",
        title="CWE-476: NULL Pointer Dereference Prevention",
        category="security",
        language="general",
        content="Always perform explicit non-null or non-empty validation before accessing object properties or calling methods. In C/C++, verify pointers returned by malloc/new before dereferencing."
    ),
    RAGDocument(
        doc_id="rag-clean-code-001",
        title="Clean Code & Refactoring Best Practices",
        category="clean_code",
        language="general",
        content="Keep functions modular and focused on a single responsibility (SRP). Use clear descriptive variable names, eliminate dead code, and avoid deeply nested conditional logic."
    ),
    RAGDocument(
        doc_id="rag-cpp-c-001",
        title="C & C++ Memory Management & Resource Safety",
        category="security",
        language="cpp",
        content="Avoid buffer overflows by using bounds-checked buffer operations (snprintf instead of sprintf). Manage memory safely with RAII or smart pointers (std::unique_ptr, std::shared_ptr) to prevent resource leaks."
    ),
    RAGDocument(
        doc_id="rag-react-next-001",
        title="React & Next.js Performance & Security Patterns",
        category="clean_code",
        language="react",
        content="Ensure React components remain pure. Avoid raw innerHTML assignments to prevent XSS. Use proper useEffect dependencies to avoid infinite re-renders and memory leaks."
    )
]


class RAGCacheManager:
    """In-memory TTL Cache Manager for RAG vector search results."""

    def __init__(self, ttl_seconds: float = 300.0):
        self.ttl = ttl_seconds
        self._cache: Dict[str, Tuple[List[str], float]] = {}
        self.hits = 0
        self.misses = 0

    def _make_key(self, query_code: str, language: str, limit: int) -> str:
        raw_key = f"{language}:{limit}:{query_code.strip()}"
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    def get(self, query_code: str, language: str, limit: int) -> Optional[List[str]]:
        key = self._make_key(query_code, language, limit)
        if key in self._cache:
            data, timestamp = self._cache[key]
            if time.time() - timestamp <= self.ttl:
                self.hits += 1
                logger.info(f"RAG Cache HIT for key {key[:8]}... (Hits: {self.hits})")
                return data
            else:
                del self._cache[key]
        self.misses += 1
        return None

    def set(self, query_code: str, language: str, limit: int, value: List[str]):
        key = self._make_key(query_code, language, limit)
        self._cache[key] = (value, time.time())

    def clear(self):
        self._cache.clear()
        self.hits = 0
        self.misses = 0


class RAGService:
    """
    RAG Service handling knowledge retrieval, embedding generation,
    MongoDB Atlas vector search, TTL caching, and graceful failover fallback.
    """

    def __init__(self, repo: Optional[RAGRepository] = None, ttl_seconds: float = 300.0):
        self.repo = repo or RAGRepository()
        self.cache = RAGCacheManager(ttl_seconds=ttl_seconds)

    async def retrieve_knowledge(
        self,
        query_code: str,
        language: str = "python",
        limit: int = 3
    ) -> List[str]:
        """
        Main RAG retrieval entry point with TTL Caching:
        1. Checks in-memory RAG Cache for matching query.
        2. Generates vector embedding for query_code using Gemini text-embedding-004.
        3. Queries MongoDB Atlas Vector Search ($vectorSearch).
        4. If vector search is unavailable, empty, or unindexed, gracefully falls back to seed knowledge documents.
        """
        if not query_code or not query_code.strip():
            return [doc.content for doc in SEED_KNOWLEDGE_DOCS[:limit]]

        # Check Cache
        cached_result = self.cache.get(query_code=query_code, language=language, limit=limit)
        if cached_result is not None:
            return cached_result

        logger.info(f"RAGService retrieving knowledge for language: '{language}'...")

        result_docs: List[str] = []

        # 1. Attempt Vector Search via Gemini Embeddings + MongoDB Atlas
        try:
            query_vector = await embeddings_service.aembed_query(query_code[:1000])
            matched_docs = await self.repo.vector_search(query_vector=query_vector, limit=limit)
            if matched_docs:
                logger.info(f"RAG Vector Search retrieved {len(matched_docs)} documents.")
                result_docs = [f"[{doc.title}]: {doc.content}" for doc in matched_docs]
        except Exception as vec_err:
            logger.warning(f"RAG Vector Search unavailable ({vec_err}). Using graceful seed fallback.")

        # 2. Graceful Fallback: Filter seed docs matching language or general standards
        if not result_docs:
            fallback_docs = [
                doc for doc in SEED_KNOWLEDGE_DOCS
                if doc.language in ["general", language.lower()]
            ]
            if not fallback_docs:
                fallback_docs = SEED_KNOWLEDGE_DOCS

            selected_docs = fallback_docs[:limit]
            result_docs = [f"[{doc.title}]: {doc.content}" for doc in selected_docs]

        # Store in Cache
        self.cache.set(query_code=query_code, language=language, limit=limit, value=result_docs)
        return result_docs


rag_service = RAGService()
