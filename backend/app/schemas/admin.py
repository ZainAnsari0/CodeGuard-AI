"""
CodeGuard AI - Admin Schemas
Pydantic schemas for admin user management and system monitoring.
"""

from typing import Optional, List, Literal
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr


# --- Admin User Management ---

class AdminUserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    role: str
    is_active: bool
    last_login: Optional[datetime] = None
    created_at: Optional[datetime] = None


class AdminUserUpdate(BaseModel):
    role: Optional[Literal["developer", "instructor", "admin"]] = Field(None, description="New role: developer, instructor, admin")
    is_active: Optional[bool] = Field(None, description="Activate or deactivate user")
    full_name: Optional[str] = None


class AdminUserListResponse(BaseModel):
    users: List[AdminUserResponse]
    total: int
    page: int
    per_page: int


# --- System Health ---

class ServiceStatus(BaseModel):
    name: str
    status: str
    latency_ms: Optional[float] = None
    details: Optional[str] = None


class SystemHealthResponse(BaseModel):
    status: str
    uptime_seconds: float
    services: List[ServiceStatus]
    version: str


# --- Event Logs ---

class EventLogResponse(BaseModel):
    id: str
    event_type: str
    severity: str
    user_id: Optional[str] = None
    message: str
    metadata: Optional[dict] = None
    created_at: Optional[datetime] = None


class EventLogListResponse(BaseModel):
    events: List[EventLogResponse]
    total: int
    page: int
    per_page: int