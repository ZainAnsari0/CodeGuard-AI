"""
CodeGuard AI - System Event Model
Audit logging for admin visibility.
"""

from typing import Optional, Dict, Any
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import String, DateTime, Text, JSON, ForeignKey, func
import uuid


class SystemEvent(SQLModel, table=True):
    """System event for audit logging."""
    __tablename__ = "system_events"

    id: Optional[str] = Field(
        default_factory=lambda: str(uuid.uuid4()),
        sa_column=Column(String(36), primary_key=True, index=True, nullable=False),
    )
    event_type: str = Field(
        sa_column=Column(String(50), nullable=False, index=True),
        description="Event type (e.g., user_login, scan_completed, error)",
    )
    severity: str = Field(
        default="info",
        sa_column=Column(String(10), default="info"),
        description="Event severity: info, warning, error, critical",
    )
    user_id: Optional[str] = Field(
        default=None,
        sa_column=Column(String(36), ForeignKey("users.id"), nullable=True, index=True),
        description="User ID associated with the event",
    )
    message: str = Field(
        sa_column=Column(Text, nullable=False),
        description="Event message",
    )
    metadata_: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column("metadata", JSON, nullable=True),
        description="Additional event metadata",
    )
    created_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime, server_default=func.now()),
    )