from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import get_current_active_user, get_current_superuser, get_password_hash
from ..db import get_db_session
from .. import models
from ..schemas import UserCreate, UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])

@router.get("", response_model=list[UserRead])
async def list_users(
    current_user: Annotated[models.User, Depends(get_current_superuser)],  # Only superusers can list all users
    session: AsyncSession = Depends(get_db_session)
):
    """List all users (superuser only)."""
    res = await session.execute(select(models.User).order_by(models.User.id))
    return [UserRead.model_validate(u) for u in res.scalars().all()]

@router.get("/me", response_model=UserRead)
async def get_current_user_profile(
    current_user: Annotated[models.User, Depends(get_current_active_user)]
):
    """Get current user's profile."""
    return UserRead.model_validate(current_user)

@router.put("/me", response_model=UserRead)
async def update_current_user(
    user_update: UserUpdate,
    current_user: Annotated[models.User, Depends(get_current_active_user)],
    session: AsyncSession = Depends(get_db_session)
):
    """Update current user's profile."""
    update_data = user_update.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    await session.flush()
    return UserRead.model_validate(current_user)

@router.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: int,
    current_user: Annotated[models.User, Depends(get_current_superuser)],  # Only superusers can view other users
    session: AsyncSession = Depends(get_db_session)
):
    """Get a specific user by ID (superuser only)."""
    user = await session.get(models.User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserRead.model_validate(user)

@router.put("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: Annotated[models.User, Depends(get_current_superuser)],  # Only superusers can update other users
    session: AsyncSession = Depends(get_db_session)
):
    """Update a user (superuser only)."""
    user = await session.get(models.User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = user_update.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(user, field, value)
    
    await session.flush()
    return UserRead.model_validate(user)

@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_user: Annotated[models.User, Depends(get_current_superuser)],  # Only superusers can delete users
    session: AsyncSession = Depends(get_db_session)
):
    """Delete a user (superuser only)."""
    user = await session.get(models.User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    await session.delete(user)
    return {"message": "User deleted successfully"}