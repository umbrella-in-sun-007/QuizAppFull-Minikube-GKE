from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import get_current_active_user
from ..db import get_db_session
from .. import models
from ..schemas import (
    UserProfile, 
    UserProfileUpdate, 
    UserPreferencesUpdate
)

router = APIRouter(prefix="/profile", tags=["profile"])

@router.get("/me", response_model=UserProfile)
async def get_my_profile(
    current_user: Annotated[models.User, Depends(get_current_active_user)]
):
    """Get current user's complete profile."""
    return UserProfile.model_validate(current_user)

@router.put("/me", response_model=UserProfile)
async def update_my_profile(
    profile_update: UserProfileUpdate,
    current_user: Annotated[models.User, Depends(get_current_active_user)],
    session: AsyncSession = Depends(get_db_session)
):
    """Update current user's profile information."""
    update_data = profile_update.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    await session.flush()
    return UserProfile.model_validate(current_user)

@router.get("/me/preferences")
async def get_my_preferences(
    current_user: Annotated[models.User, Depends(get_current_active_user)]
):
    """Get current user's preferences."""
    return {
        "preferences": current_user.preferences or {},
        "user_id": current_user.id
    }

@router.put("/me/preferences")
async def update_my_preferences(
    preferences_update: UserPreferencesUpdate,
    current_user: Annotated[models.User, Depends(get_current_active_user)],
    session: AsyncSession = Depends(get_db_session)
):
    """Update current user's preferences."""
    update_data = preferences_update.model_dump(exclude_unset=True)
    
    # Merge with existing preferences
    current_preferences = current_user.preferences or {}
    current_preferences.update(update_data)
    current_user.preferences = current_preferences
    
    await session.flush()
    return {
        "message": "Preferences updated successfully",
        "preferences": current_user.preferences,
        "user_id": current_user.id
    }

@router.delete("/me/avatar")
async def remove_my_avatar(
    current_user: Annotated[models.User, Depends(get_current_active_user)],
    session: AsyncSession = Depends(get_db_session)
):
    """Remove current user's avatar."""
    current_user.avatar_url = None
    await session.flush()
    return {"message": "Avatar removed successfully"}

@router.get("/{user_id}", response_model=UserProfile)
async def get_user_profile(
    user_id: int,
    current_user: Annotated[models.User, Depends(get_current_active_user)],
    session: AsyncSession = Depends(get_db_session)
):
    """Get a user's public profile (privacy settings will be considered later)."""
    user = await session.get(models.User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user.is_active:
        raise HTTPException(status_code=404, detail="User not found")
    
    # For now, return full profile. Later we'll implement privacy controls
    return UserProfile.model_validate(user)
