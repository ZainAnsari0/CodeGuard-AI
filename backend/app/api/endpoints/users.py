"""
CodeGuard AI - Users API Endpoints
User management with admin-only access for list/update/deactivate.
"""

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.session import get_session
from app.db.base import ResponseSchema, PaginatedResponse
from app.models.user import User
from app.schemas.auth import UserRole, UserUpdate
from app.api.dependencies import get_current_user, require_role
from app.core.exceptions import NotFoundException
from app.services.auth import get_password_hash

router = APIRouter()


def _user_dict(u: User) -> dict:
    return {
        "id": str(u.id),
        "email": u.email,
        "full_name": u.full_name,
        "role": u.role,
        "is_active": u.is_active,
        "last_login": u.last_login.isoformat() if u.last_login else None,
        "created_at": u.created_at.isoformat() if u.created_at else None,
        "updated_at": u.updated_at.isoformat() if u.updated_at else None,
    }


@router.get("/me", response_model=ResponseSchema)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get current user profile (convenience endpoint)."""
    return ResponseSchema(message="Profile retrieved", data=_user_dict(current_user))


@router.get("/", response_model=PaginatedResponse)
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_session),
) -> Any:
    """List all users (admin only)."""
    count_stmt = select(func.count()).select_from(User)
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = select(User).order_by(User.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    users = result.scalars().all()

    return PaginatedResponse(
        message="Users retrieved",
        data=[_user_dict(u) for u in users],
        pagination={"total": total, "page": skip // limit + 1, "page_size": limit, "total_pages": (total + limit - 1) // limit},
    )


@router.get("/{user_id}", response_model=ResponseSchema)
async def get_user(
    user_id: str,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_session),
) -> Any:
    """Get a user by ID (admin only)."""
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise NotFoundException(message="User not found")

    return ResponseSchema(message="User retrieved", data=_user_dict(user))


@router.patch("/{user_id}", response_model=ResponseSchema)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_session),
) -> Any:
    """Update a user (admin only)."""
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise NotFoundException(message="User not found")

    update_data = user_data.model_dump(exclude_unset=True)
    if "password" in update_data and update_data["password"]:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))

    allowed_fields = {"full_name", "hashed_password", "role", "is_active"}
    for field, value in update_data.items():
        if field in allowed_fields:
            setattr(user, field, value)

    await db.commit()
    await db.refresh(user)

    return ResponseSchema(message="User updated", data=_user_dict(user))


@router.delete("/{user_id}", response_model=ResponseSchema)
async def deactivate_user(
    user_id: str,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_session),
) -> Any:
    """Deactivate a user (admin only). Sets is_active=False instead of deleting."""
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise NotFoundException(message="User not found")

    user.is_active = False
    await db.commit()

    return ResponseSchema(message="User deactivated", data=_user_dict(user))