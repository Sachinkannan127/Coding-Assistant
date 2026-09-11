from datetime import datetime, timezone
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.app.db.mongodb import db_manager
from backend.app.models.user_profile_connector import ProfileDocument


class ProfileRepository:
    """Repository handling CRUD operations for 'profiles' MongoDB collection."""

    def __init__(self, db: Optional[AsyncIOMotorDatabase] = None):
        self._db_override = db

    @property
    def db(self) -> AsyncIOMotorDatabase:
        return self._db_override if self._db_override is not None else db_manager.get_db()

    @property
    def collection(self):
        return self.db["profiles"]

    async def create_or_update_profile(self, profile: ProfileDocument) -> ProfileDocument:
        """
        Upsert a profile document into MongoDB by user_id.
        """
        profile.updated_at = datetime.now(timezone.utc)
        profile_dict = profile.model_dump(mode="python")
        await self.collection.update_one(
            {"user_id": profile.user_id},
            {"$set": profile_dict},
            upsert=True
        )
        return profile

    async def get_profile_by_user_id(self, user_id: str) -> Optional[ProfileDocument]:
        """Fetch a single profile document by user_id."""
        doc = await self.collection.find_one({"user_id": user_id})
        if doc:
            doc.pop("_id", None)
            return ProfileDocument(**doc)
        return None

    async def delete_profile(self, user_id: str) -> bool:
        """Delete profile document by user_id."""
        result = await self.collection.delete_one({"user_id": user_id})
        return result.deleted_count > 0
