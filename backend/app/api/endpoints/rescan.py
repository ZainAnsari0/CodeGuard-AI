"""CodeGuard AI - Rescan API Endpoint
Re-scan a project after fixes have been applied.
"""

import os
import uuid
import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.user import User
from app.models.analysis import Analysis
from app.models.code_file import CodeFile
from app.api.dependencies import get_current_user, check_analysis_ownership
from app.core.exceptions import ForbiddenException

logger = logging.getLogger(__name__)

router = APIRouter()

ALLOWED_UPLOAD_DIR = os.path.join(os.sep, "tmp", "codeguard_uploads")


def _sanitize_file_name(name: str) -> str:
    """Sanitize a file name to prevent path traversal."""
    base = os.path.basename(name)
    if not base or base.startswith("."):
        raise ValueError(f"Invalid file name: {name}")
    return base


@router.post("/{analysis_id}/rescan", response_model=dict)
async def rescan_analysis(
    analysis_id: str,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Create a new analysis by re-scanning the files from a previous analysis.

    This endpoint takes an existing analysis, finds its associated code files,
    and creates a new analysis + Celery task to re-run the scan pipeline.
    Useful after applying fixes to verify that vulnerabilities have been resolved.
    """
    from app.core.config import settings

    upload_dir_base = getattr(settings, "UPLOAD_DIR", ALLOWED_UPLOAD_DIR)

    # Fetch the original analysis
    stmt = select(Analysis).where(Analysis.id == analysis_id)
    result = await db.execute(stmt)
    original_analysis = result.scalar_one_or_none()

    if not original_analysis:
        raise HTTPException(status_code=404, detail=f"Analysis {analysis_id} not found")

    # Authorization: only the owner or admin can rescan
    check_analysis_ownership(original_analysis.analysis_metadata, current_user)

    # Find code files associated with the original analysis
    code_files_stmt = select(CodeFile).where(
        CodeFile.file_metadata["analysis_id"].as_string() == analysis_id
    )
    code_files_result = await db.execute(code_files_stmt)
    code_files = code_files_result.scalars().all()

    if not code_files:
        raise HTTPException(
            status_code=400,
            detail="No code files found for this analysis. Re-upload the files instead.",
        )

    # Create a new analysis record
    new_analysis_id = str(uuid.uuid4())
    new_analysis = Analysis(
        id=new_analysis_id,
        project_id=original_analysis.project_id,
        user_id=str(current_user.id),
        status="pending",
        branch=original_analysis.branch or "main",
        analysis_metadata={
            "scan_id": new_analysis_id,
            "file_count": len(code_files),
            "language": (original_analysis.analysis_metadata or {}).get("language"),
            "uploaded_by": str(current_user.id),
            "rescan_of": analysis_id,
        },
    )
    db.add(new_analysis)

    # Update code file metadata to point to the new analysis
    file_ids = []
    for cf in code_files:
        cf.file_metadata = {**(cf.file_metadata or {}), "analysis_id": new_analysis_id}
        file_ids.append(str(cf.id))

    await db.commit()

    # Queue the scan task using the same upload directory
    from app.tasks.scan_tasks import run_scan_task

    upload_dir = os.path.join(upload_dir_base, analysis_id)
    scan_dir = upload_dir if os.path.isdir(upload_dir) else None

    if not scan_dir:
        # Original upload dir was cleaned up — re-create files from DB content
        new_upload_dir = os.path.join(upload_dir_base, new_analysis_id)
        os.makedirs(new_upload_dir, exist_ok=True)

        for cf in code_files:
            if cf.content:
                safe_name = _sanitize_file_name(cf.file_name)
                file_path = os.path.join(new_upload_dir, safe_name)
                # Write file in a thread to avoid blocking the event loop
                await asyncio.to_thread(
                    _write_file_sync, file_path, cf.content,
                )

    run_scan_task.delay(new_analysis_id, file_ids, str(current_user.id))

    return {
        "success": True,
        "message": "Re-scan initiated",
        "data": {
            "new_analysis_id": new_analysis_id,
            "original_analysis_id": analysis_id,
            "status": "pending",
            "file_count": len(code_files),
        },
    }


def _write_file_sync(path: str, content: str) -> None:
    with open(path, "w") as f:
        f.write(content)