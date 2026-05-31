"""CodeGuard AI - User Repository

Data access layer for User entities.
All database queries related to users live here.
"""

from typing import Optional, List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User entity with domain-specific queries."""

    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Find a user by email address."""
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def search(
        self,
        query: Optional[str] = None,
        role: Optional[str] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[List[User], int]:
        """Search users with filtering and return (users, total_count)."""
        stmt = select(User)
        count_stmt = select(func.count()).select_from(User)

        if role:
            stmt = stmt.where(User.role == role)
            count_stmt = count_stmt.where(User.role == role)

        if query:
            escaped = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            search_filter = (
                User.email.ilike(f"%{escaped}%", escape="\\")
                | User.full_name.ilike(f"%{escaped}%", escape="\\")
            )
            stmt = stmt.where(search_filter)
            count_stmt = count_stmt.where(search_filter)

        total = (await self.session.execute(count_stmt)).scalar() or 0
        result = await self.session.execute(
            stmt.order_by(User.created_at.desc()).offset(offset).limit(limit)
        )
        users = list(result.scalars().all())
        return users, total