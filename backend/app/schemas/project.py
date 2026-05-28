"""
CodeGuard AI - Project Schemas
Pydantic schemas for project management.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ProjectBase(BaseModel):
    """Base project schema with common fields."""
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Project name"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Project description"
    )
    repository_url: Optional[str] = Field(
        default=None,
        description="Git repository URL"
    )
    branch: str = Field(
        default="main",
        description="Git branch to scan"
    )
    config: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Project-specific configuration"
    )


class ProjectCreate(ProjectBase):
    """Schema for project creation."""
    pass


class ProjectUpdate(BaseModel):
    """Schema for project updates."""
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Project name"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Project description"
    )
    repository_url: Optional[str] = Field(
        default=None,
        description="Git repository URL"
    )
    branch: Optional[str] = Field(
        default=None,
        description="Git branch to scan"
    )
    config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Project-specific configuration"
    )


class ProjectResponse(ProjectBase):
    """Schema for project response."""
    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None