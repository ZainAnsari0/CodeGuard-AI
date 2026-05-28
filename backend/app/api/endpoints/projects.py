"""
CodeGuard AI - Projects API Endpoints
CRUD operations for project management.
"""

from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.session import get_session
from app.db.base import ResponseSchema, PaginatedResponse
from app.models.user import User
from app.models.project import Project
from app.models.code_file import CodeFile
from app.models.analysis import Analysis
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.api.dependencies import get_current_user
from app.core.exceptions import NotFoundException, ForbiddenException

router = APIRouter()


def _project_dict(p: Project) -> dict:
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


@router.get("/", response_model=PaginatedResponse)
async def list_projects(
    skip: int = Query(0, ge=0, le=10000),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> Any:
    """List projects for the current user."""
    count_stmt = select(func.count()).select_from(Project).where(Project.user_id == current_user.id)
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = (
        select(Project)
        .where(Project.user_id == current_user.id)
        .order_by(Project.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    projects = result.scalars().all()

    return PaginatedResponse(
        message="Projects retrieved",
        data=[_project_dict(p) for p in projects],
        pagination={"total": total, "page": skip // limit + 1, "page_size": limit, "total_pages": (total + limit - 1) // limit},
    )


@router.post("/", response_model=ResponseSchema)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> Any:
    """Create a new project."""
    project = Project(
        id=str(uuid4()),
        name=project_data.name,
        description=project_data.description,
        repository_url=project_data.repository_url,
        branch=project_data.branch,
        config=project_data.config or {},
        user_id=current_user.id,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)

    return ResponseSchema(message="Project created", data=_project_dict(project))


@router.get("/{project_id}", response_model=ResponseSchema)
async def get_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> Any:
    """Get a project by ID."""
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    if not project:
        raise NotFoundException(message="Project not found")
    if project.user_id != current_user.id and not current_user.is_superuser:
        raise ForbiddenException(message="Access denied")

    return ResponseSchema(message="Project retrieved", data=_project_dict(project))


@router.patch("/{project_id}", response_model=ResponseSchema)
async def update_project(
    project_id: str,
    project_data: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> Any:
    """Update a project."""
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    if not project:
        raise NotFoundException(message="Project not found")
    if project.user_id != current_user.id and not current_user.is_superuser:
        raise ForbiddenException(message="Access denied")

    update_data = project_data.model_dump(exclude_unset=True)
    allowed_fields = {"name", "description", "repository_url", "branch", "config"}
    for field, value in update_data.items():
        if field in allowed_fields:
            setattr(project, field, value)

    await db.commit()
    await db.refresh(project)

    return ResponseSchema(message="Project updated", data=_project_dict(project))


@router.delete("/{project_id}", response_model=ResponseSchema)
async def delete_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> Any:
    """Delete a project."""
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    if not project:
        raise NotFoundException(message="Project not found")
    if project.user_id != current_user.id and not current_user.is_superuser:
        raise ForbiddenException(message="Access denied")

    await db.delete(project)
    await db.commit()

    return ResponseSchema(message="Project deleted", data=None)