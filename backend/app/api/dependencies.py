"""
CodeGuard AI - Shared API Dependencies
Authentication, authorization, and common request dependencies.
Supports token from Authorization header or httpOnly cookies.
"""

from typing import List, Optional

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.user import User
from app.schemas.auth import UserRole
from app.core.exceptions import UnauthorizedException, ForbiddenException
from app.services.auth import validate_token


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


async def get_current_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_session)
) -> User:
    """Get current authenticated user from token.

    Checks Authorization header first, then httpOnly cookies.
    """
    # Try Authorization header first
    if not token:
        # Fall back to httpOnly cookie
        token = request.cookies.get("access_token")

    if not token:
        raise UnauthorizedException(message="Not authenticated")

    return await validate_token(token, db)


def require_role(allowed_roles: List[str]):
    """Dependency factory that restricts access to specified roles."""
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise ForbiddenException(
                message=f"Access denied. Required role: {', '.join(allowed_roles)}"
            )
        return current_user
    return role_checker


def check_analysis_ownership(analysis_metadata: Optional[dict], current_user: User, *, owner_id: Optional[str] = None) -> bool:
    """Check if the current user owns the analysis or is an admin.

    Returns True if the user is the owner or an admin, raises ForbiddenException otherwise.
    Falls back to owner_id when metadata is missing the uploaded_by field.
    """
    if current_user.role == UserRole.ADMIN:
        return True

    uploaded_by = analysis_metadata.get("uploaded_by") if analysis_metadata else None
    effective_owner = uploaded_by or owner_id

    if not effective_owner:
        # No ownership info available — deny access rather than grant it
        raise ForbiddenException(message="Not authorized to access this resource")

    if str(effective_owner) != str(current_user.id):
        raise ForbiddenException(message="Not authorized to access this resource")

    return True