"""
CodeGuard AI - Class & Enrollment Models
Instructor class management and student enrollment.
"""

from typing import Optional, List
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import String, DateTime, Boolean, Text, Integer, ForeignKey, func
import uuid
import secrets


class Class_(SQLModel, table=True):
    """Instructor class for managing student groups."""
    __tablename__ = "classes"

    id: Optional[str] = Field(
        default_factory=lambda: str(uuid.uuid4()),
        sa_column=Column(String(36), primary_key=True, index=True, nullable=False),
    )
    name: str = Field(
        sa_column=Column(String(255), nullable=False),
        description="Class name",
    )
    description: Optional[str] = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
        description="Class description",
    )
    instructor_id: str = Field(
        sa_column=Column(String(36), ForeignKey("users.id"), nullable=False, index=True),
        description="Instructor user ID",
    )
    join_code: str = Field(
        default_factory=lambda: secrets.token_urlsafe(8),
        sa_column=Column(String(16), unique=True, nullable=False, index=True),
        description="Student join code",
    )
    is_active: bool = Field(
        default=True,
        sa_column=Column(Boolean, default=True),
        description="Whether the class is active",
    )
    created_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime, server_default=func.now()),
    )
    updated_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime, onupdate=func.now()),
    )

    # Relationships
    enrollments: List["Enrollment"] = Relationship(
        back_populates="class_",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class Enrollment(SQLModel, table=True):
    """Student enrollment in a class."""
    __tablename__ = "enrollments"

    id: Optional[str] = Field(
        default_factory=lambda: str(uuid.uuid4()),
        sa_column=Column(String(36), primary_key=True, index=True, nullable=False),
    )
    class_id: str = Field(
        sa_column=Column(String(36), ForeignKey("classes.id"), nullable=False, index=True),
        description="Class ID",
    )
    student_id: str = Field(
        sa_column=Column(String(36), ForeignKey("users.id"), nullable=False, index=True),
        description="Student user ID",
    )
    status: str = Field(
        default="active",
        sa_column=Column(String(20), default="active"),
        description="Enrollment status: active, dropped",
    )
    enrolled_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime, server_default=func.now()),
    )

    # Relationships
    class_: Class_ = Relationship(back_populates="enrollments")