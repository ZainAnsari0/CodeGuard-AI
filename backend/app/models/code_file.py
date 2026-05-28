"""
CodeGuard AI - CodeFile Model
Database model for code file storage.
"""

from typing import Optional, List
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import String, DateTime, func, Text, Integer, JSON, ForeignKey
import uuid


class CodeFileBase(SQLModel):
    """Base code file model with common fields."""
    project_id: Optional[str] = Field(
        default=None,
        sa_column=Column(
            String(36),
            ForeignKey("projects.id"),
            nullable=True,
            index=True
        ),
        description="Project ID"
    )
    file_path: str = Field(
        sa_column=Column(String, nullable=False),
        description="File path relative to project root"
    )
    file_name: str = Field(
        sa_column=Column(String, nullable=False),
        description="File name"
    )
    file_extension: str = Field(
        sa_column=Column(String, nullable=False),
        description="File extension (e.g., .py, .js)"
    )
    file_size: int = Field(
        default=0,
        sa_column=Column(Integer, default=0),
        description="File size in bytes"
    )
    content: Optional[str] = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
        description="File content"
    )
    language: Optional[str] = Field(
        default=None,
        sa_column=Column(String, nullable=True),
        description="Detected programming language"
    )
    line_count: int = Field(
        default=0,
        sa_column=Column(Integer, default=0),
        description="Number of lines"
    )
    last_commit_hash: Optional[str] = Field(
        default=None,
        sa_column=Column(String, nullable=True),
        description="Last commit hash"
    )
    last_commit_date: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime, nullable=True),
        description="Last commit date"
    )
    file_metadata: Optional[dict] = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
        description="File metadata"
    )


class CodeFile(CodeFileBase, table=True):
    """CodeFile database model."""
    __tablename__ = "code_files"

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
    project: "Project" = Relationship(
        back_populates="code_files"
    )
    findings: List["Finding"] = Relationship(
        back_populates="code_file",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class CodeFileCreate(SQLModel):
    """Schema for code file creation."""
    project_id: Optional[uuid.UUID] = None
    file_path: str
    file_name: str
    file_extension: str
    content: Optional[str] = None
    language: Optional[str] = None
    line_count: int = 0
    last_commit_hash: Optional[str] = None
    last_commit_date: Optional[datetime] = None
    file_metadata: Optional[dict] = None


class CodeFileUpdate(SQLModel):
    """Schema for code file updates."""
    content: Optional[str] = None
    file_size: Optional[int] = None
    language: Optional[str] = None
    line_count: Optional[int] = None
    last_commit_hash: Optional[str] = None
    last_commit_date: Optional[datetime] = None
    file_metadata: Optional[dict] = None


class CodeFileResponse(SQLModel):
    """Schema for code file response."""
    id: uuid.UUID
    project_id: uuid.UUID
    file_path: str
    file_name: str
    file_extension: str
    file_size: int
    language: Optional[str] = None
    line_count: int
    last_commit_hash: Optional[str] = None
    last_commit_date: Optional[datetime] = None
    file_metadata: Optional[dict] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None