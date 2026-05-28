"""
CodeGuard AI - Project Model
Database model for project management.
"""

from typing import Optional, List
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import String, DateTime, func, JSON, ForeignKey
import uuid


class ProjectBase(SQLModel):
    """Base project model with common fields."""
    name: str = Field(
        sa_column=Column(String, nullable=False),
        description="Project name"
    )
    description: Optional[str] = Field(
        default=None,
        sa_column=Column(String, nullable=True),
        description="Project description"
    )
    repository_url: Optional[str] = Field(
        default=None,
        sa_column=Column(String, nullable=True),
        description="Git repository URL"
    )
    branch: str = Field(
        default="main",
        sa_column=Column(String, default="main"),
        description="Git branch to scan"
    )
    config: Optional[dict] = Field(
        default_factory=dict,
        sa_column=Column(JSON, nullable=True),
        description="Project-specific configuration"
    )


class Project(ProjectBase, table=True):
    """Project database model."""
    __tablename__ = "projects"
    
    id: Optional[str] = Field(
        default_factory=lambda: str(uuid.uuid4()),
        sa_column=Column(
            String(36),
            primary_key=True,
            index=True,
            nullable=False
        ),
        description="Unique identifier"
    )
    
    user_id: Optional[str] = Field(
        sa_column=Column(
            String(36),
            ForeignKey("users.id"),
            nullable=False,
            index=True
        ),
        description="Owner user ID"
    )
    
    created_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime, server_default=func.now()),
        description="Created timestamp"
    )
    
    updated_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime, onupdate=func.now()),
        description="Updated timestamp"
    )
    
    # Relationships
    user: "User" = Relationship(
        back_populates="projects"
    )
    code_files: List["CodeFile"] = Relationship(
        back_populates="project",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    analyses: List["Analysis"] = Relationship(
        back_populates="project",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class ProjectCreate(SQLModel):
    """Schema for project creation."""
    name: str
    description: Optional[str] = None
    repository_url: Optional[str] = None
    branch: str = "main"
    config: Optional[dict] = None


class ProjectUpdate(SQLModel):
    """Schema for project updates."""
    name: Optional[str] = None
    description: Optional[str] = None
    repository_url: Optional[str] = None
    branch: Optional[str] = None
    config: Optional[dict] = None


class ProjectResponse(SQLModel):
    """Schema for project response."""
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    repository_url: Optional[str] = None
    branch: str
    config: Optional[dict] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None