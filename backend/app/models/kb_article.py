"""
CodeGuard AI - Knowledge Base Article Model
Educational content about vulnerabilities.
"""

from typing import Optional, List
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import String, DateTime, Text, Boolean, Integer, ForeignKey, func
import uuid


class KBArticle(SQLModel, table=True):
    """Knowledge base article about security vulnerabilities."""
    __tablename__ = "kb_articles"

    id: Optional[str] = Field(
        default_factory=lambda: str(uuid.uuid4()),
        sa_column=Column(String(36), primary_key=True, index=True, nullable=False),
    )
    slug: str = Field(
        sa_column=Column(String(100), unique=True, nullable=False, index=True),
        description="URL-friendly slug",
    )
    title: str = Field(
        sa_column=Column(String(255), nullable=False),
        description="Article title",
    )
    category: str = Field(
        default="general",
        sa_column=Column(String(50), default="general"),
        description="Article category",
    )
    cwe_ids: Optional[str] = Field(
        default=None,
        sa_column=Column(String(200), nullable=True),
        description="Comma-separated CWE IDs",
    )
    owasp_category: Optional[str] = Field(
        default=None,
        sa_column=Column(String(50), nullable=True),
        description="OWASP category",
    )
    content_markdown: str = Field(
        sa_column=Column(Text, nullable=False),
        description="Article content in markdown",
    )
    vulnerable_example: Optional[str] = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
        description="Vulnerable code example",
    )
    safe_example: Optional[str] = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
        description="Safe/fixed code example",
    )
    is_published: bool = Field(
        default=True,
        sa_column=Column(Boolean, default=True),
        description="Whether the article is published",
    )
    view_count: int = Field(
        default=0,
        sa_column=Column(Integer, default=0),
        description="Number of views",
    )
    created_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime, server_default=func.now()),
    )
    updated_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime, onupdate=func.now()),
    )