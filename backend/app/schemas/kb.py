"""
CodeGuard AI - Knowledge Base Schemas
Pydantic schemas for KB article CRUD and search.
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class KBArticleCreate(BaseModel):
    slug: str = Field(..., min_length=1, max_length=100, description="URL-friendly slug")
    title: str = Field(..., min_length=1, max_length=255, description="Article title")
    category: str = Field(default="general", max_length=50)
    cwe_ids: Optional[str] = Field(None, description="Comma-separated CWE IDs")
    owasp_category: Optional[str] = None
    content_markdown: str = Field(..., min_length=1, description="Article content in markdown")
    vulnerable_example: Optional[str] = None
    safe_example: Optional[str] = None
    is_published: bool = True


class KBArticleUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    category: Optional[str] = None
    cwe_ids: Optional[str] = None
    owasp_category: Optional[str] = None
    content_markdown: Optional[str] = None
    vulnerable_example: Optional[str] = None
    safe_example: Optional[str] = None
    is_published: Optional[bool] = None


class KBArticleResponse(BaseModel):
    id: str
    slug: str
    title: str
    category: str
    cwe_ids: Optional[str] = None
    owasp_category: Optional[str] = None
    content_markdown: str
    vulnerable_example: Optional[str] = None
    safe_example: Optional[str] = None
    is_published: bool
    view_count: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class KBArticleSummary(BaseModel):
    """Lightweight article for list views (no full content)."""
    id: str
    slug: str
    title: str
    category: str
    cwe_ids: Optional[str] = None
    owasp_category: Optional[str] = None
    is_published: bool
    view_count: int
    created_at: Optional[datetime] = None


class KBSearchResponse(BaseModel):
    articles: List[KBArticleSummary]
    total: int