"""CodeGuard AI - Auth Service (Domain Layer)

Extracted from app/services/auth.py into a DI-ready service class.
Token logic, password hashing, and account lockout remain in auth.py
as infrastructure concerns. This module provides the high-level
business operations for authentication.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.repositories.user import UserRepository
from app.core.exceptions import (
    AuthenticationFailed,
    AccessDenied,
    ValidationFailed,
    DuplicateEntity,
    AccountLocked,
)
from app.schemas.auth import UserRole

logger = logging.getLogger(__name__)


class AuthService:
    """High-level authentication business operations.

    Encapsulates business logic for user authentication, registration,
    and authorization checks. Lower-level token/password operations
    remain in app.services.auth infrastructure module.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Look up a user by email."""
        return await self.user_repo.get_by_email(email)

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Look up a user by ID."""
        return await self.user_repo.get_by_id(user_id)

    async def validate_registration(self, email: str) -> None:
        """Validate that a registration request is allowed.

        Raises:
            DuplicateEntity: If email is already registered.
            ValidationFailed: If email format is invalid.
        """
        existing = await self.user_repo.get_by_email(email)
        if existing:
            raise DuplicateEntity(entity="User", field="email")

    async def validate_ownership(
        self,
        resource_owner_id: Optional[str],
        current_user: User,
        *,
        owner_id: Optional[str] = None,
    ) -> bool:
        """Check if current user owns a resource or is an admin.

        Args:
            resource_owner_id: The owner ID from the resource's metadata.
            current_user: The authenticated user.
            owner_id: Fallback owner ID if metadata is missing.

        Returns:
            True if authorized.

        Raises:
            AccessDenied: If the user doesn't own the resource and isn't admin.
        """
        if current_user.role == UserRole.ADMIN:
            return True

        effective_owner = resource_owner_id or owner_id
        if not effective_owner:
            raise AccessDenied(message="Not authorized to access this resource")

        if str(effective_owner) != str(current_user.id):
            raise AccessDenied(message="Not authorized to access this resource")

        return True

    async def search_users(
        self,
        query: Optional[str] = None,
        role: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list, int]:
        """Search and paginate users. Returns (users, total_count)."""
        offset = (page - 1) * per_page
        return await self.user_repo.search(
            query=query, role=role, offset=offset, limit=per_page
        )

    async def deactivate_user(self, user_id: str, current_user_id: str) -> User:
        """Soft-delete a user by setting is_active=False.

        Raises:
            EntityNotFound: If user doesn't exist.
            BusinessRuleViolation: If trying to deactivate yourself.
        """
        from app.core.exceptions import EntityNotFound, BusinessRuleViolation

        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise EntityNotFound(entity="User", entity_id=user_id)

        if user.id == current_user_id:
            raise BusinessRuleViolation(message="Cannot deactivate yourself")

        user.is_active = False
        await self.db.commit()
        await self.db.refresh(user)
        return user