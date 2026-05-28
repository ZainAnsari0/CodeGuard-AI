"""
CodeGuard AI - Scanner Schemas
Pydantic models for scan upload, status, and results.
"""

from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field


class ScanUploadResponse(BaseModel):
    scan_id: str
    filename: str
    file_count: int = 1
    status: str = "pending"
    message: str = "Scan uploaded successfully"


class ScanStatusResponse(BaseModel):
    scan_id: str
    status: str = Field(description="pending, parsing, analyzing, completed, or failed")
    progress: float = 0.0
    stage: Optional[str] = None
    total_files: int = 0
    files_scanned: int = 0
    findings_count: int = 0
    error: Optional[str] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class FixSuggestionResponse(BaseModel):
    id: str
    title: str = ""
    description: str = ""
    priority: int = 0
    code_before: Optional[str] = None
    code_after: Optional[str] = None
    language: str = ""


class FindingResponse(BaseModel):
    id: str
    vulnerability_type: str
    severity: str
    title: str = ""
    description: Optional[str] = None
    analyzer_type: str = "sast"
    cwe_id: Optional[str] = None
    cvss_score: Optional[str] = None
    file_path: str
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    code_snippet: Optional[str] = None
    status: str = "new"
    confidence: Optional[float] = None
    fix_suggestions: List[FixSuggestionResponse] = []


class ScanResultResponse(BaseModel):
    scan_id: str
    status: str
    total_files: int = 0
    findings: List[FindingResponse] = []
    code_files: Dict[str, str] = Field(default_factory=dict, description="file_path -> file_content")
    summary: Optional[dict] = None