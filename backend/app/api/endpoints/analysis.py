"""
CodeGuard AI - Analysis API Endpoints
CRUD operations for security analysis management.
"""

from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.db.session import get_session
from app.db.base import ResponseSchema, PaginatedResponse
from app.models.user import User
from app.models.project import Project
from app.models.analysis import Analysis, Finding
from app.schemas.analysis import AnalysisCreate
from app.schemas.auth import UserRole
from app.api.dependencies import get_current_user, require_role
from app.core.exceptions import NotFoundException, ForbiddenException

router = APIRouter()


def _analysis_dict(a: Analysis) -> dict:
    return {
        "id": str(a.id),
        "project_id": str(a.project_id) if a.project_id else None,
        "branch": a.branch,
        "commit_hash": a.commit_hash,
        "status": a.status,
        "started_at": a.started_at.isoformat() if a.started_at else None,
        "completed_at": a.completed_at.isoformat() if a.completed_at else None,
        "summary": a.summary,
        "created_at": a.created_at.isoformat() if a.created_at else None,
        "updated_at": a.updated_at.isoformat() if a.updated_at else None,
    }


@router.get("/", response_model=PaginatedResponse)
async def list_analyses(
    project_id: str = Query(None),
    skip: int = Query(0, ge=0, le=10000),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> Any:
    """List analyses for the current user (or all for admin)."""
    query = select(Analysis)
    count_query = select(func.count()).select_from(Analysis)

    if current_user.role != UserRole.ADMIN:
        user_project_ids = select(Project.id).where(Project.user_id == current_user.id)
        query = query.where(Analysis.project_id.in_(user_project_ids))
        count_query = count_query.where(Analysis.project_id.in_(user_project_ids))

    if project_id:
        query = query.where(Analysis.project_id == project_id)
        count_query = count_query.where(Analysis.project_id == project_id)

    total = (await db.execute(count_query)).scalar() or 0
    result = await db.execute(query.order_by(Analysis.created_at.desc()).offset(skip).limit(limit))
    analyses = result.scalars().all()

    return PaginatedResponse(
        message="Analyses retrieved",
        data=[_analysis_dict(a) for a in analyses],
        pagination={"total": total, "page": skip // limit + 1, "page_size": limit, "total_pages": (total + limit - 1) // limit},
    )


@router.post("/", response_model=ResponseSchema)
async def create_analysis(
    data: AnalysisCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> Any:
    """Create a new analysis record."""
    if data.project_id:
        stmt = select(Project).where(Project.id == data.project_id)
        result = await db.execute(stmt)
        project = result.scalar_one_or_none()
        if not project:
            raise NotFoundException(message="Project not found")
        if project.user_id != current_user.id and not current_user.is_superuser:
            raise ForbiddenException(message="Access denied")

    analysis = Analysis(
        id=str(uuid4()),
        project_id=data.project_id,
        user_id=str(current_user.id),
        branch=data.branch,
        commit_hash=data.commit_hash,
        status="pending",
        analysis_metadata={"created_by": current_user.id},
    )
    db.add(analysis)
    await db.commit()
    await db.refresh(analysis)

    return ResponseSchema(message="Analysis created", data=_analysis_dict(analysis))


@router.get("/{analysis_id}", response_model=ResponseSchema)
async def get_analysis(
    analysis_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> Any:
    """Get an analysis by ID."""
    stmt = select(Analysis).where(Analysis.id == analysis_id)
    result = await db.execute(stmt)
    analysis = result.scalar_one_or_none()

    if not analysis:
        raise NotFoundException(message="Analysis not found")

    if analysis.project_id and current_user.role != UserRole.ADMIN:
        proj_stmt = select(Project).where(Project.id == analysis.project_id)
        proj = (await db.execute(proj_stmt)).scalar_one_or_none()
        if not proj or proj.user_id != current_user.id:
            raise ForbiddenException(message="Access denied")
    elif not analysis.project_id:
        # Scan without project — check user_id or analysis_metadata.uploaded_by
        owner_id = analysis.user_id or (analysis.analysis_metadata or {}).get("uploaded_by")
        if owner_id and str(owner_id) != str(current_user.id) and current_user.role != UserRole.ADMIN:
            raise ForbiddenException(message="Access denied")

    return ResponseSchema(message="Analysis retrieved", data=_analysis_dict(analysis))


@router.get("/{analysis_id}/findings", response_model=ResponseSchema)
async def get_analysis_findings(
    analysis_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> Any:
    """Get findings for an analysis."""
    stmt = select(Analysis).where(Analysis.id == analysis_id)
    result = await db.execute(stmt)
    analysis = result.scalar_one_or_none()

    if not analysis:
        raise NotFoundException(message="Analysis not found")

    # Ownership check: only the owner or admin can view findings
    if analysis.project_id and current_user.role != UserRole.ADMIN:
        proj_stmt = select(Project).where(Project.id == analysis.project_id)
        proj = (await db.execute(proj_stmt)).scalar_one_or_none()
        if not proj or proj.user_id != current_user.id:
            raise ForbiddenException(message="Access denied")
    elif not analysis.project_id:
        # Scan without project — check analysis_metadata.uploaded_by
        if analysis.analysis_metadata and analysis.analysis_metadata.get("uploaded_by") != str(current_user.id) and current_user.role != UserRole.ADMIN:
            raise ForbiddenException(message="Access denied")

    findings_stmt = select(Finding).options(selectinload(Finding.fix_suggestions)).where(Finding.analysis_id == analysis_id)
    findings_result = await db.execute(findings_stmt)
    findings = findings_result.scalars().all()

    findings_data = []
    for f in findings:
        findings_data.append({
            "id": str(f.id),
            "analyzer_type": f.analyzer_type,
            "vulnerability_type": f.vulnerability_type,
            "severity": f.severity.value if hasattr(f.severity, "value") else str(f.severity),
            "title": f.title,
            "description": f.description,
            "cwe_id": f.cwe_id,
            "cvss_score": f.cvss_score,
            "file_path": f.file_path,
            "line_start": f.line_start,
            "line_end": f.line_end,
            "code_snippet": f.code_snippet,
            "status": f.status,
            "confidence": f.confidence,
        })

    return ResponseSchema(message="Findings retrieved", data={"findings": findings_data, "total": len(findings_data)})


@router.delete("/{analysis_id}", response_model=ResponseSchema)
async def delete_analysis(
    analysis_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> Any:
    """Delete an analysis."""
    stmt = select(Analysis).where(Analysis.id == analysis_id)
    result = await db.execute(stmt)
    analysis = result.scalar_one_or_none()

    if not analysis:
        raise NotFoundException(message="Analysis not found")

    if analysis.project_id and current_user.role != UserRole.ADMIN:
        proj_stmt = select(Project).where(Project.id == analysis.project_id)
        proj = (await db.execute(proj_stmt)).scalar_one_or_none()
        if not proj or proj.user_id != current_user.id:
            raise ForbiddenException(message="Access denied")
    elif not analysis.project_id:
        # Scan without project — check user_id or analysis_metadata.uploaded_by
        owner_id = analysis.user_id or (analysis.analysis_metadata or {}).get("uploaded_by")
        if owner_id and str(owner_id) != str(current_user.id) and current_user.role != UserRole.ADMIN:
            raise ForbiddenException(message="Access denied")

    await db.delete(analysis)
    await db.commit()

    return ResponseSchema(message="Analysis deleted", data=None)