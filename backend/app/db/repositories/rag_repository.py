from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.app.db.mongodb import db_manager
from backend.app.models.review_schemas import RAGDocument


class RAGRepository:
    """Repository handling operations for 'rag_documents' vector search collection."""

    def __init__(self, db: Optional[AsyncIOMotorDatabase] = None):
        self._db_override = db

    @property
    def db(self) -> AsyncIOMotorDatabase:
        return self._db_override if self._db_override is not None else db_manager.get_db()

    @property
    def rag_collection(self):
        return self.db["rag_documents"]

    async def insert_document(self, doc: RAGDocument) -> RAGDocument:
        """Insert a RAG knowledge document into MongoDB."""
        doc_dict = doc.model_dump(mode="python")
        await self.rag_collection.insert_one(doc_dict)
        return doc

    async def get_document_by_id(self, doc_id: str) -> Optional[RAGDocument]:
        """Retrieve a RAG document by its unique doc_id."""
        doc = await self.rag_collection.find_one({"doc_id": doc_id})
        if doc:
            doc.pop("_id", None)
            return RAGDocument(**doc)
        return None

    async def list_documents_by_category(self, category: str) -> List[RAGDocument]:
        """Fetch all RAG documents belonging to a specified category."""
        cursor = self.rag_collection.find({"category": category})
        documents = []
        async for doc in cursor:
            doc.pop("_id", None)
            documents.append(RAGDocument(**doc))
        return documents

    async def vector_search(self, query_vector: List[float], limit: int = 3) -> List[RAGDocument]:
        """Execute MongoDB Atlas $vectorSearch aggregation pipeline."""
        pipeline = [
            {
                "$vectorSearch": {
                    "index": "vector_index",
                    "path": "embedding",
                    "queryVector": query_vector,
                    "numCandidates": 20,
                    "limit": limit
                }
            }
        ]
        documents = []
        try:
            cursor = self.rag_collection.aggregate(pipeline)
            async for doc in cursor:
                doc.pop("_id", None)
                documents.append(RAGDocument(**doc))
        except Exception:
            # Vector index might not be created on local MongoDB or Atlas cluster
            pass
        return documents

