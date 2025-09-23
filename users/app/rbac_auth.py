"""
RBAC Authentication and Authorization Utilities

This module provides decorators and dependencies for role-based access control.
"""

from functools import wraps
from typing import List, Callable, Any
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select

from .auth import get_current_active_user
from .db import get_db_session
from .models import User
from .rbac_models import Role, Permission


class RBACDependencies:
    """Collection of RBAC-related FastAPI dependencies."""
    
    @staticmethod
    def require_permission(resource: str, action: str):
        """
        Dependency factory that creates a dependency requiring specific permission.
        
        Usage:
            @app.get("/admin/users")
            async def get_users(user: User = Depends(require_permission("user", "read"))):
                ...
        """
        async def permission_dependency(
            current_user: User = Depends(get_current_active_user),
            session: AsyncSession = Depends(get_db_session)
        ) -> User:
            # Reload user with roles to ensure we have fresh data
            user = await session.scalar(
                select(User)
                .options(selectinload(User.roles).selectinload(Role.permissions))
                .where(User.id == current_user.id)
            )
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Check if user has required permission
            if not user.has_permission(resource, action):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied. Required: {resource}:{action}"
                )
            
            return user
        
        return permission_dependency
    
    @staticmethod
    def require_role(role_name: str):
        """
        Dependency factory that creates a dependency requiring specific role.
        
        Usage:
            @app.get("/admin/dashboard")
            async def admin_dashboard(user: User = Depends(require_role("admin"))):
                ...
        """
        async def role_dependency(
            current_user: User = Depends(get_current_active_user),
            session: AsyncSession = Depends(get_db_session)
        ) -> User:
            # Reload user with roles
            user = await session.scalar(
                select(User)
                .options(selectinload(User.roles))
                .where(User.id == current_user.id)
            )
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Check if user has required role
            if not user.has_role(role_name):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role required: {role_name}"
                )
            
            return user
        
        return role_dependency
    
    @staticmethod
    def require_admin():
        """Dependency that requires admin privileges (superuser, admin role, or admin:all permission)."""
        async def admin_dependency(
            current_user: User = Depends(get_current_active_user),
            session: AsyncSession = Depends(get_db_session)
        ) -> User:
            # Reload user with roles
            user = await session.scalar(
                select(User)
                .options(selectinload(User.roles).selectinload(Role.permissions))
                .where(User.id == current_user.id)
            )
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Check admin privileges
            if not user.is_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Administrator privileges required"
                )
            
            return user
        
        return admin_dependency


# Convenience dependencies
require_permission = RBACDependencies.require_permission
require_role = RBACDependencies.require_role
require_admin = RBACDependencies.require_admin


async def get_user_permissions(user: User, session: AsyncSession) -> List[Permission]:
    """Get all permissions for a user through their roles."""
    user_with_roles = await session.scalar(
        select(User)
        .options(selectinload(User.roles).selectinload(Role.permissions))
        .where(User.id == user.id)
    )
    
    permissions = []
    if user_with_roles:
        for role in user_with_roles.roles:
            permissions.extend(role.permissions)
    
    # Remove duplicates
    seen = set()
    unique_permissions = []
    for perm in permissions:
        if perm.id not in seen:
            seen.add(perm.id)
            unique_permissions.append(perm)
    
    return unique_permissions


async def get_user_roles(user: User, session: AsyncSession) -> List[Role]:
    """Get all roles for a user."""
    user_with_roles = await session.scalar(
        select(User)
        .options(selectinload(User.roles))
        .where(User.id == user.id)
    )
    
    return user_with_roles.roles if user_with_roles else []
