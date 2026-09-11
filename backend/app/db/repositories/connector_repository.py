from datetime import datetime, timezone
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.app.db.mongodb import db_manager
from backend.app.models.user_profile_connector import ConnectorDocument


class ConnectorRepository:
    """Repository handling CRUD operations for 'connectors' MongoDB collection."""

    def __init__(self, db: Optional[AsyncIOMotorDatabase] = None):
        self._db_override = db

    @property
    def db(self) -> AsyncIOMotorDatabase:
        return self._db_override if self._db_override is not None else db_manager.get_db()

    @property
    def collection(self):
        return self.db["connectors"]

    async def save_connector(self, connector: ConnectorDocument) -> ConnectorDocument:
        """
        Upsert a connector document into MongoDB matching (user_id, connector_id).
        """
        connector.updated_at = datetime.now(timezone.utc)
        connector_dict = connector.model_dump(mode="python")
        await self.collection.update_one(
            {"user_id": connector.user_id, "connector_id": connector.connector_id},
            {"$set": connector_dict},
            upsert=True
        )
        return connector

    async def get_user_connectors(self, user_id: str) -> List[ConnectorDocument]:
        """Fetch all saved connectors for a given user_id."""
        cursor = self.collection.find({"user_id": user_id}).sort("updated_at", -1)
        connectors = []
        async for doc in cursor:
            doc.pop("_id", None)
            connectors.append(ConnectorDocument(**doc))
        return connectors

    async def get_connector(self, user_id: str, connector_id: str) -> Optional[ConnectorDocument]:
        """Fetch specific connector document by user_id and connector_id."""
        doc = await self.collection.find_one({"user_id": user_id, "connector_id": connector_id})
        if doc:
            doc.pop("_id", None)
            return ConnectorDocument(**doc)
        return None

    async def update_connector_status(
        self,
        user_id: str,
        connector_id: str,
        status: str,
        access_token: Optional[str] = None
    ) -> bool:
        """Update connection status and optional token for specified connector."""
        now = datetime.now(timezone.utc)
        update_fields = {"status": status, "updated_at": now}
        if access_token is not None:
            update_fields["access_token"] = access_token

        result = await self.collection.update_one(
            {"user_id": user_id, "connector_id": connector_id},
            {"$set": update_fields}
        )
        return result.modified_count > 0

    async def delete_connector(self, user_id: str, connector_id: str) -> bool:
        """Remove a connector document from MongoDB."""
        result = await self.collection.delete_one({"user_id": user_id, "connector_id": connector_id})
        return result.deleted_count > 0
