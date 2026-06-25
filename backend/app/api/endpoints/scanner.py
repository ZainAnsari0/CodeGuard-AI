"""CodeGuard AI - Scanner API Endpoints
Handles file upload, scan initiation, and scan status retrieval.
"""

import os
import uuid
import logging
import tempfile
import shutil
import asyncio
import json
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request, BackgroundTasks
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only, selectinload
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
from app.services.temp_workspace import workspace_service
from app.models.analysis import Finding, FixSuggestion

logger = logging.getLogger(__name__)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

# Use workspace service for scan workspace management
UPLOAD_DIR = getattr(settings, "UPLOAD_DIR", "/tmp/codeguard_uploads")

MAX_UPLOAD_SIZE = getattr(settings, "MAX_FILE_SIZE", 10 * 1024 * 1024)  # 10MB default

def _write_file_sync(path: str, data: bytes):
    with open(path, "wb") as f:
        f.write(data)

def _read_file_sync(path: str) -> str:
    with open(path, "r", errors="replace") as f:
        return f.read()


def _parse_json_field(value) -> Optional[dict]:
    """Safely parse a JSON string field (explanation column) to a dict."""
    if value is None:
        return None
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return None
    return None


@router.post("/upload", response_model=dict)
@limiter.limit("5/minute")
async def upload_scan_files(
    request: Request,
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    language: Optional[str] = Form(None),
    scan_name: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Upload files for security scanning.

    Accepts one or more code files (or a ZIP archive).
    Validates files, stores them, creates an Analysis record, and queues a scan.
    """
    scan_id = str(uuid.uuid4())
    # Create an isolated temporary workspace for this scan
    workspace_info = workspace_service.create_workspace(scan_id)
    upload_dir = workspace_info["path"]

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

        default_name = files[0].filename if len(files) == 1 else f"{len(files)} files"
        actual_scan_name = scan_name or default_name

        analysis = Analysis(
            id=scan_id,
            user_id=str(current_user.id),
            status="pending",
            branch="main",
            scan_name=actual_scan_name,
            analysis_metadata={
                "scan_id": scan_id,
                "file_count": total_files,
                "files_completed": 0,
                "language": language,
                "uploaded_by": str(current_user.id),
            },
        )
        db.add(analysis)

        for cf in validated_files:
            cf.file_metadata["analysis_id"] = scan_id

        await db.commit()

        from app.tasks.scan_tasks import run_scan_task, _run_scan_async
        try:
            run_scan_task.delay(scan_id, [cf.id for cf in validated_files], str(current_user.id))
        except Exception as dispatch_err:
            # Celery is down — run scan inline via asyncio task so uploads still work safely
            logger.warning(f"Celery dispatch failed ({dispatch_err}), running scan inline via asyncio task")
            try:
                scan_config = {
                    "file_ids": [cf.id for cf in validated_files],
                    "user_id": str(current_user.id),
                    "scan_id": scan_id,
                }
                asyncio.ensure_future(
                    _run_scan_async(
                        scan_id,
                        [cf.id for cf in validated_files],
                        str(current_user.id),
                        upload_dir,
                        scan_config,
                    )
                )
            except Exception as inline_err:
                logger.error(f"Inline scan execution request failed: {inline_err}")
                # Scan will show as "pending" — user can retry later

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
        logger.error(f"Upload error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process upload: {str(e)}")


@router.get("/{scan_id}/status", response_model=dict)
async def get_scan_status(
    scan_id: UUID,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get the status of a scan by its ID."""
    from sqlalchemy import select, func

    stmt = select(Analysis).where(Analysis.id == str(scan_id))
    result = await db.execute(stmt)
    analysis = result.scalar_one_or_none()

    if not analysis:
        raise HTTPException(status_code=404, detail=f"Scan {scan_id} not found")

    # Count findings via an explicit query — accessing analysis.findings directly
    # would trigger async lazy-loading (MissingGreenlet) since it isn't eager-loaded.
    findings_count_stmt = select(func.count(Finding.id)).where(Finding.analysis_id == str(scan_id))
    findings_count_result = await db.execute(findings_count_stmt)
    findings_count = findings_count_result.scalar() or 0

    # Ownership check: only the owner or admin can view scan status
    check_analysis_ownership(analysis.analysis_metadata, current_user)

    progress = 0.0
    stage = "pending"
    if analysis.status == "running":
        stage = "analyzing"
        completed = analysis.analysis_metadata.get("files_completed", 0) if analysis.analysis_metadata else 0
        total = analysis.analysis_metadata.get("file_count", 1) if analysis.analysis_metadata else 1
        if total > 0:
            progress = min(0.95, completed / total)
        else:
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
            scan_id=str(scan_id),
            status=analysis.status,
            progress=progress,
            stage=stage,
            total_files=analysis.analysis_metadata.get("file_count", 0) if analysis.analysis_metadata else 0,
            files_scanned=analysis.analysis_metadata.get("files_completed", 0) if analysis.analysis_metadata else 0,
            findings_count=findings_count,
            created_at=analysis.started_at,
            completed_at=analysis.completed_at,
        ).model_dump(),
    }


@router.get("/{scan_id}/results", response_model=dict)
async def get_scan_results(
    scan_id: UUID,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get full scan results: analysis metadata, findings with fix suggestions, and code files."""
    from sqlalchemy import select, func
    from sqlalchemy.orm import selectinload

    stmt = select(Analysis).where(Analysis.id == str(scan_id))
    result = await db.execute(stmt)
    analysis = result.scalar_one_or_none()

    if not analysis:
        raise HTTPException(status_code=404, detail=f"Scan {scan_id} not found")

    # Ownership check
    check_analysis_ownership(analysis.analysis_metadata, current_user)

    # Fetch total findings count
    total_findings_stmt = select(func.count(Finding.id)).where(Finding.analysis_id == str(scan_id))
    total_findings_result = await db.execute(total_findings_stmt)
    total_findings_count = total_findings_result.scalar() or 0

    # Fetch findings with fix suggestions (paginated)
    findings_stmt = select(Finding).where(Finding.analysis_id == str(scan_id)).options(
        selectinload(Finding.fix_suggestions)
    ).limit(limit).offset(offset)
    findings_result = await db.execute(findings_stmt)
    findings = findings_result.scalars().all()

    # Fetch code files for this scan — include content for direct display
    code_files_stmt = select(CodeFile).where(
        CodeFile.file_metadata["analysis_id"].as_string() == str(scan_id)
    )
    code_files_result = await db.execute(code_files_stmt)
    code_files = code_files_result.scalars().all()

    code_files_dict = {}
    for cf in code_files:
        code_files_dict[cf.file_name] = cf.content or ""

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
                ast_validated=fs.ast_validated,
                validation_warnings=fs.validation_warnings if isinstance(fs.validation_warnings, list) else (
                    json.loads(fs.validation_warnings) if isinstance(fs.validation_warnings, str) else None
                ) if fs.validation_warnings else None,
                confidence=float(fs.confidence) if fs.confidence else None,
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
            finding_metadata=f.finding_metadata if isinstance(f.finding_metadata, dict) else (
                json.loads(f.finding_metadata) if isinstance(f.finding_metadata, str) else None
            ),
            explanation=_parse_json_field(f.explanation),
            explanation_provider=f.explanation_provider,
        ))

    summary = analysis.summary or {
        "total_findings": total_findings_count,
        "by_severity": {},
    }
    if isinstance(summary, dict):
        summary["total_findings"] = total_findings_count

    return {
        "success": True,
        "message": "Scan results retrieved",
        "pagination": {
            "total": total_findings_count,
            "limit": limit,
            "offset": offset,
        },
        "data": ScanResultResponse(
            scan_id=str(scan_id),
            status=analysis.status,
            total_files=analysis.analysis_metadata.get("file_count", 0) if analysis.analysis_metadata else 0,
            findings=findings_data,
            code_files=code_files_dict,
            summary=summary,
        ).model_dump(),
    }


@router.get("/{scan_id}/files/{file_id}/content", response_model=dict)
async def get_scan_file_content(
    scan_id: UUID,
    file_id: UUID,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Fetch content for a single code file (on-demand loading)."""
    stmt = select(Analysis).where(Analysis.id == str(scan_id))
    result = await db.execute(stmt)
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=404, detail=f"Scan {scan_id} not found")
    check_analysis_ownership(analysis.analysis_metadata, current_user)

    file_stmt = select(CodeFile).where(CodeFile.id == str(file_id))
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
    scan_id: UUID,
    finding_id: UUID,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Generate a fix suggestion for a finding using the AI fallback chain."""
    from sqlalchemy import select

    # Verify scan ownership first
    analysis_stmt = select(Analysis).where(Analysis.id == str(scan_id))
    analysis_result = await db.execute(analysis_stmt)
    analysis = analysis_result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=404, detail="Scan not found")
    check_analysis_ownership(analysis.analysis_metadata, current_user)

    stmt = select(Finding).where(Finding.id == str(finding_id), Finding.analysis_id == str(scan_id)).options(
        selectinload(Finding.fix_suggestions)
    )
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
                ast_validated=existing.ast_validated,
                validation_warnings=existing.validation_warnings if isinstance(existing.validation_warnings, list) else (
                    json.loads(existing.validation_warnings) if isinstance(existing.validation_warnings, str) else None
                ) if existing.validation_warnings else None,
                confidence=float(existing.confidence) if existing.confidence else None,
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
        ast_validated=ast_valid,
        validation_warnings=validation_warnings,
        confidence=float(fix.confidence) if fix.confidence else None,
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
        ast_validated=ast_valid,
        validation_warnings=validation_warnings,
        confidence=float(new_fix.confidence) if new_fix.confidence else None,
    ).model_dump()

    return {
        "success": True,
        "message": "Fix suggestion generated" if ast_valid else "Fix suggestion generated but validation warnings",
        "data": response_data,
    }


@router.post("/{scan_id}/findings/{finding_id}/apply-fix", response_model=dict)
async def apply_fix(
    scan_id: UUID,
    finding_id: UUID,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Mark a finding as fixed and store the applied fix."""
    from sqlalchemy import select

    # Verify scan ownership first
    analysis_stmt = select(Analysis).where(Analysis.id == str(scan_id))
    analysis_result = await db.execute(analysis_stmt)
    analysis = analysis_result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=404, detail="Scan not found")
    check_analysis_ownership(analysis.analysis_metadata, current_user)

    stmt = select(Finding).where(Finding.id == str(finding_id), Finding.analysis_id == str(scan_id)).options(
        selectinload(Finding.fix_suggestions)
    )
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


@router.post("/{scan_id}/findings/{finding_id}/enrich", response_model=dict)
async def enrich_finding(
    scan_id: UUID,
    finding_id: UUID,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """On-demand AI enrichment for a single finding.

    Generates an explanation and fix suggestion (for critical/high),
    persists them to the DB, and returns the enriched finding data.
    If the finding is already enriched, returns the cached data.
    """
    from app.services.ai_enrichment_service import ai_enrichment_service

    # Verify scan ownership
    analysis_stmt = select(Analysis).where(Analysis.id == str(scan_id))
    analysis_result = await db.execute(analysis_stmt)
    analysis = analysis_result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=404, detail="Scan not found")
    check_analysis_ownership(analysis.analysis_metadata, current_user)

    # Enrich and persist
    try:
        result = await ai_enrichment_service.enrich_finding_and_persist(
            finding_id=str(finding_id),
            scan_id=str(scan_id),
            db=db,
        )
    except Exception as e:
        logger.error(f"On-demand enrichment failed: {e}")
        raise HTTPException(status_code=500, detail=f"Enrichment failed: {str(e)}")

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    # Build the FindingResponse from the result
    fix_suggestions = [
        FixSuggestionResponse(**fs) for fs in result.get("fix_suggestions", [])
    ]
    finding_response = FindingResponse(
        id=result["id"],
        vulnerability_type=result["vulnerability_type"],
        severity=result["severity"],
        title=result.get("title", ""),
        description=result.get("description"),
        analyzer_type="sast",
        cwe_id=result.get("cwe_id"),
        file_path=result.get("file_path", ""),
        line_start=result.get("line_start"),
        line_end=result.get("line_end"),
        code_snippet=result.get("code_snippet"),
        status=result.get("status", "new"),
        confidence=result.get("confidence"),
        fix_suggestions=fix_suggestions,
        explanation=result.get("explanation"),
        explanation_provider=result.get("explanation_provider"),
    )

    from app.schemas.scanner import EnrichFindingResponse
    return {
        "success": True,
        "message": "Finding enriched" if not result.get("explanation_cached") else "Enrichment retrieved from cache",
        "data": EnrichFindingResponse(
            finding=finding_response,
            explanation_cached=result.get("explanation_cached", False),
        ).model_dump(),
    }


def analysis_metadata_language(finding):
    """Extract language from finding metadata or default to python."""
    if finding.finding_metadata and "language" in finding.finding_metadata:
        return finding.finding_metadata["language"]
    return "python"


@router.get("/workspace-health", response_model=dict)
async def workspace_health_check(
    current_user: User = Depends(get_current_user),
):
    """Check if the temporary scan workspace service is available.

    Replaces the former Docker health check. Since scans now run via
    in-process AST analysis (no containers), this checks that the
    temporary workspace directory is writable.
    """
    from app.services.temp_workspace import workspace_service

    result = workspace_service.check_available()
    if not result["available"]:
        raise HTTPException(
            status_code=503,
            detail={
                "available": False,
                "error": result["error"],
                "message": "Scan workspace directory is not accessible. Check UPLOAD_DIR configuration.",
            },
        )
    return result