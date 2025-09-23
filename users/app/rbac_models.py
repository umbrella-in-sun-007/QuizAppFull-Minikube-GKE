"""
Role-Based Access Control (RBAC) Models

This module defines the database models for implementing a flexible RBAC system:
- Role: Groups of permissions (e.g., "admin", "moderator", "user")
- Permission: Specific actions (e.g., "user:read", "user:write", "admin:all")
- UserRole: Many-to-many relationship between users and roles
"""

from datetime import datetime, timezone
from typing import List
from sqlalchemy import String, DateTime, Boolean, Text, ForeignKey, Table, Column, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base

# Association table for many-to-many relationship between users and roles
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
    Column('assigned_at', DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)),
    Column('assigned_by_user_id', Integer, ForeignKey('users.id'), nullable=True),
)

# Association table for many-to-many relationship between roles and permissions
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id', ondelete='CASCADE'), primary_key=True),
)

class Permission(Base):
    """
    Represents a specific permission/action that can be performed.
    
    Examples:
    - "user:read" - Can read user information
    - "user:write" - Can modify user information
    - "user:delete" - Can delete users
    - "admin:all" - Full administrative access
    """
    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=True)
    resource: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., "user", "admin", "profile"
    action: Mapped[str] = mapped_column(String(50), nullable=False)    # e.g., "read", "write", "delete", "all"
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    
    # Relationships
    roles: Mapped[List["Role"]] = relationship(
        "Role", 
        secondary=role_permissions, 
        back_populates="permissions"
    )
    
    def __str__(self) -> str:
        return f"{self.resource}:{self.action}"


class Role(Base):
    """
    Represents a role that groups multiple permissions.
    
    Examples:
    - "user" - Basic user permissions
    - "moderator" - Moderate content permissions
    - "admin" - Full administrative permissions
    """
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # Assigned to new users
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)   # Cannot be deleted
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    
    # Relationships
    permissions: Mapped[List[Permission]] = relationship(
        "Permission", 
        secondary=role_permissions, 
        back_populates="roles"
    )
    users: Mapped[List["User"]] = relationship(
        "User", 
        secondary=user_roles, 
        back_populates="roles",
        primaryjoin="Role.id == user_roles.c.role_id",
        secondaryjoin="User.id == user_roles.c.user_id"
    )
    
    def has_permission(self, resource: str, action: str) -> bool:
        """Check if this role has a specific permission."""
        for permission in self.permissions:
            if permission.resource == resource and (permission.action == action or permission.action == "all"):
                return True
            # Check for wildcard permissions
            if permission.resource == "admin" and permission.action == "all":
                return True
        return False
    
    def __str__(self) -> str:
        return self.name
