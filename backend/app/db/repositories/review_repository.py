from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.app.db.mongodb import db_manager
from backend.app.models.review_schemas import CodeReviewDocument, Finding, AgentRunDocument


class ReviewRepository:
    """Repository handling CRUD operations for 'code_reviews', 'review_findings', and 'agent_runs'."""

    def __init__(self, db: Optional[AsyncIOMotorDatabase] = None):
        self._db_override = db

    @property
    def db(self) -> AsyncIOMotorDatabase:
        return self._db_override if self._db_override is not None else db_manager.get_db()

    @property
    def reviews_collection(self):
        return self.db["code_reviews"]

    @property
    def findings_collection(self):
        return self.db["review_findings"]

    @property
    def agent_runs_collection(self):
        return self.db["agent_runs"]

    async def create_review(self, review: CodeReviewDocument) -> CodeReviewDocument:
        """Insert a code review document into MongoDB."""
        review_dict = review.model_dump(mode="python")
        await self.reviews_collection.insert_one(review_dict)
        return review

    async def get_review_by_id(self, review_id: str) -> Optional[CodeReviewDocument]:
        """Fetch a single code review by its review_id."""
        doc = await self.reviews_collection.find_one({"review_id": review_id})
        if doc:
            doc.pop("_id", None)
            return CodeReviewDocument(**doc)
        return None

    async def list_reviews(self, limit: int = 20, skip: int = 0) -> List[CodeReviewDocument]:
        """List code reviews sorted by created_at descending."""
        cursor = self.reviews_collection.find({}).sort("created_at", -1).skip(skip).limit(limit)
        reviews = []
        async for doc in cursor:
            doc.pop("_id", None)
            reviews.append(CodeReviewDocument(**doc))
        return reviews

    async def save_findings(self, review_id: str, findings: List[Finding]) -> List[Finding]:
        """Bulk save findings associated with a review_id."""
        if not findings:
            return []
        
        docs = []
        for finding in findings:
            finding_dict = finding.model_dump(mode="python")
            finding_dict["review_id"] = review_id
            docs.append(finding_dict)
            
        await self.findings_collection.insert_many(docs)
        return findings

    async def get_findings_by_review_id(self, review_id: str) -> List[Finding]:
        """Fetch all findings associated with a given review_id."""
        cursor = self.findings_collection.find({"review_id": review_id})
        findings = []
        async for doc in cursor:
            doc.pop("_id", None)
            doc.pop("review_id", None)
            findings.append(Finding(**doc))
        return findings

    async def log_agent_run(self, agent_run: AgentRunDocument) -> AgentRunDocument:
        """Record an agent execution audit log."""
        run_dict = agent_run.model_dump(mode="python")
        await self.agent_runs_collection.insert_one(run_dict)
        return agent_run

    async def get_agent_runs_by_review_id(self, review_id: str) -> List[AgentRunDocument]:
        """Fetch all agent run audit logs for a given review_id."""
        cursor = self.agent_runs_collection.find({"review_id": review_id}).sort("timestamp", 1)
        runs = []
        async for doc in cursor:
            doc.pop("_id", None)
            runs.append(AgentRunDocument(**doc))
        return runs
