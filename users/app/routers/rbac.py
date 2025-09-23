"""
RBAC Management Router

This router provides endpoints for managing roles, permissions, and user role assignments.
Only accessible by administrators.
"""

from typing import List, Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, delete

from ..db import get_db_session
from ..models import User
from ..rbac_models import Role, Permission, user_roles, role_permissions
from ..rbac_schemas import (
    PermissionCreate, PermissionRead,
    RoleCreate, RoleRead, RoleUpdate,
    UserRoleAssignment, UserRoleResponse,
    PermissionCheck, PermissionCheckResponse,
    UserWithRoles
)
from ..rbac_auth import require_admin, get_user_permissions, get_user_roles

router = APIRouter(prefix="/rbac", tags=["rbac"])

# Permission management endpoints
@router.post("/permissions", response_model=PermissionRead, status_code=status.HTTP_201_CREATED)
async def create_permission(
    permission_data: PermissionCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_admin())
):
    """Create a new permission. Admin only."""
    # Check if permission already exists
    existing = await session.scalar(
        select(Permission).where(Permission.name == permission_data.name)
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Permission already exists"
        )
    
    permission = Permission(**permission_data.model_dump())
    session.add(permission)
    await session.flush()
    return PermissionRead.model_validate(permission)

@router.get("/permissions", response_model=List[PermissionRead])
async def list_permissions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_admin())
):
    """List all permissions. Admin only."""
    result = await session.execute(
        select(Permission).offset(skip).limit(limit).order_by(Permission.name)
    )
    permissions = result.scalars().all()
    return [PermissionRead.model_validate(p) for p in permissions]

@router.delete("/permissions/{permission_id}")
async def delete_permission(
    permission_id: int,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_admin())
):
    """Delete a permission. Admin only."""
    permission = await session.get(Permission, permission_id)
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found"
        )
    
    await session.delete(permission)
    await session.flush()
    return {"message": "Permission deleted successfully"}

# Role management endpoints
@router.post("/roles", response_model=RoleRead, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: RoleCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_admin())
):
    """Create a new role with permissions. Admin only."""
    # Check if role already exists
    existing = await session.scalar(
        select(Role).where(Role.name == role_data.name)
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role already exists"
        )
    
    # Create role
    role_dict = role_data.model_dump(exclude={"permission_ids"})
    role = Role(**role_dict)
    session.add(role)
    await session.flush()
    
    # Add permissions
    if role_data.permission_ids:
        permissions = await session.execute(
            select(Permission).where(Permission.id.in_(role_data.permission_ids))
        )
        role.permissions = list(permissions.scalars().all())
        await session.flush()
    
    # Reload with permissions
    await session.refresh(role, ["permissions"])
    return RoleRead.model_validate(role)

@router.get("/roles", response_model=List[RoleRead])
async def list_roles(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_admin())
):
    """List all roles with their permissions. Admin only."""
    result = await session.execute(
        select(Role)
        .options(selectinload(Role.permissions))
        .offset(skip)
        .limit(limit)
        .order_by(Role.name)
    )
    roles = result.scalars().all()
    return [RoleRead.model_validate(r) for r in roles]

@router.get("/roles/{role_id}", response_model=RoleRead)
async def get_role(
    role_id: int,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_admin())
):
    """Get a specific role with permissions. Admin only."""
    role = await session.scalar(
        select(Role)
        .options(selectinload(Role.permissions))
        .where(Role.id == role_id)
    )
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    return RoleRead.model_validate(role)

@router.put("/roles/{role_id}", response_model=RoleRead)
async def update_role(
    role_id: int,
    role_update: RoleUpdate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_admin())
):
    """Update a role and its permissions. Admin only."""
    role = await session.scalar(
        select(Role).options(selectinload(Role.permissions)).where(Role.id == role_id)
    )
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    if role.is_system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify system role"
        )
    
    # Update basic fields
    update_data = role_update.model_dump(exclude_unset=True, exclude={"permission_ids"})
    for field, value in update_data.items():
        setattr(role, field, value)
    
    # Update permissions if provided
    if role_update.permission_ids is not None:
        permissions = await session.execute(
            select(Permission).where(Permission.id.in_(role_update.permission_ids))
        )
        role.permissions = list(permissions.scalars().all())
    
    await session.flush()
    await session.refresh(role, ["permissions"])
    return RoleRead.model_validate(role)

@router.delete("/roles/{role_id}")
async def delete_role(
    role_id: int,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_admin())
):
    """Delete a role. Admin only."""
    role = await session.get(Role, role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    if role.is_system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete system role"
        )
    
    await session.delete(role)
    await session.flush()
    return {"message": "Role deleted successfully"}

# User role assignment endpoints
@router.post("/users/{user_id}/roles", response_model=UserRoleResponse)
async def assign_user_roles(
    user_id: int,
    assignment: UserRoleAssignment,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_admin())
):
    """Assign roles to a user. Admin only."""
    if assignment.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID mismatch"
        )
    
    # Get user
    user = await session.scalar(
        select(User).options(selectinload(User.roles)).where(User.id == user_id)
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get roles
    roles = await session.execute(
        select(Role).where(Role.id.in_(assignment.role_ids))
    )
    user.roles = list(roles.scalars().all())
    await session.flush()
    
    # Reload user with roles and permissions
    await session.refresh(user, ["roles"])
    return UserRoleResponse(
        user_id=user.id,
        roles=[RoleRead.model_validate(r) for r in user.roles],
        message="Roles assigned successfully"
    )

@router.get("/users/{user_id}/roles", response_model=List[RoleRead])
async def get_user_roles(
    user_id: int,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_admin())
):
    """Get all roles assigned to a user. Admin only."""
    user = await session.scalar(
        select(User).options(selectinload(User.roles)).where(User.id == user_id)
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return [RoleRead.model_validate(r) for r in user.roles]

@router.get("/users", response_model=List[UserWithRoles])
async def list_users_with_roles(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_admin())
):
    """List all users with their roles. Admin only."""
    result = await session.execute(
        select(User)
        .options(selectinload(User.roles))
        .offset(skip)
        .limit(limit)
        .order_by(User.id)
    )
    users = result.scalars().all()
    return [UserWithRoles.model_validate(u) for u in users]

# Permission checking endpoints
@router.post("/check-permission", response_model=PermissionCheckResponse)
async def check_permission(
    permission_check: PermissionCheck,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_admin())
):
    """Check if current user has a specific permission."""
    # Reload user with roles and permissions
    user = await session.scalar(
        select(User)
        .options(selectinload(User.roles).selectinload(Role.permissions))
        .where(User.id == current_user.id)
    )
    
    has_permission = user.has_permission(permission_check.resource, permission_check.action)
    
    # Find which roles granted the permission
    granted_by_roles = []
    if has_permission and user:
        for role in user.roles:
            if role.has_permission(permission_check.resource, permission_check.action):
                granted_by_roles.append(role.name)
    
    return PermissionCheckResponse(
        has_permission=has_permission,
        user_id=current_user.id,
        resource=permission_check.resource,
        action=permission_check.action,
        granted_by_roles=granted_by_roles
    )
