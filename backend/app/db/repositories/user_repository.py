from datetime import datetime, timezone
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.app.db.mongodb import db_manager
from backend.app.models.user_profile_connector import UserDocument


class UserRepository:
    """Repository handling CRUD operations for 'users' MongoDB collection."""

    def __init__(self, db: Optional[AsyncIOMotorDatabase] = None):
        self._db_override = db

    @property
    def db(self) -> AsyncIOMotorDatabase:
        return self._db_override if self._db_override is not None else db_manager.get_db()

    @property
    def collection(self):
        return self.db["users"]

    async def create_or_update_user(self, user: UserDocument) -> UserDocument:
        """
        Upsert a user document into MongoDB.
        Updates timestamps and matches on 'user_id'.
        """
        user.updated_at = datetime.now(timezone.utc)
        user_dict = user.model_dump(mode="python")
        await self.collection.update_one(
            {"user_id": user.user_id},
            {"$set": user_dict},
            upsert=True
        )
        return user

    async def get_user_by_id(self, user_id: str) -> Optional[UserDocument]:
        """Fetch a single user document by user_id."""
        doc = await self.collection.find_one({"user_id": user_id})
        if doc:
            doc.pop("_id", None)
            return UserDocument(**doc)
        return None

    async def get_user_by_email(self, email: str) -> Optional[UserDocument]:
        """Fetch a single user document by email address."""
        doc = await self.collection.find_one({"email": email})
        if doc:
            doc.pop("_id", None)
            return UserDocument(**doc)
        return None

    async def list_users(self, limit: int = 50, skip: int = 0) -> List[UserDocument]:
        """List users sorted by created_at descending."""
        cursor = self.collection.find({}).sort("created_at", -1).skip(skip).limit(limit)
        users = []
        async for doc in cursor:
            doc.pop("_id", None)
            users.append(UserDocument(**doc))
        return users

    async def update_last_login(self, user_id: str) -> bool:
        """Update last_login_at timestamp for specified user."""
        now = datetime.now(timezone.utc)
        result = await self.collection.update_one(
            {"user_id": user_id},
            {"$set": {"last_login_at": now, "updated_at": now}}
        )
        return result.modified_count > 0

    async def delete_user(self, user_id: str) -> bool:
        """Delete user document by user_id."""
        result = await self.collection.delete_one({"user_id": user_id})
        return result.deleted_count > 0
