"""
CodeGuard AI - Authentication Schemas
Pydantic schemas for user authentication and management.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator
import re


class Token(BaseModel):
    """Access token response."""
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Token payload model."""
    sub: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    expires_at: datetime


class UserRole:
    """User role constants."""
    DEVELOPER = "developer"
    INSTRUCTOR = "instructor"
    ADMIN = "admin"


def _validate_password(v: str) -> str:
    """Validate password strength requirements."""
    if len(v) < 8:
        raise ValueError('Password must be at least 8 characters')
    if not any(c.isupper() for c in v):
        raise ValueError('Password must contain at least one uppercase letter')
    if not any(c.islower() for c in v):
        raise ValueError('Password must contain at least one lowercase letter')
    if not any(c.isdigit() for c in v):
        raise ValueError('Password must contain at least one digit')
    if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in v):
        raise ValueError('Password must contain at least one special character')
    return v


class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """Schema for user registration."""
    password: str = Field(
        ...,
        min_length=8,
        description="Password must be at least 8 characters"
    )
    role: str = Field(
        ...,
        description="User role: developer, instructor, or admin"
    )

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        return _validate_password(v)

    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        valid_roles = [UserRole.DEVELOPER, UserRole.INSTRUCTOR, UserRole.ADMIN]
        if v not in valid_roles:
            raise ValueError(f'Role must be one of: {", ".join(valid_roles)}')
        return v


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class UserResponse(UserBase):
    """Schema for user response."""
    id: str
    is_active: bool
    role: str
    last_login: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class UserUpdate(BaseModel):
    """Schema for user updates."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = Field(
        None,
        min_length=8,
        description="Password must be at least 8 characters"
    )
    is_active: Optional[bool] = None
    role: Optional[str] = Field(
        None,
        description="User role: developer, instructor, or admin"
    )

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if v is None:
            return v
        return _validate_password(v)

    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        if v is None:
            return v
        valid_roles = [UserRole.DEVELOPER, UserRole.INSTRUCTOR, UserRole.ADMIN]
        if v not in valid_roles:
            raise ValueError(f'Role must be one of: {", ".join(valid_roles)}')
        return v


class PasswordChangeRequest(BaseModel):
    """Request to change password."""
    current_password: str
    new_password: str = Field(
        ...,
        min_length=8,
        description="New password must be at least 8 characters"
    )

    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v):
        return _validate_password(v)


class PasswordResetRequest(BaseModel):
    """Request to initiate password reset."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Confirm password reset with token."""
    token: str
    new_password: str = Field(
        ...,
        min_length=8,
        description="New password must be at least 8 characters"
    )

    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v):
        return _validate_password(v)


class UserProfile(BaseModel):
    """User profile information."""
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime


class LockoutInfo(BaseModel):
    """Account lockout information."""
    locked: bool
    unlock_time: Optional[datetime] = None
    failed_attempts: int
    lockout_duration_minutes: int = 15