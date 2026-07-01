"""
CodeGuard AI - Analysis Models
Database models for security analysis results.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import String, DateTime, func, Text, Enum, Integer, JSON, ForeignKey, Boolean, Float
import uuid
import enum


class Severity(enum.Enum):
    """Security finding severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class FindingBase(SQLModel):
    """Base finding model with common fields."""
    code_file_id: Optional[str] = Field(
        default=None,
        sa_column=Column(
            String(36),
            ForeignKey("code_files.id"),
            nullable=True,
            index=True
        ),
        description="Code file ID"
    )
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
    analysis_id: Optional[str] = Field(
        sa_column=Column(
            String(36),
            ForeignKey("analyses.id"),
            nullable=False,
            index=True
        ),
        description="Analysis ID"
    )
    analyzer_type: str = Field(
        sa_column=Column(String, nullable=False),
        description="Type of analyzer that found this (e.g., 'sast', 'sca', 'dast')"
    )
    vulnerability_type: str = Field(
        sa_column=Column(String, nullable=False),
        description="Type of vulnerability (e.g., 'SQL Injection', 'XSS')"
    )
    severity: Severity = Field(
        sa_column=Column(
            Enum(Severity, values_callable=lambda obj: [e.value for e in obj]),
            nullable=False
        ),
        description="Severity level"
    )
    title: str = Field(
        sa_column=Column(String, nullable=False),
        description="Finding title"
    )
    description: str = Field(
        sa_column=Column(Text, nullable=False),
        description="Detailed description"
    )
    cwe_id: Optional[str] = Field(
        default=None,
        sa_column=Column(String, nullable=True),
        description="CWE ID"
    )
    cvss_score: Optional[float] = Field(
        default=None,
        sa_column=Column(String, nullable=True),
        description="CVSS score"
    )
    cve_id: Optional[str] = Field(
        default=None,
        sa_column=Column(String, nullable=True),
        description="CVE ID"
    )
    file_path: str = Field(
        sa_column=Column(String, nullable=False),
        description="File path"
    )
    line_start: int = Field(
        default=0,
        sa_column=Column(Integer, default=0),
        description="Start line number"
    )
    line_end: int = Field(
        default=0,
        sa_column=Column(Integer, default=0),
        description="End line number"
    )
    column_start: int = Field(
        default=0,
        sa_column=Column(Integer, default=0),
        description="Start column"
    )
    column_end: int = Field(
        default=0,
        sa_column=Column(Integer, default=0),
        description="End column"
    )
    code_snippet: Optional[str] = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
        description="Relevant code snippet"
    )
    status: str = Field(
        default="new",
        sa_column=Column(String, default="new"),
        description="Finding status"
    )
    confidence: int = Field(
        default=100,
        sa_column=Column(Integer, default=100),
        description="Confidence score (0-100)"
    )
    finding_metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
        description="Additional metadata"
    )

    # AI Enrichment fields
    explanation: Optional[str] = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
        description="AI-generated explanation JSON"
    )
    explanation_provider: Optional[str] = Field(
        default=None,
        sa_column=Column(String, nullable=True),
        description="AI provider that generated the explanation"
    )
    explanation_generated_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
        description="When the explanation was generated"
    )


class Finding(FindingBase, table=True):
    """Finding database model."""
    __tablename__ = "findings"

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
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
        description="Created timestamp"
    )

    updated_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), onupdate=func.now()),
        description="Updated timestamp"
    )

    # Relationships
    code_file: "CodeFile" = Relationship(
        back_populates="findings"
    )
    analysis: "Analysis" = Relationship(
        back_populates="findings"
    )
    fix_suggestions: List["FixSuggestion"] = Relationship(
        back_populates="finding",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class FixSuggestionBase(SQLModel):
    """Base fix suggestion model with common fields."""
    finding_id: Optional[str] = Field(
        sa_column=Column(
            String(36),
            ForeignKey("findings.id"),
            nullable=False,
            index=True
        ),
        description="Finding ID"
    )
    title: str = Field(
        sa_column=Column(String, nullable=False),
        description="Suggestion title"
    )
    description: str = Field(
        sa_column=Column(Text, nullable=False),
        description="Detailed description"
    )
    priority: int = Field(
        default=0,
        sa_column=Column(Integer, default=0),
        description="Priority score"
    )
    code_before: Optional[str] = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
        description="Code before fix"
    )
    code_after: Optional[str] = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
        description="Code after fix"
    )
    language: str = Field(
        sa_column=Column(String, nullable=False),
        description="Target programming language"
    )

    # AI Validation fields
    ast_validated: Optional[bool] = Field(
        default=None,
        sa_column=Column(Boolean, nullable=True),
        description="Whether AST validation passed"
    )
    validation_warnings: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
        description="AST validation warnings"
    )
    confidence: Optional[float] = Field(
        default=None,
        sa_column=Column(Float, nullable=True),
        description="AI confidence score for the fix"
    )


class FixSuggestion(FixSuggestionBase, table=True):
    """FixSuggestion database model."""
    __tablename__ = "fix_suggestions"

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
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
        description="Created timestamp"
    )

    updated_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), onupdate=func.now()),
        description="Updated timestamp"
    )

    # Relationships
    finding: "Finding" = Relationship(
        back_populates="fix_suggestions"
    )


class AnalysisBase(SQLModel):
    """Base analysis model with common fields."""
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
    user_id: Optional[str] = Field(
        default=None,
        sa_column=Column(
            String(36),
            ForeignKey("users.id"),
            nullable=True,
            index=True
        ),
        description="User who created the analysis"
    )
    branch: str = Field(
        default="main",
        sa_column=Column(String, default="main", nullable=True),
        description="Branch analyzed"
    )
    scan_name: Optional[str] = Field(
        default=None,
        sa_column=Column(String, nullable=True),
        description="User-friendly name of the scan"
    )
    commit_hash: Optional[str] = Field(
        default=None,
        sa_column=Column(String, nullable=True),
        description="Commit hash analyzed"
    )
    status: str = Field(
        default="running",
        sa_column=Column(String, default="running"),
        description="Analysis status"
    )
    started_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
        description="Analysis start time"
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
        description="Analysis completion time"
    )
    summary: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
        description="Analysis summary"
    )
    analysis_metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
        description="Additional metadata"
    )


class Analysis(AnalysisBase, table=True):
    """Analysis database model."""
    __tablename__ = "analyses"

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
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
        description="Created timestamp"
    )

    updated_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), onupdate=func.now()),
        description="Updated timestamp"
    )

    # Relationships
    project: "Project" = Relationship(
        back_populates="analyses"
    )
    findings: List["Finding"] = Relationship(
        back_populates="analysis"
    )


class AnalysisCreate(SQLModel):
    """Schema for analysis creation."""
    project_id: Optional[uuid.UUID] = None
    branch: str
    commit_hash: Optional[str] = None


class AnalysisResponse(SQLModel):
    """Schema for analysis response."""
    id: uuid.UUID
    project_id: uuid.UUID
    branch: str
    commit_hash: Optional[str] = None
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    summary: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None