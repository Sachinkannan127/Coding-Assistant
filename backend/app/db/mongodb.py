import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from backend.app.config import settings

logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Async MongoDB Database Manager using Motor.
    Manages connection lifecycle and provides database access across the application.
    """
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None

    @classmethod
    async def connect(cls) -> str:
        """
        Initialize MongoDB client, verify connection with a ping, and return connection state.
        States: 'connecting' -> 'connected' (or raises error if connection fails).
        """
        if cls.client is not None:
            logger.info("MongoDB client already initialized.")
            return "connected"

        try:
            logger.info("Connecting to MongoDB database...")
            cls.client = AsyncIOMotorClient(
                settings.MONGODB_URI,
                serverSelectionTimeoutMS=5000
            )
            cls.db = cls.client[settings.MONGODB_DATABASE]
            
            # Ping database to confirm connection
            await cls.client.admin.command("ping")
            logger.info(f"Successfully connected to MongoDB database: '{settings.MONGODB_DATABASE}'")
            
            # Initialize Collection Indexes
            await cls.create_indexes()
            return "connected"
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            cls.client = None
            cls.db = None
            raise e

    @classmethod
    async def create_indexes(cls) -> None:
        """Ensure required collection indexes exist in MongoDB."""
        if cls.db is None:
            return
        try:
            logger.info("Initializing collection indexes for users, profiles, and connectors...")
            # Users collection indexes
            await cls.db["users"].create_index("user_id", unique=True)
            await cls.db["users"].create_index("email")

            # Profiles collection indexes
            await cls.db["profiles"].create_index("user_id", unique=True)

            # Connectors collection indexes
            await cls.db["connectors"].create_index(
                [("user_id", 1), ("connector_id", 1)],
                unique=True
            )
            logger.info("Collection indexes created successfully.")
        except Exception as e:
            logger.warning(f"Error creating collection indexes: {e}")

    @classmethod
    async def close(cls) -> None:
        """Close MongoDB client connection."""
        if cls.client is not None:
            logger.info("Closing MongoDB client connection...")
            cls.client.close()
            cls.client = None
            cls.db = None
            logger.info("MongoDB connection closed.")

    @classmethod
    def get_db(cls) -> AsyncIOMotorDatabase:
        """Get the active MongoDB database instance."""
        if cls.db is None:
            raise RuntimeError("Database connection not initialized. Call connect() first.")
        return cls.db

    @classmethod
    async def ping(cls) -> bool:
        """Ping MongoDB server to verify connectivity status."""
        if cls.client is None:
            return False
        try:
            await cls.client.admin.command("ping")
            return True
        except Exception as e:
            logger.warning(f"MongoDB ping failed: {e}")
            return False


db_manager = DatabaseManager


async def connect_mongodb() -> dict:
    """
    Connect to MongoDB database and verify connection state ('connecting' -> 'connected').
    """
    logger.info("Connecting to MongoDB...")
    status_state = await db_manager.connect()
    return {
        "status": status_state,
        "database": settings.MONGODB_DATABASE,
        "is_alive": await db_manager.ping()
    }

