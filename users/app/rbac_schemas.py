"""
RBAC Pydantic Schemas

This module defines the Pydantic schemas for RBAC API endpoints.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

# Permission schemas
class PermissionBase(BaseModel):
    name: str = Field(..., max_length=100, description="Permission name (e.g., 'user:read')")
    description: Optional[str] = Field(None, max_length=500)
    resource: str = Field(..., max_length=50, description="Resource type (e.g., 'user', 'admin')")
    action: str = Field(..., max_length=50, description="Action type (e.g., 'read', 'write', 'all')")

class PermissionCreate(PermissionBase):
    pass

class PermissionRead(PermissionBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Role schemas
class RoleBase(BaseModel):
    name: str = Field(..., max_length=50, description="Role name (e.g., 'admin', 'user')")
    description: Optional[str] = Field(None, max_length=500)
    is_default: bool = Field(False, description="Assign to new users by default")

class RoleCreate(RoleBase):
    permission_ids: List[int] = Field(default_factory=list, description="List of permission IDs")

class RoleUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=500)
    is_default: Optional[bool] = None
    permission_ids: Optional[List[int]] = None

class RoleRead(RoleBase):
    id: int
    is_system: bool
    created_at: datetime
    updated_at: datetime
    permissions: List[PermissionRead] = []

    class Config:
        from_attributes = True

# User role assignment schemas
class UserRoleAssignment(BaseModel):
    user_id: int
    role_ids: List[int] = Field(..., description="List of role IDs to assign")

class UserRoleResponse(BaseModel):
    user_id: int
    roles: List[RoleRead]
    message: str

# Permission check schemas
class PermissionCheck(BaseModel):
    resource: str = Field(..., description="Resource to check (e.g., 'user', 'admin')")
    action: str = Field(..., description="Action to check (e.g., 'read', 'write')")

class PermissionCheckResponse(BaseModel):
    has_permission: bool
    user_id: int
    resource: str
    action: str
    granted_by_roles: List[str] = Field(default_factory=list)

# Extended user schemas with RBAC
class UserWithRoles(BaseModel):
    id: int
    email: str
    username: str
    is_active: bool
    is_superuser: bool
    roles: List[RoleRead] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
