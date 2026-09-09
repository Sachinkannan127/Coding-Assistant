import logging
from typing import List, Optional
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


class RAGService:
    """
    RAG Service handling knowledge retrieval, embedding generation,
    MongoDB Atlas vector search, and graceful failover fallback.
    """

    def __init__(self, repo: Optional[RAGRepository] = None):
        self.repo = repo or RAGRepository()

    async def retrieve_knowledge(
        self,
        query_code: str,
        language: str = "python",
        limit: int = 3
    ) -> List[str]:
        """
        Main RAG retrieval entry point:
        1. Generates vector embedding for query_code using Gemini text-embedding-004.
        2. Queries MongoDB Atlas Vector Search ($vectorSearch).
        3. If vector search returns documents, formats their title + content.
        4. If vector search is unavailable, empty, or unindexed, gracefully falls back to seed knowledge documents.
        """
        logger.info(f"RAGService retrieving knowledge for language: '{language}'...")
        if not query_code or not query_code.strip():
            return [doc.content for doc in SEED_KNOWLEDGE_DOCS[:limit]]

        # 1. Attempt Vector Search via Gemini Embeddings + MongoDB Atlas
        try:
            query_vector = await embeddings_service.aembed_query(query_code[:1000])
            matched_docs = await self.repo.vector_search(query_vector=query_vector, limit=limit)
            if matched_docs:
                logger.info(f"RAG Vector Search retrieved {len(matched_docs)} documents.")
                return [f"[{doc.title}]: {doc.content}" for doc in matched_docs]
        except Exception as vec_err:
            logger.warning(f"RAG Vector Search unavailable ({vec_err}). Using graceful seed fallback.")

        # 2. Graceful Fallback: Filter seed docs matching language or general standards
        fallback_docs = [
            doc for doc in SEED_KNOWLEDGE_DOCS
            if doc.language in ["general", language.lower()]
        ]
        if not fallback_docs:
            fallback_docs = SEED_KNOWLEDGE_DOCS

        selected_docs = fallback_docs[:limit]
        return [f"[{doc.title}]: {doc.content}" for doc in selected_docs]


rag_service = RAGService()
