"""
CodeGuard AI - User Model
Database model for user management with role support and account lockout.
"""

from typing import Optional, List
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import String, Boolean, Integer, func
from sqlalchemy import DateTime as SACDateTime
import uuid


class User(SQLModel, table=True):
    """User database model."""
    __tablename__ = "users"

    id: Optional[str] = Field(
        default_factory=lambda: str(uuid.uuid4()),
        sa_column=Column(
            String(36),
            primary_key=True,
            index=True,
            nullable=False
        ),
    )
    email: str = Field(
        sa_column=Column(String, nullable=False, unique=True, index=True),
    )
    full_name: Optional[str] = Field(
        default=None,
        sa_column=Column(String, nullable=True),
    )
    hashed_password: str = Field(
        sa_column=Column(String, nullable=False),
    )
    role: str = Field(
        default="developer",
        sa_column=Column(String(20), nullable=False, default="developer"),
    )
    is_active: bool = Field(
        default=True,
        sa_column=Column(Boolean, default=True),
    )
    is_superuser: bool = Field(
        default=False,
        sa_column=Column(Boolean, default=False),
    )

    # Account lockout fields
    failed_login_attempts: int = Field(
        default=0,
        sa_column=Column(Integer, default=0),
    )
    locked_until: Optional[datetime] = Field(
        default=None,
        sa_column=Column(SACDateTime(timezone=True), nullable=True),
    )

    # Password reset fields
    password_reset_token: Optional[str] = Field(
        default=None,
        sa_column=Column(String, nullable=True, unique=True),
    )
    password_reset_expires: Optional[datetime] = Field(
        default=None,
        sa_column=Column(SACDateTime(timezone=True), nullable=True),
    )

    last_login: Optional[datetime] = Field(
        default=None,
        sa_column=Column(SACDateTime(timezone=True), nullable=True),
    )
    created_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(SACDateTime(timezone=True), server_default=func.now()),
    )
    updated_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(SACDateTime(timezone=True), onupdate=func.now()),
    )

    # Relationships
    projects: List["Project"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )