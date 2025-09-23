from datetime import datetime
from typing import Dict, Any
from pydantic import BaseModel, EmailStr, HttpUrl, Field

# User schemas
class UserBase(BaseModel):
    email: EmailStr
    name: str | None = None
    is_active: bool = True

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")

class UserUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    is_active: bool | None = None

class UserRead(UserBase):
    id: int
    is_superuser: bool
    bio: str | None = None
    avatar_url: str | None = None
    location: str | None = None
    website: str | None = None
    phone: str | None = None
    preferences: Dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Profile-specific schemas
class UserProfileUpdate(BaseModel):
    name: str | None = Field(None, max_length=255)
    bio: str | None = Field(None, max_length=1000)
    avatar_url: str | None = Field(None, max_length=500)
    location: str | None = Field(None, max_length=255)
    website: str | None = Field(None, max_length=500)
    phone: str | None = Field(None, max_length=20, pattern=r'^\+?[\d\s\-\(\)]+$')

class UserPreferencesUpdate(BaseModel):
    theme: str | None = Field(None, pattern=r'^(light|dark|auto)$')
    language: str | None = Field(None, max_length=10)
    timezone: str | None = Field(None, max_length=50)
    notifications_email: bool | None = None
    notifications_sms: bool | None = None
    privacy_public_profile: bool | None = None

class UserProfile(BaseModel):
    id: int
    email: EmailStr
    name: str | None = None
    bio: str | None = None
    avatar_url: str | None = None
    location: str | None = None
    website: str | None = None
    phone: str | None = None
    preferences: Dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Authentication schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: str | None = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str