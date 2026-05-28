"""
CodeGuard AI - Code File Schemas
Pydantic schemas for code file management.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class CodeFileBase(BaseModel):
    """Base code file schema with common fields."""
    project_id: Optional[str] = Field(
        default=None,
        description="Project ID"
    )
    file_path: str = Field(
        ...,
        description="File path relative to project root"
    )
    file_name: str = Field(
        ...,
        description="File name"
    )
    file_extension: str = Field(
        ...,
        description="File extension (e.g., .py, .js)"
    )
    content: Optional[str] = Field(
        default=None,
        description="File content"
    )
    language: Optional[str] = Field(
        default=None,
        description="Detected programming language"
    )
    line_count: int = Field(
        default=0,
        description="Number of lines"
    )
    last_commit_hash: Optional[str] = Field(
        default=None,
        description="Last commit hash"
    )
    last_commit_date: Optional[datetime] = Field(
        default=None,
        description="Last commit date"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="File metadata"
    )


class CodeFileCreate(CodeFileBase):
    """Schema for code file creation."""
    pass


class CodeFileUpdate(BaseModel):
    """Schema for code file updates."""
    content: Optional[str] = Field(
        default=None,
        description="File content"
    )
    language: Optional[str] = Field(
        default=None,
        description="Detected programming language"
    )
    line_count: Optional[int] = Field(
        default=None,
        description="Number of lines"
    )
    last_commit_hash: Optional[str] = Field(
        default=None,
        description="Last commit hash"
    )
    last_commit_date: Optional[datetime] = Field(
        default=None,
        description="Last commit date"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="File metadata"
    )


class CodeFileResponse(CodeFileBase):
    """Schema for code file response."""
    id: str
    file_size: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None