"""
CodeGuard AI - Analysis Schemas
Pydantic schemas for security analysis.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class AnalysisBase(BaseModel):
    """Base analysis schema with common fields."""
    project_id: Optional[str] = Field(
        default=None,
        description="Project ID"
    )
    branch: str = Field(
        ...,
        description="Branch analyzed"
    )
    commit_hash: Optional[str] = Field(
        default=None,
        description="Commit hash analyzed"
    )


class AnalysisCreate(AnalysisBase):
    """Schema for analysis creation."""
    pass


class AnalysisResponse(BaseModel):
    """Schema for analysis response."""
    id: str
    project_id: str
    branch: str
    commit_hash: Optional[str] = None
    status: str = "running"
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    summary: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class AnalysisSummary(BaseModel):
    """Schema for analysis summary."""
    total_files: int = 0
    total_findings: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    info_count: int = 0
    by_severity: Dict[str, int] = Field(default_factory=dict)
    by_type: Dict[str, int] = Field(default_factory=dict)
    by_language: Dict[str, int] = Field(default_factory=dict)