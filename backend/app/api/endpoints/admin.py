"""
CodeGuard AI - Admin API Endpoints
User management, system health, and event logs.
"""

import uuid
import logging
import asyncio
import time as time_module
from typing import Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.user import User
from app.models.analysis import Analysis
from app.models.system_event import SystemEvent
from app.schemas.admin import (
    AdminUserResponse, AdminUserUpdate, AdminUserListResponse,
    ServiceStatus, SystemHealthResponse,
    EventLogResponse, EventLogListResponse,
)
from app.api.dependencies import get_current_user, require_role
from app.schemas.auth import UserRole
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

_start_time = time_module.time()


# --- User Management ---

@router.get("/users", response_model=dict)
async def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    role: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role([UserRole.ADMIN])),
):
    """List all users with optional filtering."""
    query = select(User)
    count_query = select(func.count()).select_from(User)

    if role:
        query = query.where(User.role == role)
        count_query = count_query.where(User.role == role)
    if search:
        escaped = search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        search_filter = User.email.ilike(f"%{escaped}%", escape="\\") | User.full_name.ilike(f"%{escaped}%", escape="\\")
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    offset = (page - 1) * per_page
    result = await db.execute(query.order_by(User.created_at.desc()).offset(offset).limit(per_page))
    users = result.scalars().all()

    user_list = [
        AdminUserResponse(
            id=u.id, email=u.email, full_name=u.full_name,
            role=u.role, is_active=u.is_active,
            last_login=u.last_login, created_at=u.created_at,
        ).model_dump()
        for u in users
    ]

    return {
        "success": True,
        "data": AdminUserListResponse(
            users=user_list, total=total, page=page, per_page=per_page,
        ).model_dump(),
    }


@router.patch("/users/{user_id}", response_model=dict)
async def update_user(
    user_id: str,
    data: AdminUserUpdate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role([UserRole.ADMIN])),
):
    """Update a user's role or active status (admin only)."""
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if data.role is not None:
        valid_roles = [UserRole.DEVELOPER, UserRole.INSTRUCTOR, UserRole.ADMIN]
        if data.role not in valid_roles:
            raise HTTPException(status_code=400, detail=f"Invalid role. Must be: {', '.join(valid_roles)}")
        user.role = data.role
    if data.is_active is not None:
        user.is_active = data.is_active
    if data.full_name is not None:
        user.full_name = data.full_name

    await db.commit()
    await db.refresh(user)

    # Log the event
    event = SystemEvent(
        id=str(uuid.uuid4()),
        event_type="user_updated",
        severity="info",
        user_id=current_user.id,
        message=f"Admin updated user {user.id}: role={user.role}, is_active={user.is_active}",
        metadata={"target_user_id": user.id, "changes": data.model_dump()},
    )
    db.add(event)
    await db.commit()

    return {
        "success": True,
        "message": "User updated",
        "data": AdminUserResponse(
            id=user.id, email=user.email, full_name=user.full_name,
            role=user.role, is_active=user.is_active,
            last_login=user.last_login, created_at=user.created_at,
        ).model_dump(),
    }


@router.delete("/users/{user_id}", response_model=dict)
async def deactivate_user(
    user_id: str,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role([UserRole.ADMIN])),
):
    """Deactivate a user account (soft delete)."""
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")

    user.is_active = False
    await db.commit()

    event = SystemEvent(
        id=str(uuid.uuid4()),
        event_type="user_deactivated",
        severity="warning",
        user_id=current_user.id,
        message=f"Admin deactivated user {user.id}",
        metadata={"target_user_id": user.id},
    )
    db.add(event)
    await db.commit()

    return {"success": True, "message": "User deactivated"}


# --- System Health ---

@router.get("/system/health", response_model=dict)
async def system_health(
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role([UserRole.ADMIN])),
):
    """Get system health status."""
    services = []
    overall_status = "healthy"

    async def _check_db():
        try:
            await db.execute(select(1))
            return ServiceStatus(name="database", status="healthy", latency_ms=0).model_dump()
        except Exception as e:
            return ServiceStatus(name="database", status="unhealthy", details=str(e)[:100]).model_dump()

    async def _check_redis():
        try:
            from app.services.cache import prompt_cache
            await prompt_cache.set("health", "check", "default", {"ok": True})
            result = await prompt_cache.get("health", "check", "default")
            if result:
                return ServiceStatus(name="redis", status="healthy", latency_ms=0).model_dump()
            return ServiceStatus(name="redis", status="degraded", details="Cache miss").model_dump()
        except Exception as e:
            return ServiceStatus(name="redis", status="unhealthy", details=str(e)[:100]).model_dump()

    async def _check_ai():
        try:
            from app.ai.fallback_chain import ai_chain
            provider_status = ai_chain.get_provider_status()
            return [
                ServiceStatus(name=f"ai_{name}", status="healthy" if available else "unavailable").model_dump()
                for name, available in provider_status.items()
            ]
        except Exception:
            return [ServiceStatus(name="ai_pipeline", status="unknown").model_dump()]

    # Run all health checks in parallel
    db_result, redis_result, ai_result = await asyncio.gather(
        _check_db(), _check_redis(), _check_ai(),
    )

    services.append(db_result)
    services.append(redis_result)
    services.extend(ai_result if isinstance(ai_result, list) else [ai_result])

    # Determine overall status from individual checks
    for svc in services:
        if svc.get("status") in ("unhealthy", "degraded"):
            overall_status = "degraded"
            break

    # Count users and scans
    user_count = await db.execute(select(func.count()).select_from(User))
    scan_count = await db.execute(select(func.count()).select_from(Analysis))

    uptime = time_module.time() - _start_time if '_start_time' in dir() else 0

    return {
        "success": True,
        "data": SystemHealthResponse(
            status=overall_status,
            uptime_seconds=uptime,
            services=services,
            version=settings.PROJECT_VERSION,
        ).model_dump(),
        "stats": {
            "total_users": user_count.scalar() or 0,
            "total_scans": scan_count.scalar() or 0,
        },
    }


# --- Event Logs ---

@router.get("/system/events", response_model=dict)
async def list_events(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    event_type: Optional[str] = None,
    severity: Optional[str] = None,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role([UserRole.ADMIN])),
):
    """List system events with optional filtering."""
    query = select(SystemEvent)
    count_query = select(func.count()).select_from(SystemEvent)

    if event_type:
        query = query.where(SystemEvent.event_type == event_type)
        count_query = count_query.where(SystemEvent.event_type == event_type)
    if severity:
        query = query.where(SystemEvent.severity == severity)
        count_query = count_query.where(SystemEvent.severity == severity)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    offset = (page - 1) * per_page
    result = await db.execute(
        query.order_by(SystemEvent.created_at.desc()).offset(offset).limit(per_page)
    )
    events = result.scalars().all()

    event_list = [
        EventLogResponse(
            id=e.id, event_type=e.event_type, severity=e.severity,
            user_id=e.user_id, message=e.message,
            metadata=e.metadata_, created_at=e.created_at,
        ).model_dump()
        for e in events
    ]

    return {
        "success": True,
        "data": EventLogListResponse(
            events=event_list, total=total, page=page, per_page=per_page,
        ).model_dump(),
    }


@router.get("/system/token-usage", response_model=dict)
async def get_token_usage(
    current_user: User = Depends(require_role([UserRole.ADMIN])),
):
    """Get AI token usage summary (admin only)."""
    from app.ai.fallback_chain import ai_chain

    usage = ai_chain.get_token_usage()
    provider_status = ai_chain.get_provider_status()

    return {
        "success": True,
        "data": {
            "token_usage": usage,
            "provider_status": provider_status,
        },
    }