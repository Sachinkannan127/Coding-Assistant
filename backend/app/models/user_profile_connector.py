from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, EmailStr


class UserDocument(BaseModel):
    """
    MongoDB User Document Model representing stored user account entity.
    Collection name: 'users'
    """
    user_id: str = Field(..., description="Unique Clerk or System User ID (e.g., user_2xxx)")
    email: str = Field(..., description="User primary email address")
    first_name: Optional[str] = Field(None, description="User first name")
    last_name: Optional[str] = Field(None, description="User last name")
    image_url: Optional[str] = Field(None, description="User avatar image URL")
    role: str = Field("user", description="User access role (e.g. user, admin)")
    is_active: bool = Field(True, description="Account active status")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login_at: Optional[datetime] = Field(None, description="Timestamp of last login")


class ProfileDocument(BaseModel):
    """
    MongoDB Profile Document Model representing extended user bio and settings.
    Collection name: 'profiles'
    """
    user_id: str = Field(..., description="Foreign key reference to User user_id")
    bio: Optional[str] = Field(None, description="User biography summary")
    company: Optional[str] = Field(None, description="Company or organization name")
    location: Optional[str] = Field(None, description="Location or city")
    website: Optional[str] = Field(None, description="Personal website or portfolio URL")
    github_username: Optional[str] = Field(None, description="GitHub handle")
    preferred_theme: str = Field("dark", description="UI theme preference ('dark' | 'light')")
    preferred_language: str = Field("typescript", description="Primary code language preference")
    notifications_enabled: bool = Field(True, description="Email/App notifications toggle")
    custom_settings: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary custom key-value settings")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ConnectorDocument(BaseModel):
    """
    MongoDB Connector Document Model representing user-configured MCP connector.
    Collection name: 'connectors'
    """
    connector_id: str = Field(..., description="ID of connector (e.g., github_mcp, slack_mcp, jira_mcp)")
    user_id: str = Field(..., description="User ID owner of this connector credential")
    name: str = Field(..., description="Display name of connector")
    provider: str = Field("custom", description="Provider category (github, slack, jira, custom, oauth)")
    status: str = Field("disconnected", description="Connection status ('connected' | 'disconnected' | 'error')")
    access_token: Optional[str] = Field(None, description="Access token or API key for connector")
    refresh_token: Optional[str] = Field(None, description="Optional OAuth refresh token")
    expires_at: Optional[datetime] = Field(None, description="Token expiration timestamp")
    config: Dict[str, Any] = Field(default_factory=dict, description="Additional endpoint/scope settings")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# API Request/Response Schemas

class SyncUserRequest(BaseModel):
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    image_url: Optional[str] = None


class UpdateProfileRequest(BaseModel):
    bio: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    github_username: Optional[str] = None
    preferred_theme: Optional[str] = None
    preferred_language: Optional[str] = None
    notifications_enabled: Optional[bool] = None
    custom_settings: Optional[Dict[str, Any]] = None


class ConnectConnectorRequest(BaseModel):
    connector_id: str
    name: Optional[str] = None
    provider: Optional[str] = "custom"
    access_token: str
    config: Optional[Dict[str, Any]] = Field(default_factory=dict)
