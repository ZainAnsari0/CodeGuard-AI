"""
CodeGuard AI - Instructor Schemas
Pydantic schemas for class management and enrollment.
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


# --- Class Schemas ---

class ClassCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Class name")
    description: Optional[str] = Field(None, max_length=2000, description="Class description")


class ClassUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ClassResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    instructor_id: str
    join_code: str
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    student_count: int = 0


# --- Enrollment Schemas ---

class EnrollmentCreate(BaseModel):
    join_code: str = Field(..., min_length=1, description="Class join code")


class JoinByCodeRequest(BaseModel):
    join_code: str = Field(..., min_length=1, description="Class join code")


class EnrolledClassResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    join_code: str
    is_active: bool
    instructor_name: Optional[str] = None
    instructor_email: Optional[str] = None
    enrolled_at: Optional[datetime] = None
    student_count: int = 0


class EnrollmentResponse(BaseModel):
    id: str
    class_id: str
    student_id: str
    status: str
    enrolled_at: Optional[datetime] = None
    student_name: Optional[str] = None
    student_email: Optional[str] = None


# --- Metrics Schemas ---

class ClassMetricsResponse(BaseModel):
    class_id: str
    class_name: str
    total_students: int
    total_scans: int
    total_findings: int
    findings_by_severity: dict
    findings_by_type: dict
    avg_findings_per_student: float
    top_vulnerability_types: List[dict]