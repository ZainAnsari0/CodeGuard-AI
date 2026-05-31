"""CodeGuard AI - Project Service (Domain Layer)

Business logic for project CRUD operations.
Extracts project business rules from endpoint handlers.
"""

import logging
from typing import Optional
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.project import Project
from app.models.user import User
from app.core.exceptions import EntityNotFound, AccessDenied
from app.schemas.auth import UserRole
from app.schemas.project import ProjectCreate, ProjectUpdate

logger = logging.getLogger(__name__)


class ProjectService:
    """Business operations for project management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_projects(
        self,
        user: User,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Project], int]:
        """List projects for the given user. Returns (projects, total)."""
        count_stmt = select(func.count()).select_from(Project).where(Project.user_id == user.id)
        total = (await self.db.execute(count_stmt)).scalar() or 0

        stmt = (
            select(Project)
            .where(Project.user_id == user.id)
            .order_by(Project.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        projects = list(result.scalars().all())
        return projects, total

    async def create_project(
        self,
        user: User,
        data: ProjectCreate,
    ) -> Project:
        """Create a new project owned by the given user."""
        project = Project(
            id=str(uuid4()),
            name=data.name,
            description=data.description,
            repository_url=data.repository_url,
            branch=data.branch,
            config=data.config or {},
            user_id=user.id,
        )
        self.db.add(project)
        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def get_project(self, project_id: str, user: User) -> Project:
        """Get a project by ID, checking ownership.

        Raises:
            EntityNotFound: If project doesn't exist.
            AccessDenied: If user doesn't own the project.
        """
        stmt = select(Project).where(Project.id == project_id)
        result = await self.db.execute(stmt)
        project = result.scalar_one_or_none()

        if not project:
            raise EntityNotFound(entity="Project", entity_id=project_id)

        if project.user_id != user.id and not user.is_superuser:
            raise AccessDenied(message="Access denied")

        return project

    async def update_project(
        self,
        project_id: str,
        user: User,
        data: ProjectUpdate,
    ) -> Project:
        """Update a project with ownership check."""
        project = await self.get_project(project_id, user)

        update_data = data.model_dump(exclude_unset=True)
        allowed_fields = {"name", "description", "repository_url", "branch", "config"}
        for field, value in update_data.items():
            if field in allowed_fields:
                setattr(project, field, value)

        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def delete_project(self, project_id: str, user: User) -> None:
        """Delete a project with ownership check."""
        project = await self.get_project(project_id, user)
        await self.db.delete(project)
        await self.db.commit()

    @staticmethod
    def project_to_dict(p: Project) -> dict:
        """Serialize a Project model to a response dict."""
        return {
            "id": str(p.id),
            "name": p.name,
            "description": p.description,
            "repository_url": p.repository_url,
            "branch": p.branch,
            "config": p.config,
            "user_id": str(p.user_id),
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "updated_at": p.updated_at.isoformat() if p.updated_at else None,
        }