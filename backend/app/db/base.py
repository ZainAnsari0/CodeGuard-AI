"""
CodeGuard AI - Database Base Models
SQLModel base class for ORM models.
"""

from sqlmodel import SQLModel as BaseSQLModel
from typing import Any, Dict, Optional
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Boolean
from pydantic import BaseModel, ConfigDict


class SQLModel(BaseSQLModel):
    """Base class for SQLModel models.

    NOTE: This shadows the name `sqlmodel.SQLModel`. Table models in
    `app.models` import `from sqlmodel import SQLModel` directly, which
    is correct — they share the same metadata for `create_all`.
    """

    __table_args__ = {"extend_existing": True}


def _utcnow():
    return datetime.now(timezone.utc)


class TimestampMixin:
    """Mixin for adding timestamp fields to models."""

    created_at: datetime = Column(
        DateTime,
        default=_utcnow,
    )
    updated_at: datetime = Column(
        DateTime,
        default=_utcnow,
        onupdate=_utcnow,
    )


class AuditMixin:
    """Mixin for adding audit fields to models."""

    created_by: Optional[str] = Column(String, default=None)
    updated_by: Optional[str] = Column(String, default=None)
    deleted_by: Optional[str] = Column(String, default=None)
    is_deleted: bool = Column(Boolean, default=False)


class ResponseSchema(BaseModel):
    """Base response schema."""
    model_config = ConfigDict(from_attributes=True)

    success: bool = True
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None


class PaginatedResponse(BaseModel):
    """Paginated response schema."""
    model_config = ConfigDict(from_attributes=True)

    success: bool = True
    message: Optional[str] = None
    data: Any = None
    pagination: Dict[str, Any] = {
        "total": 0,
        "page": 1,
        "page_size": 10,
        "total_pages": 0,
    }