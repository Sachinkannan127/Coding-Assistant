import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from backend.app.auth import get_current_user
from backend.app.db.repositories.user_repository import UserRepository
from backend.app.db.repositories.profile_repository import ProfileRepository
from backend.app.models.user_profile_connector import (
    UserDocument,
    ProfileDocument,
    SyncUserRequest,
    UpdateProfileRequest
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/users/sync", status_code=status.HTTP_200_OK, response_model=Dict[str, Any])
async def sync_user(
    body: Optional[SyncUserRequest] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Sync current authenticated user data into MongoDB 'users' collection and initialize default 'profiles' document.
    """
    user_id = current_user.get("user_id", "dev_guest_user")
    email = (body and body.email) or current_user.get("email") or "guest@codepilot.local"
    first_name = (body and body.first_name) or current_user.get("first_name")
    last_name = (body and body.last_name) or current_user.get("last_name")
    image_url = (body and body.image_url) or current_user.get("picture")

    user_repo = UserRepository()
    profile_repo = ProfileRepository()

    # Upsert User document
    user_doc = UserDocument(
        user_id=user_id,
        email=email,
        first_name=first_name,
        last_name=last_name,
        image_url=image_url
    )
    await user_repo.create_or_update_user(user_doc)
    await user_repo.update_last_login(user_id)

    # Ensure profile document exists
    existing_profile = await profile_repo.get_profile_by_user_id(user_id)
    if not existing_profile:
        new_profile = ProfileDocument(user_id=user_id)
        await profile_repo.create_or_update_profile(new_profile)

    return {
        "status": "success",
        "message": "User and profile synced with MongoDB",
        "user_id": user_id,
        "email": email
    }


@router.get("/users/me", status_code=status.HTTP_200_OK)
async def get_my_user(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Fetch current user record from MongoDB 'users' collection."""
    user_id = current_user.get("user_id", "dev_guest_user")
    user_repo = UserRepository()
    user_doc = await user_repo.get_user_by_id(user_id)
    if not user_doc:
        # Auto-create guest user record if not existing
        user_doc = UserDocument(
            user_id=user_id,
            email=current_user.get("email") or "guest@codepilot.local",
            first_name=current_user.get("first_name"),
            last_name=current_user.get("last_name"),
            image_url=current_user.get("picture")
        )
        await user_repo.create_or_update_user(user_doc)

    return user_doc.model_dump()


@router.get("/profiles/me", status_code=status.HTTP_200_OK)
async def get_my_profile(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Fetch current user profile document from MongoDB 'profiles' collection."""
    user_id = current_user.get("user_id", "dev_guest_user")
    profile_repo = ProfileRepository()
    profile_doc = await profile_repo.get_profile_by_user_id(user_id)
    if not profile_doc:
        profile_doc = ProfileDocument(user_id=user_id)
        await profile_repo.create_or_update_profile(profile_doc)

    return profile_doc.model_dump()


@router.put("/profiles/me", status_code=status.HTTP_200_OK)
async def update_my_profile(
    body: UpdateProfileRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update profile fields in MongoDB 'profiles' collection for current user."""
    user_id = current_user.get("user_id", "dev_guest_user")
    profile_repo = ProfileRepository()

    existing_profile = await profile_repo.get_profile_by_user_id(user_id)
    if not existing_profile:
        existing_profile = ProfileDocument(user_id=user_id)

    # Apply provided updates
    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None and hasattr(existing_profile, key):
            setattr(existing_profile, key, value)

    updated_profile = await profile_repo.create_or_update_profile(existing_profile)
    return {
        "status": "success",
        "message": "Profile updated in MongoDB",
        "profile": updated_profile.model_dump()
    }
