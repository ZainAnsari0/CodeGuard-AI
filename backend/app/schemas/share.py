"""
CodeGuard AI - Share Token Schemas
Pydantic schemas for report sharing.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ShareCreate(BaseModel):
    analysis_id: str = Field(..., description="Analysis ID to share")
    expires_in_hours: Optional[int] = Field(None, description="Hours until link expires (None = never)")


class ShareResponse(BaseModel):
    id: str
    token: str
    share_url: str
    analysis_id: str
    expires_at: Optional[datetime] = None
    view_count: int = 0
    created_at: Optional[datetime] = None


class ShareListResponse(BaseModel):
    shares: list[ShareResponse]
    total: int