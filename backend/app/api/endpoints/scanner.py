"""CodeGuard AI - Scanner API Endpoints
Handles file upload, scan initiation, and scan status retrieval.
"""

import os
import uuid
import logging
import tempfile
import shutil
import asyncio
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings
from app.core.exceptions import FileException, ValidationError
from app.db.session import get_session
from app.models.user import User
from app.models.analysis import Analysis
from app.models.code_file import CodeFile
from app.models.project import Project
from app.schemas.scanner import ScanUploadResponse, ScanStatusResponse, ScanResultResponse, FindingResponse, FixSuggestionResponse
from app.api.dependencies import get_current_user, check_analysis_ownership
from app.services.file_validator import file_validator
from app.models.analysis import Finding, FixSuggestion

logger = logging.getLogger(__name__)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

UPLOAD_DIR = getattr(settings, "UPLOAD_DIR", "/tmp/codeguard_uploads")
MAX_UPLOAD_SIZE = getattr(settings, "MAX_FILE_SIZE", 10 * 1024 * 1024)  # 10MB default

def _write_file_sync(path: str, data: bytes):
    with open(path, "wb") as f:
        f.write(data)

def _read_file_sync(path: str) -> str:
    with open(path, "r", errors="replace") as f:
        return f.read()


@router.post("/upload", response_model=dict)
@limiter.limit("5/minute")
async def upload_scan_files(
    request: Request,
    files: List[UploadFile] = File(...),
    language: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Upload files for security scanning.

    Accepts one or more code files (or a ZIP archive).
    Validates files, stores them, creates an Analysis record, and queues a scan.
    """
    scan_id = str(uuid.uuid4())
    upload_dir = os.path.join(UPLOAD_DIR, scan_id)
    os.makedirs(upload_dir, exist_ok=True)

    total_files = 0
    validated_files = []

    try:
        for upload_file in files:
            # Stream-read in chunks with size limit — avoid loading entire file before validation
            chunks = []
            total_size = 0
            while True:
                chunk = await upload_file.read(1024 * 1024)  # 1MB chunks
                if not chunk:
                    break
                total_size += len(chunk)
                if total_size > MAX_UPLOAD_SIZE:
                    raise FileException(f"File '{upload_file.filename or 'unnamed'}' exceeds maximum upload size ({MAX_UPLOAD_SIZE // (1024*1024)}MB)")
                chunks.append(chunk)
            content = b"".join(chunks)
            filename = upload_file.filename or "unnamed"

            if filename.lower().endswith(".zip"):
                zip_path = os.path.join(upload_dir, filename)
                await asyncio.to_thread(_write_file_sync, zip_path, content)

                zip_result = file_validator.validate_zip(zip_path)
                if not zip_result.is_valid:
                    raise FileException(f"ZIP validation failed: {'; '.join(zip_result.errors)}")

                extracted, extract_errors = file_validator.extract_zip(
                    zip_path, os.path.join(upload_dir, "extracted")
                )

                for filepath in extracted:
                    ext = os.path.splitext(filepath)[1].lower()
                    if ext in [e.lower() for e in settings.ALLOWED_EXTENSIONS]:
                        file_content = await asyncio.to_thread(_read_file_sync, filepath)

                        code_file = CodeFile(
                            id=str(uuid.uuid4()),
                            file_path=filepath,
                            file_name=os.path.basename(filepath),
                            file_extension=ext,
                            language=language or ext.lstrip("."),
                            content=file_content,
                            line_count=file_content.count("\n") + 1,
                            file_metadata={"scan_id": scan_id, "source": "zip_upload"},
                        )
                        db.add(code_file)
                        validated_files.append(code_file)
                        total_files += 1

                if extract_errors:
                    logger.warning(f"ZIP extraction warnings: {extract_errors}")

            else:
                validation = file_validator.validate_file(filename, content)
                if not validation.is_valid:
                    raise FileException(f"File validation failed: {'; '.join(validation.errors)}")

                safe_path = os.path.join(upload_dir, validation.sanitized_filename)
                await asyncio.to_thread(_write_file_sync, safe_path, content)

                ext = os.path.splitext(validation.sanitized_filename)[1].lower()
                file_content = content.decode("utf-8", errors="replace")

                code_file = CodeFile(
                    id=str(uuid.uuid4()),
                    file_path=safe_path,
                    file_name=validation.sanitized_filename,
                    file_extension=ext,
                    language=language or ext.lstrip("."),
                    content=file_content,
                    line_count=file_content.count("\n") + 1,
                    file_metadata={"scan_id": scan_id, "source": "direct_upload"},
                )
                db.add(code_file)
                validated_files.append(code_file)
                total_files += 1

        if total_files == 0:
            raise FileException("No valid code files found in upload")

        analysis = Analysis(
            id=scan_id,
            user_id=str(current_user.id),
            status="pending",
            branch="main",
            analysis_metadata={
                "scan_id": scan_id,
                "file_count": total_files,
                "language": language,
                "uploaded_by": str(current_user.id),
            },
        )
        db.add(analysis)

        for cf in validated_files:
            cf.file_metadata["analysis_id"] = scan_id

        await db.commit()

        from app.tasks.scan_tasks import run_scan_task
        try:
            run_scan_task.delay(scan_id, [cf.id for cf in validated_files], current_user.id)
        except Exception as dispatch_err:
            # Celery is down — clean up upload dir to prevent disk accumulation
            logger.error(f"Failed to dispatch scan task: {dispatch_err}")
            shutil.rmtree(upload_dir, ignore_errors=True)
            raise HTTPException(status_code=503, detail="Scan service unavailable. Please try again later.")

        return {
            "success": True,
            "message": "Files uploaded and scan queued",
            "data": ScanUploadResponse(
                scan_id=scan_id,
                filename=files[0].filename if len(files) == 1 else f"{len(files)} files",
                file_count=total_files,
                status="pending",
                message="Scan has been queued for processing",
            ).model_dump(),
        }

    except (FileException, ValidationError) as e:
        await db.rollback()
        shutil.rmtree(upload_dir, ignore_errors=True)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await db.rollback()
        shutil.rmtree(upload_dir, ignore_errors=True)
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail="Failed to process upload")


@router.get("/{scan_id}/status", response_model=dict)
async def get_scan_status(
    scan_id: str,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get the status of a scan by its ID."""
    from sqlalchemy import select

    stmt = select(Analysis).where(Analysis.id == scan_id)
    result = await db.execute(stmt)
    analysis = result.scalar_one_or_none()

    if not analysis:
        raise HTTPException(status_code=404, detail=f"Scan {scan_id} not found")

    # Ownership check: only the owner or admin can view scan status
    check_analysis_ownership(analysis.analysis_metadata, current_user)

    progress = 0.0
    stage = "pending"
    if analysis.status == "running":
        stage = "analyzing"
        progress = 0.5
    elif analysis.status == "completed":
        stage = "completed"
        progress = 1.0
    elif analysis.status == "failed":
        stage = "failed"

    return {
        "success": True,
        "message": "Scan status retrieved",
        "data": ScanStatusResponse(
            scan_id=scan_id,
            status=analysis.status,
            progress=progress,
            stage=stage,
            total_files=analysis.analysis_metadata.get("file_count", 0) if analysis.analysis_metadata else 0,
            created_at=analysis.started_at,
            completed_at=analysis.completed_at,
        ).model_dump(),
    }


@router.get("/{scan_id}/results", response_model=dict)
async def get_scan_results(
    scan_id: str,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get full scan results: analysis metadata, findings with fix suggestions, and code files."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    stmt = select(Analysis).where(Analysis.id == scan_id)
    result = await db.execute(stmt)
    analysis = result.scalar_one_or_none()

    if not analysis:
        raise HTTPException(status_code=404, detail=f"Scan {scan_id} not found")

    # Ownership check
    check_analysis_ownership(analysis.analysis_metadata, current_user)

    # Fetch findings with fix suggestions
    findings_stmt = select(Finding).where(Finding.analysis_id == scan_id).options(
        selectinload(Finding.fix_suggestions)
    )
    findings_result = await db.execute(findings_stmt)
    findings = findings_result.scalars().all()

    # Fetch code files for this scan — metadata only, content loaded on demand
    code_files_stmt = select(CodeFile).options(load_only(
        CodeFile.id, CodeFile.file_name, CodeFile.file_path,
        CodeFile.file_extension, CodeFile.language, CodeFile.line_count,
        CodeFile.file_size,
    )).where(
        CodeFile.file_metadata["analysis_id"].as_string() == scan_id
    )
    code_files_result = await db.execute(code_files_stmt)
    code_files = code_files_result.scalars().all()

    code_files_dict = {}
    for cf in code_files:
        code_files_dict[cf.file_name] = {
            "id": str(cf.id),
            "language": cf.language,
            "lines": cf.line_count,
        }

    findings_data = []
    for f in findings:
        fix_suggestions = []
        for fs in f.fix_suggestions:
            fix_suggestions.append(FixSuggestionResponse(
                id=str(fs.id),
                title=fs.title,
                description=fs.description,
                priority=fs.priority,
                code_before=fs.code_before,
                code_after=fs.code_after,
                language=fs.language,
            ))
        findings_data.append(FindingResponse(
            id=str(f.id),
            vulnerability_type=f.vulnerability_type,
            severity=f.severity.value if hasattr(f.severity, "value") else str(f.severity),
            title=f.title,
            description=f.description,
            analyzer_type=f.analyzer_type,
            cwe_id=f.cwe_id,
            cvss_score=f.cvss_score,
            file_path=f.file_path,
            line_start=f.line_start,
            line_end=f.line_end,
            code_snippet=f.code_snippet,
            status=f.status,
            confidence=f.confidence,
            fix_suggestions=fix_suggestions,
        ))

    summary = analysis.summary or {
        "total_findings": len(findings_data),
        "by_severity": {},
    }

    return {
        "success": True,
        "message": "Scan results retrieved",
        "data": ScanResultResponse(
            scan_id=scan_id,
            status=analysis.status,
            total_files=analysis.analysis_metadata.get("file_count", 0) if analysis.analysis_metadata else 0,
            findings=findings_data,
            code_files=code_files_dict,
            summary=summary,
        ).model_dump(),
    }


@router.get("/{scan_id}/files/{file_id}/content", response_model=dict)
async def get_scan_file_content(
    scan_id: str,
    file_id: str,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Fetch content for a single code file (on-demand loading)."""
    stmt = select(Analysis).where(Analysis.id == scan_id)
    result = await db.execute(stmt)
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=404, detail=f"Scan {scan_id} not found")
    check_analysis_ownership(analysis.analysis_metadata, current_user)

    file_stmt = select(CodeFile).where(CodeFile.id == file_id)
    file_result = await db.execute(file_stmt)
    code_file = file_result.scalar_one_or_none()
    if not code_file:
        raise HTTPException(status_code=404, detail="File not found")

    return {
        "success": True,
        "data": {
            "id": str(code_file.id),
            "file_path": code_file.file_path,
            "file_name": code_file.file_name,
            "language": code_file.language,
            "content": code_file.content,
        },
    }


@router.post("/{scan_id}/findings/{finding_id}/preview-fix", response_model=dict)
async def preview_fix(
    scan_id: str,
    finding_id: str,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Generate a fix suggestion for a finding using the AI fallback chain."""
    from sqlalchemy import select

    # Verify scan ownership first
    analysis_stmt = select(Analysis).where(Analysis.id == scan_id)
    analysis_result = await db.execute(analysis_stmt)
    analysis = analysis_result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=404, detail="Scan not found")
    check_analysis_ownership(analysis.analysis_metadata, current_user)

    stmt = select(Finding).where(Finding.id == finding_id, Finding.analysis_id == scan_id)
    result = await db.execute(stmt)
    finding = result.scalar_one_or_none()

    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")

    if finding.fix_suggestions:
        existing = finding.fix_suggestions[0]
        return {
            "success": True,
            "message": "Existing fix suggestion found",
            "data": FixSuggestionResponse(
                id=str(existing.id),
                title=existing.title,
                description=existing.description,
                priority=existing.priority,
                code_before=existing.code_before,
                code_after=existing.code_after,
                language=existing.language,
            ).model_dump(),
        }

    # Generate fix via AI
    from app.ai.fallback_chain import ai_chain
    from app.api.endpoints.ai import _prompt_manager, _output_parser

    prompt_manager = _prompt_manager
    parser = _output_parser

    code_snippet = finding.code_snippet or ""
    language = analysis_metadata_language(finding)

    prompt = prompt_manager.render_template(
        "fix_generation",
        {
            "vulnerability_type": finding.vulnerability_type,
            "severity": finding.severity.value if hasattr(finding.severity, "value") else str(finding.severity),
            "cwe_id": finding.cwe_id or "",
            "language": language,
            "original_code": code_snippet,
            "explanation": finding.description or "",
        },
    )

    ai_result = await ai_chain.generate(prompt=prompt, finding={"vulnerability_type": finding.vulnerability_type})

    raw_response = ai_result.get("response", "")
    try:
        fix = parser.parse_fix_suggestion(raw_response, original_code=code_snippet)
    except Exception:
        fix = None

    if not fix:
        raise HTTPException(status_code=500, detail="Failed to generate fix suggestion")

    # AST re-validation: verify the fix produces syntactically correct code
    from app.services.ast_validators import ast_validator

    fixed_code = fix.fixed_code or ""
    validation = ast_validator.validate_fix(
        original_code=code_snippet,
        fixed_code=fixed_code,
        language=language,
    )
    ast_valid = validation["valid"]
    validation_warnings = validation.get("warnings", [])

    if not ast_valid:
        logger.warning(
            f"AST validation failed for finding {finding_id}: {validation_warnings}"
        )

    # Persist the fix suggestion with validation status
    new_fix = FixSuggestion(
        id=str(uuid.uuid4()),
        finding_id=finding.id,
        title=f"Fix for {finding.vulnerability_type}",
        description=fix.explanation,
        priority=1,
        code_before=fix.original_code,
        code_after=fixed_code,
        language=language,
    )
    db.add(new_fix)
    await db.commit()
    await db.refresh(new_fix)

    response_data = FixSuggestionResponse(
        id=str(new_fix.id),
        title=new_fix.title,
        description=new_fix.description,
        priority=new_fix.priority,
        code_before=new_fix.code_before,
        code_after=new_fix.code_after,
        language=new_fix.language,
    ).model_dump()
    response_data["ast_validated"] = ast_valid
    response_data["validation_warnings"] = validation_warnings

    return {
        "success": True,
        "message": "Fix suggestion generated" if ast_valid else "Fix suggestion generated but validation warnings",
        "data": response_data,
    }


@router.post("/{scan_id}/findings/{finding_id}/apply-fix", response_model=dict)
async def apply_fix(
    scan_id: str,
    finding_id: str,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Mark a finding as fixed and store the applied fix."""
    from sqlalchemy import select

    # Verify scan ownership first
    analysis_stmt = select(Analysis).where(Analysis.id == scan_id)
    analysis_result = await db.execute(analysis_stmt)
    analysis = analysis_result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=404, detail="Scan not found")
    check_analysis_ownership(analysis.analysis_metadata, current_user)

    stmt = select(Finding).where(Finding.id == finding_id, Finding.analysis_id == scan_id)
    result = await db.execute(stmt)
    finding = result.scalar_one_or_none()

    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")

    # Get the fix suggestion if available
    fix_data = None
    if finding.fix_suggestions:
        fix = finding.fix_suggestions[0]
        fix_data = {
            "code_before": fix.code_before,
            "code_after": fix.code_after,
            "explanation": fix.description,
        }

    # Update finding status
    finding.status = "fixed"
    # Create a new dict to ensure SQLAlchemy detects the mutation on the JSON column
    updated_metadata = {**(finding.finding_metadata or {})}
    updated_metadata["applied_fix"] = fix_data
    updated_metadata["fixed_by"] = str(current_user.id)
    updated_metadata["fixed_at"] = datetime.now(timezone.utc).isoformat()
    finding.finding_metadata = updated_metadata

    await db.commit()

    return {
        "success": True,
        "message": "Fix applied",
        "data": {
            "finding_id": str(finding.id),
            "new_status": "fixed",
        },
    }


def analysis_metadata_language(finding):
    """Extract language from finding metadata or default to python."""
    if finding.finding_metadata and "language" in finding.finding_metadata:
        return finding.finding_metadata["language"]
    return "python"


@router.get("/docker-health", response_model=dict)
async def docker_health_check(
    current_user: User = Depends(get_current_user),
):
    """Check if Docker daemon is accessible from the API container."""
    from app.services.container import container_service

    result = container_service.check_docker_available()
    if not result["available"]:
        raise HTTPException(
            status_code=503,
            detail={
                "available": False,
                "error": result["error"],
                "message": "Docker daemon is not accessible. Ensure /var/run/docker.sock is mounted.",
            },
        )
    return result