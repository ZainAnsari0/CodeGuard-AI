"""
CodeGuard AI - Share Token Model
Tokens for sharing scan reports publicly without authentication.
"""

from typing import Optional
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import String, DateTime, Boolean, Integer, ForeignKey, func
import uuid
import secrets


class ShareToken(SQLModel, table=True):
    """Shareable link token for report access."""
    __tablename__ = "share_tokens"

    id: Optional[str] = Field(
        default_factory=lambda: str(uuid.uuid4()),
        sa_column=Column(String(36), primary_key=True, index=True, nullable=False),
    )
    token: str = Field(
        default_factory=lambda: secrets.token_urlsafe(24),
        sa_column=Column(String(64), unique=True, nullable=False, index=True),
        description="Unique shareable URL token",
    )
    analysis_id: str = Field(
        sa_column=Column(String(36), ForeignKey("analyses.id"), nullable=False, index=True),
        description="Analysis ID being shared",
    )
    created_by: str = Field(
        sa_column=Column(String(36), ForeignKey("users.id"), nullable=False, index=True),
        description="User who created the share link",
    )
    expires_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
        description="Optional expiry time",
    )
    is_revoked: bool = Field(
        default=False,
        sa_column=Column(Boolean, default=False),
        description="Whether the share link has been revoked",
    )
    view_count: int = Field(
        default=0,
        sa_column=Column(Integer, default=0),
        description="Number of times the shared link has been viewed",
    )
    created_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )