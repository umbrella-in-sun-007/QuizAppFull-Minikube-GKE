"""
RBAC Setup and Initialization

This script creates default roles and permissions for the application.
Run this after database migrations to set up the RBAC system.
"""

import asyncio
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db import get_session
from app.rbac_models import Role, Permission, role_permissions
from app.models import User


async def create_default_permissions(session: AsyncSession) -> Dict[str, Permission]:
    """Create default permissions if they don't exist."""
    
    default_permissions = [
        # User permissions
        {"name": "user:read", "description": "Read user information", "resource": "user", "action": "read"},
        {"name": "user:write", "description": "Modify user information", "resource": "user", "action": "write"},
        {"name": "user:delete", "description": "Delete users", "resource": "user", "action": "delete"},
        
        # Profile permissions
        {"name": "profile:read", "description": "Read user profiles", "resource": "profile", "action": "read"},
        {"name": "profile:write", "description": "Modify user profiles", "resource": "profile", "action": "write"},
        
        # Admin permissions
        {"name": "admin:all", "description": "Full administrative access", "resource": "admin", "action": "all"},
        {"name": "rbac:manage", "description": "Manage roles and permissions", "resource": "rbac", "action": "manage"},
        
        # Moderator permissions
        {"name": "content:moderate", "description": "Moderate user content", "resource": "content", "action": "moderate"},
        {"name": "user:suspend", "description": "Suspend user accounts", "resource": "user", "action": "suspend"},
    ]
    
    created_permissions = {}
    
    for perm_data in default_permissions:
        # Check if permission already exists
        existing = await session.scalar(
            select(Permission).where(Permission.name == perm_data["name"])
        )
        
        if not existing:
            permission = Permission(**perm_data)
            session.add(permission)
            await session.flush()
            created_permissions[perm_data["name"]] = permission
        else:
            created_permissions[perm_data["name"]] = existing
    
    return created_permissions


async def create_default_roles(session: AsyncSession, permissions: Dict[str, Permission]) -> Dict[str, Role]:
    """Create default roles if they don't exist."""
    
    default_roles = [
        {
            "name": "user",
            "description": "Basic user role with standard permissions",
            "is_default": True,
            "is_system": True,
            "permissions": ["profile:read", "profile:write"]
        },
        {
            "name": "moderator", 
            "description": "Moderator role with content management permissions",
            "is_default": False,
            "is_system": True,
            "permissions": ["user:read", "profile:read", "content:moderate", "user:suspend"]
        },
        {
            "name": "admin",
            "description": "Administrator role with full system access",
            "is_default": False,
            "is_system": True,
            "permissions": ["admin:all", "rbac:manage"]
        }
    ]
    
    created_roles = {}
    
    for role_data in default_roles:
        # Check if role already exists
        existing = await session.scalar(
            select(Role).where(Role.name == role_data["name"])
        )
        
        if not existing:
            # Create role without permissions first
            role_perms = role_data.pop("permissions")
            role_name = role_data["name"]  # Store the name before creating
            role = Role(**role_data)
            session.add(role)
            await session.flush()
            
            # Add permissions to role
            if role_perms:
                permissions_to_add = await session.execute(
                    select(Permission).where(Permission.name.in_(role_perms))
                )
                role.permissions = list(permissions_to_add.scalars().all())
                await session.flush()
            
            created_roles[role_name] = role
        else:
            created_roles[role_data["name"]] = existing
    
    return created_roles


async def assign_default_role_to_existing_users(session: AsyncSession, default_role: Role):
    """Assign default role to existing users who don't have any roles."""
    
    # Get all users
    result = await session.execute(select(User))
    users = result.scalars().all()
    
    assigned_count = 0
    for user in users:
        # Load user's roles
        await session.refresh(user, ["roles"])
        
        # If user has no roles, assign default role
        if not user.roles:
            user.roles = [default_role]
            assigned_count += 1
    
    if assigned_count > 0:
        await session.flush()
    
    return assigned_count


async def setup_rbac():
    """Main setup function to initialize RBAC system."""
    
    print("🔧 Setting up RBAC system...")
    
    async with get_session() as session:
        try:
            # Create default permissions
            print("📋 Creating default permissions...")
            permissions = await create_default_permissions(session)
            print(f"✅ Created/verified {len(permissions)} permissions")
            
            # Create default roles
            print("👥 Creating default roles...")
            roles = await create_default_roles(session, permissions)
            print(f"✅ Created/verified {len(roles)} roles")
            
            # Assign default role to existing users
            if "user" in roles:
                print("🔗 Assigning default role to existing users...")
                assigned_count = await assign_default_role_to_existing_users(session, roles["user"])
                print(f"✅ Assigned default role to {assigned_count} users")
            
            # Commit all changes
            await session.commit()
            print("🎉 RBAC setup completed successfully!")
            
            # Print summary
            print("\n📊 RBAC System Summary:")
            print(f"  Permissions: {len(permissions)}")
            print(f"  Roles: {len(roles)}")
            print("\n🔑 Default Roles:")
            for role_name, role in roles.items():
                print(f"  - {role_name}: {role.description}")
                print(f"    Default: {role.is_default}, System: {role.is_system}")
                if hasattr(role, 'permissions'):
                    perm_names = [p.name for p in role.permissions]
                    print(f"    Permissions: {', '.join(perm_names)}")
                print()
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Error setting up RBAC: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(setup_rbac())
