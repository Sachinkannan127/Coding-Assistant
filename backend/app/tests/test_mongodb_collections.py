import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock
from backend.app.models.user_profile_connector import (
    UserDocument,
    ProfileDocument,
    ConnectorDocument
)
from backend.app.db.repositories.user_repository import UserRepository
from backend.app.db.repositories.profile_repository import ProfileRepository
from backend.app.db.repositories.connector_repository import ConnectorRepository


class InMemoryAsyncCollection:
    def __init__(self):
        self.docs = []

    async def update_one(self, filter_dict, update_dict, upsert=False):
        set_fields = update_dict.get("$set", {})
        matched = False
        for i, doc in enumerate(self.docs):
            match = all(doc.get(k) == v for k, v in filter_dict.items())
            if match:
                matched = True
                self.docs[i].update(set_fields)
                break
        if not matched and upsert:
            new_doc = {**set_fields}
            self.docs.append(new_doc)
        res = MagicMock()
        res.modified_count = 1 if matched else 0
        return res

    async def find_one(self, filter_dict):
        for doc in self.docs:
            if all(doc.get(k) == v for k, v in filter_dict.items()):
                return dict(doc)
        return None

    def find(self, filter_dict):
        results = [dict(d) for d in self.docs if all(d.get(k) == v for k, v in filter_dict.items())]
        
        class AsyncCursor:
            def __init__(self, data):
                self.data = data
            def sort(self, *args, **kwargs):
                return self
            def skip(self, *args, **kwargs):
                return self
            def limit(self, *args, **kwargs):
                return self
            def __aiter__(self):
                self._iter = iter(self.data)
                return self
            async def __anext__(self):
                try:
                    return next(self._iter)
                except StopIteration:
                    raise StopAsyncIteration

        return AsyncCursor(results)

    async def delete_one(self, filter_dict):
        initial_len = len(self.docs)
        self.docs = [d for d in self.docs if not all(d.get(k) == v for k, v in filter_dict.items())]
        res = MagicMock()
        res.deleted_count = initial_len - len(self.docs)
        return res


class MockAsyncDatabase:
    def __init__(self):
        self.collections = {}

    def __getitem__(self, name):
        if name not in self.collections:
            self.collections[name] = InMemoryAsyncCollection()
        return self.collections[name]


def test_user_repository_crud():
    async def _test():
        db = MockAsyncDatabase()
        repo = UserRepository(db=db)

        # 1. Create User
        user = UserDocument(
            user_id="user_test_123",
            email="testuser@codepilot.io",
            first_name="Test",
            last_name="Developer",
            image_url="https://example.com/avatar.png"
        )
        saved_user = await repo.create_or_update_user(user)
        assert saved_user.user_id == "user_test_123"
        assert saved_user.email == "testuser@codepilot.io"

        # 2. Get User by ID
        fetched_user = await repo.get_user_by_id("user_test_123")
        assert fetched_user is not None
        assert fetched_user.email == "testuser@codepilot.io"
        assert fetched_user.first_name == "Test"

        # 3. Get User by Email
        fetched_by_email = await repo.get_user_by_email("testuser@codepilot.io")
        assert fetched_by_email is not None
        assert fetched_by_email.user_id == "user_test_123"

        # 4. List Users
        users_list = await repo.list_users()
        assert len(users_list) == 1

        # 5. Delete User
        deleted = await repo.delete_user("user_test_123")
        assert deleted is True
        assert await repo.get_user_by_id("user_test_123") is None

    asyncio.run(_test())


def test_profile_repository_crud():
    async def _test():
        db = MockAsyncDatabase()
        repo = ProfileRepository(db=db)

        # 1. Create Profile
        profile = ProfileDocument(
            user_id="user_test_123",
            bio="Full-Stack AI Engineer",
            company="CodePilot Labs",
            github_username="testdev",
            preferred_theme="dark",
            preferred_language="typescript"
        )
        saved_profile = await repo.create_or_update_profile(profile)
        assert saved_profile.user_id == "user_test_123"

        # 2. Get Profile
        fetched = await repo.get_profile_by_user_id("user_test_123")
        assert fetched is not None
        assert fetched.company == "CodePilot Labs"
        assert fetched.github_username == "testdev"

        # 3. Update Profile
        fetched.bio = "Updated Bio Statement"
        updated = await repo.create_or_update_profile(fetched)
        assert updated.bio == "Updated Bio Statement"

        # 4. Delete Profile
        deleted = await repo.delete_profile("user_test_123")
        assert deleted is True
        assert await repo.get_profile_by_user_id("user_test_123") is None

    asyncio.run(_test())


def test_connector_repository_crud():
    async def _test():
        db = MockAsyncDatabase()
        repo = ConnectorRepository(db=db)

        # 1. Create/Save Connector
        connector = ConnectorDocument(
            connector_id="github_mcp",
            user_id="user_test_123",
            name="GitHub Integration MCP",
            provider="github",
            status="connected",
            access_token="ghp_mock_secret_token_12345"
        )
        saved = await repo.save_connector(connector)
        assert saved.connector_id == "github_mcp"
        assert saved.status == "connected"

        # 2. Fetch User Connectors
        user_connectors = await repo.get_user_connectors("user_test_123")
        assert len(user_connectors) == 1
        assert user_connectors[0].connector_id == "github_mcp"

        # 3. Update Connector Status
        updated = await repo.update_connector_status(
            user_id="user_test_123",
            connector_id="github_mcp",
            status="disconnected"
        )
        assert updated is True

        fetched = await repo.get_connector("user_test_123", "github_mcp")
        assert fetched is not None
        assert fetched.status == "disconnected"

        # 4. Delete Connector
        deleted = await repo.delete_connector("user_test_123", "github_mcp")
        assert deleted is True
        assert await repo.get_connector("user_test_123", "github_mcp") is None

    asyncio.run(_test())
