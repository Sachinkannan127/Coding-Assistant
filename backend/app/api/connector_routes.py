import logging
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from backend.app.auth import get_current_user
from backend.app.db.repositories.connector_repository import ConnectorRepository
from backend.app.models.user_profile_connector import (
    ConnectorDocument,
    ConnectConnectorRequest
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/connectors", status_code=status.HTTP_200_OK, response_model=List[Dict[str, Any]])
async def list_connectors(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Fetch all saved MCP connectors for current user from MongoDB 'connectors' collection."""
    user_id = current_user.get("user_id", "dev_guest_user")
    connector_repo = ConnectorRepository()
    connectors = await connector_repo.get_user_connectors(user_id)
    return [c.model_dump() for c in connectors]


@router.post("/connectors/connect", status_code=status.HTTP_200_OK, response_model=Dict[str, Any])
async def connect_connector(
    body: ConnectConnectorRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Save or update MCP connector status to 'connected' and store access token in MongoDB 'connectors' collection.
    """
    user_id = current_user.get("user_id", "dev_guest_user")
    token = body.access_token.strip()

    if not token or len(token) < 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token provided. Token must be at least 4 characters long."
        )

    connector_repo = ConnectorRepository()
    existing = await connector_repo.get_connector(user_id, body.connector_id)

    name = body.name or (existing.name if existing else body.connector_id.replace("_", " ").title())
    provider = body.provider or (existing.provider if existing else "custom")

    connector_doc = ConnectorDocument(
        connector_id=body.connector_id,
        user_id=user_id,
        name=name,
        provider=provider,
        status="connected",
        access_token=token,
        config=body.config or {}
    )

    saved = await connector_repo.save_connector(connector_doc)
    logger.info(f"Connector '{body.connector_id}' connected for user '{user_id}' in MongoDB.")

    return {
        "status": "success",
        "message": f"Connector '{body.connector_id}' connected successfully",
        "connector": saved.model_dump()
    }


@router.post("/connectors/disconnect", status_code=status.HTTP_200_OK, response_model=Dict[str, Any])
async def disconnect_connector(
    connector_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update MCP connector status to 'disconnected' in MongoDB 'connectors' collection."""
    user_id = current_user.get("user_id", "dev_guest_user")
    connector_repo = ConnectorRepository()
    
    updated = await connector_repo.update_connector_status(
        user_id=user_id,
        connector_id=connector_id,
        status="disconnected",
        access_token=""
    )

    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connector '{connector_id}' not found for user."
        )

    return {
        "status": "success",
        "message": f"Connector '{connector_id}' disconnected"
    }


@router.delete("/connectors/{connector_id}", status_code=status.HTTP_200_OK, response_model=Dict[str, Any])
async def delete_connector(
    connector_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete MCP connector document from MongoDB 'connectors' collection."""
    user_id = current_user.get("user_id", "dev_guest_user")
    connector_repo = ConnectorRepository()
    deleted = await connector_repo.delete_connector(user_id, connector_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connector '{connector_id}' not found for user."
        )

    return {
        "status": "success",
        "message": f"Connector '{connector_id}' deleted from database"
    }
