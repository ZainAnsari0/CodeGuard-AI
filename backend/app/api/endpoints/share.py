"""
CodeGuard AI - Share API Endpoints
Create, list, revoke, and access shared report tokens.
"""

import uuid
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_session
from app.models.user import User
from app.models.share_token import ShareToken
from app.models.analysis import Analysis, Finding
from app.models.code_file import CodeFile
from app.schemas.share import ShareCreate, ShareResponse, ShareListResponse
from app.schemas.scanner import ScanResultResponse, FindingResponse, FixSuggestionResponse
from app.api.dependencies import get_current_user, require_role
from app.schemas.auth import UserRole

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=dict)
async def create_share_token(
    data: ShareCreate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Create a shareable link for a scan report."""
    # Verify the analysis exists and user owns it
    stmt = select(Analysis).where(Analysis.id == data.analysis_id)
    result = await db.execute(stmt)
    analysis = result.scalar_one_or_none()

    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    # Ownership check: only the owner or admin can share an analysis
    if analysis.analysis_metadata and analysis.analysis_metadata.get("uploaded_by") != str(current_user.id) and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to share this analysis")

    expires_at = None
    if data.expires_in_hours:
        expires_at = datetime.now(timezone.utc) + timedelta(hours=data.expires_in_hours)

    share = ShareToken(
        id=str(uuid.uuid4()),
        analysis_id=data.analysis_id,
        created_by=current_user.id,
        expires_at=expires_at,
    )
    db.add(share)
    await db.commit()
    await db.refresh(share)

    share_url = f"/share/{share.token}"

    return {
        "success": True,
        "message": "Share link created",
        "data": ShareResponse(
            id=share.id, token=share.token, share_url=share_url,
            analysis_id=share.analysis_id, expires_at=share.expires_at,
            view_count=share.view_count, created_at=share.created_at,
        ).model_dump(),
    }


@router.get("", response_model=dict)
async def list_user_shares(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """List current user's share tokens."""
    count_stmt = select(func.count()).select_from(ShareToken).where(ShareToken.created_by == current_user.id)
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    stmt = (
        select(ShareToken)
        .where(ShareToken.created_by == current_user.id)
        .order_by(ShareToken.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    result = await db.execute(stmt)
    shares = result.scalars().all()

    share_list = [
        ShareResponse(
            id=s.id, token=s.token, share_url=f"/share/{s.token}",
            analysis_id=s.analysis_id, expires_at=s.expires_at,
            view_count=s.view_count, created_at=s.created_at,
        ).model_dump()
        for s in shares
    ]

    return {
        "success": True,
        "data": ShareListResponse(shares=share_list, total=total).model_dump(),
    }


@router.get("/{token}", response_model=dict)
async def get_shared_report(
    token: str,
    db: AsyncSession = Depends(get_session),
):
    """Public endpoint: Get scan results by share token (no auth required)."""
    stmt = select(ShareToken).where(ShareToken.token == token)
    result = await db.execute(stmt)
    share = result.scalar_one_or_none()

    if not share:
        raise HTTPException(status_code=404, detail="Share link not found")
    if share.is_revoked:
        raise HTTPException(status_code=410, detail="Share link has been revoked")
    if share.expires_at and share.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="Share link has expired")

    # Increment view count atomically
    await db.execute(
        ShareToken.__table__.update()
        .where(ShareToken.id == share.id)
        .values(view_count=func.coalesce(ShareToken.view_count, 0) + 1)
    )
    await db.commit()

    # Fetch the analysis
    stmt = select(Analysis).where(Analysis.id == share.analysis_id)
    result = await db.execute(stmt)
    analysis = result.scalar_one_or_none()

    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    # Fetch findings with fix suggestions
    findings_stmt = select(Finding).where(Finding.analysis_id == share.analysis_id).options(
        selectinload(Finding.fix_suggestions)
    )
    findings_result = await db.execute(findings_stmt)
    findings = findings_result.scalars().all()

    # Fetch code files
    code_files_stmt = select(CodeFile).where(
        CodeFile.file_metadata["analysis_id"].as_string() == share.analysis_id
    )
    code_files_result = await db.execute(code_files_stmt)
    code_files = code_files_result.scalars().all()

    code_files_dict = {cf.file_name: cf.content for cf in code_files if cf.content}

    findings_data = []
    for f in findings:
        fix_suggestions = []
        for fs in f.fix_suggestions:
            fix_suggestions.append(FixSuggestionResponse(
                id=str(fs.id), title=fs.title, description=fs.description,
                priority=fs.priority, code_before=fs.code_before,
                code_after=fs.code_after, language=fs.language,
            ).model_dump())
        findings_data.append(FindingResponse(
            id=str(f.id), vulnerability_type=f.vulnerability_type,
            severity=f.severity.value if hasattr(f.severity, "value") else str(f.severity),
            title=f.title, description=f.description, analyzer_type=f.analyzer_type,
            cwe_id=f.cwe_id, cvss_score=f.cvss_score, file_path=f.file_path,
            line_start=f.line_start, line_end=f.line_end, code_snippet=f.code_snippet,
            status=f.status, confidence=f.confidence, fix_suggestions=fix_suggestions,
        ).model_dump())

    summary = analysis.summary or {"total_findings": len(findings_data), "by_severity": {}}

    return {
        "success": True,
        "data": ScanResultResponse(
            scan_id=share.analysis_id, status=analysis.status,
            total_files=analysis.analysis_metadata.get("file_count", 0) if analysis.analysis_metadata else 0,
            findings=findings_data, code_files=code_files_dict, summary=summary,
        ).model_dump(),
        "shared": True,
    }


@router.delete("/{token}", response_model=dict)
async def revoke_share_token(
    token: str,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Revoke a share token (owner or admin only)."""
    stmt = select(ShareToken).where(ShareToken.token == token)
    result = await db.execute(stmt)
    share = result.scalar_one_or_none()

    if not share:
        raise HTTPException(status_code=404, detail="Share link not found")
    if share.created_by != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to revoke this link")

    share.is_revoked = True
    await db.commit()

    return {"success": True, "message": "Share link revoked"}