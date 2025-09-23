from datetime import datetime, timezone
from typing import List
from sqlalchemy import String, DateTime, Boolean, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base

# Import RBAC models to register them with Base
from .rbac_models import Role, Permission, user_roles, role_permissions

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Profile fields
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    
    # User preferences stored as JSON
    preferences: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=dict)
    
    # Timestamps
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
    
    # RBAC Relationships  
    roles: Mapped[List["Role"]] = relationship(
        "Role", 
        secondary=user_roles, 
        back_populates="users",
        primaryjoin="User.id == user_roles.c.user_id",
        secondaryjoin="Role.id == user_roles.c.role_id",
        lazy="selectin"
    )
    
    def has_permission(self, resource: str, action: str) -> bool:
        """Check if user has a specific permission through their roles."""
        for role in self.roles:
            if role.has_permission(resource, action):
                return True
        return False
    
    def has_role(self, role_name: str) -> bool:
        """Check if user has a specific role."""
        return any(role.name == role_name for role in self.roles)
    
    @property
    def is_admin(self) -> bool:
        """Check if user has admin role or admin permissions."""
        return self.is_superuser or self.has_role("admin") or self.has_permission("admin", "all")