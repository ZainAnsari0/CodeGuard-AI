"""
CodeGuard AI - Scan Tasks
Celery tasks for running security scans in ephemeral containers.
"""

import json
import logging
import os
import shutil
import uuid
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List

from sqlalchemy import create_engine, text

from app.tasks.celery_app import celery_app
from app.services.container import container_service
from app.core.config import settings

logger = logging.getLogger(__name__)

# Module-level engine with connection pooling for Celery tasks
_sync_engine = None


def _get_sync_engine():
    """Get or create the module-level sync engine for Celery tasks."""
    global _sync_engine
    if _sync_engine is None:
        from sqlalchemy.engine import make_url

        db_url = settings.DATABASE_URL
        parsed = make_url(db_url)

        # Convert async driver to its synchronous counterpart
        _ASYNC_TO_SYNC = {
            "aiosqlite": "pysqlite",
            "asyncpg": "psycopg2",
            "asyncmy": "pymysql",
        }
        sync_driver = _ASYNC_TO_SYNC.get(parsed.get_driver_name())
        if sync_driver:
            parsed = parsed.set(drivername=f"{parsed.drivername.rsplit('+', 1)[0]}+{sync_driver}" if '+' in parsed.drivername else f"{parsed.get_dialect().name}+{sync_driver}")
            db_url = str(parsed)
        else:
            # If no async driver detected, strip any async prefix just in case
            db_url = str(parsed)

        engine_kwargs = {"echo": False}
        if not db_url.startswith("sqlite"):
            engine_kwargs.update({
                "pool_size": 5,
                "max_overflow": 10,
                "pool_pre_ping": True,
                "pool_recycle": 3600,
            })
        else:
            engine_kwargs["connect_args"] = {"check_same_thread": False}

        _sync_engine = create_engine(db_url, **engine_kwargs)
        logger.info("Created sync engine for Celery tasks")
    return _sync_engine


@celery_app.task(name="run_scan_task", bind=True, max_retries=2)
def run_scan_task(self, scan_id: str, file_ids: List[str], user_id: str) -> Dict[str, Any]:
    """Run a security scan in an ephemeral container.

    Task lifecycle: PENDING -> RUNNING -> COMPLETED/FAILED

    Args:
        scan_id: Analysis ID for this scan
        file_ids: List of CodeFile IDs to scan
        user_id: ID of the user who initiated the scan
    """
    logger.info(f"Starting scan task for {scan_id} with {len(file_ids)} files")

    try:
        _update_analysis_status(scan_id, "running")
    except Exception as e:
        logger.error(f"Failed to set scan status to running: {e}")

    try:

        upload_dir = os.path.join(getattr(settings, "UPLOAD_DIR", "/tmp/codeguard_uploads"), scan_id)
        if not os.path.isdir(upload_dir):
            logger.error(f"Upload directory not found: {upload_dir}")
            _update_analysis_status(scan_id, "failed", error="Upload directory not found")
            return {"status": "failed", "error": "Upload directory not found"}

        scan_config = {
            "file_ids": file_ids,
            "user_id": user_id,
            "scan_id": scan_id,
        }

        # spawn_scan_container is async — run via asyncio.run() which handles
        # loop creation and cleanup properly (Python 3.10+)
        result = asyncio.run(
            container_service.spawn_scan_container(
                code_volume_path=upload_dir,
                scanner_image=getattr(settings, "SCANNER_IMAGE", "codeguard-scanner:latest"),
                scan_config=scan_config,
            )
        )

        if result["status"] == "completed" and result["exit_code"] == 0:
            output_data = None
            try:
                output_data = json.loads(result["output"])
                findings = output_data.get("findings", [])
            except json.JSONDecodeError:
                findings = _parse_raw_output(result["output"])

            # Persist findings to DB
            _persist_findings(scan_id, file_ids, findings)

            _update_analysis_status(
                scan_id,
                "completed",
                metadata={
                    "total_findings": len(findings),
                    "scanner_output": output_data if output_data else result,
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                },
            )

            return {
                "status": "completed",
                "scan_id": scan_id,
                "total_findings": len(findings),
                "container_id": result.get("container_id"),
            }
        else:
            error_msg = result.get("output", "Unknown scan error")
            _update_analysis_status(scan_id, "failed", error=error_msg[:500])
            return {"status": "failed", "scan_id": scan_id, "error": error_msg[:500]}

    except Exception as e:
        logger.error(f"Scan task failed: {e}", exc_info=True)
        if self.request.retries < self.max_retries:
            # Don't mark as failed yet — retry will set status back to running
            raise self.retry(exc=e, countdown=60)
        else:
            _update_analysis_status(scan_id, "failed", error=str(e)[:500])
    finally:
        # Close Docker client to release resources
        try:
            container_service.close()
        except Exception:
            pass
        # Clean up upload directory to prevent disk space accumulation
        upload_dir = os.path.join(getattr(settings, "UPLOAD_DIR", "/tmp/codeguard_uploads"), scan_id)
        if os.path.isdir(upload_dir):
            try:
                shutil.rmtree(upload_dir)
                logger.info(f"Cleaned up upload directory: {upload_dir}")
            except Exception as cleanup_err:
                logger.warning(f"Failed to clean up upload directory {upload_dir}: {cleanup_err}")


@celery_app.task(name="update_scan_status")
def update_scan_status(scan_id: str, status: str, details: Dict[str, Any] = None) -> Dict[str, Any]:
    """Update the status of a scan in the database."""
    return _update_analysis_status(scan_id, status, details=details)


# Strict allowlist of columns that may appear in UPDATE statements
_ALLOWED_UPDATE_COLUMNS = frozenset({
    "status", "started_at", "completed_at", "error", "summary",
})


def _update_analysis_status(scan_id: str, status: str, error: str = None,
                             metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """Update analysis record status in the database.

    Uses synchronous DB access since Celery workers are sync.
    """
    try:
        engine = _get_sync_engine()

        with engine.connect() as conn:
            update_fields = {"status": status}
            if status == "running":
                update_fields["started_at"] = datetime.now(timezone.utc).isoformat()
            elif status in ("completed", "failed"):
                update_fields["completed_at"] = datetime.now(timezone.utc).isoformat()

            if error:
                update_fields["error"] = error

            if metadata:
                import json as _json
                update_fields["summary"] = _json.dumps(metadata)

            # Validate all column names against allowlist to prevent SQL injection
            invalid_cols = set(update_fields.keys()) - _ALLOWED_UPDATE_COLUMNS
            if invalid_cols:
                raise ValueError(f"Invalid update columns: {invalid_cols}")

            set_clauses = ", ".join([f"{k} = :{k}" for k in update_fields])
            sql = text(f"UPDATE analyses SET {set_clauses} WHERE id = :scan_id")

            params = {"scan_id": scan_id, **update_fields}
            conn.execute(sql, params)
            conn.commit()

        return {"success": True, "scan_id": scan_id, "status": status}

    except Exception as e:
        logger.error(f"Failed to update analysis status: {e}")
        return {"success": False, "error": str(e)}


def _persist_findings(scan_id: str, file_ids: List[str], findings: List[Dict[str, Any]]) -> None:
    """Persist parsed findings and fix suggestions to the database.

    Uses synchronous DB access since Celery workers are sync.
    """
    try:
        from app.models.analysis import Severity

        engine = _get_sync_engine()

        with engine.connect() as conn:
            # Get code_file_id for the first file (simplified mapping)
            file_id = file_ids[0] if file_ids else None

            # Get analysis project_id
            analysis_result = conn.execute(
                text("SELECT project_id FROM analyses WHERE id = :scan_id"),
                {"scan_id": scan_id},
            )
            analysis_row = analysis_result.fetchone()
            project_id = analysis_row.project_id if analysis_row else None

            for finding_data in findings:
                finding_id = str(uuid.uuid4())

                # Normalize severity
                severity_raw = finding_data.get("severity", "medium").lower()
                if severity_raw not in ("critical", "high", "medium", "low", "info"):
                    severity_raw = "medium"

                code_snippet = finding_data.get("code_snippet", "")
                line_start = finding_data.get("line_number", finding_data.get("line_start", 0))
                line_end = finding_data.get("line_end", line_start)

                conn.execute(
                    text("""
                        INSERT INTO findings (id, code_file_id, project_id, analysis_id,
                            analyzer_type, vulnerability_type, severity, title, description,
                            cwe_id, cvss_score, file_path, line_start, line_end,
                            code_snippet, status, confidence, finding_metadata)
                        VALUES (:id, :code_file_id, :project_id, :analysis_id,
                            :analyzer_type, :vulnerability_type, :severity, :title, :description,
                            :cwe_id, :cvss_score, :file_path, :line_start, :line_end,
                            :code_snippet, :status, :confidence, :finding_metadata)
                    """),
                    {
                        "id": finding_id,
                        "code_file_id": file_id,
                        "project_id": project_id,
                        "analysis_id": scan_id,
                        "analyzer_type": finding_data.get("analyzer_type", "sast"),
                        "vulnerability_type": finding_data.get("vulnerability_type", "Unknown"),
                        "severity": severity_raw,
                        "title": finding_data.get("title", finding_data.get("vulnerability_type", "Unknown Vulnerability")),
                        "description": finding_data.get("description", finding_data.get("explanation", "")),
                        "cwe_id": finding_data.get("cwe_id"),
                        "cvss_score": str(finding_data.get("cvss_score", "")) if finding_data.get("cvss_score") else None,
                        "file_path": finding_data.get("file_path", "unknown"),
                        "line_start": line_start,
                        "line_end": line_end,
                        "code_snippet": code_snippet,
                        "status": "new",
                        "confidence": int(finding_data.get("confidence", 0.7) * 100) if isinstance(finding_data.get("confidence"), float) else finding_data.get("confidence", 100),
                        "finding_metadata": json.dumps({
                            k: v for k, v in finding_data.items()
                            if k not in ("vulnerability_type", "severity", "title", "description",
                                        "cwe_id", "file_path", "line_start", "line_end",
                                        "code_snippet", "confidence", "analyzer_type", "cvss_score")
                        }),
                    },
                )

                # Persist fix suggestion if present
                fix_data = finding_data.get("fix_suggestion")
                if fix_data:
                    fix_id = str(uuid.uuid4())
                    conn.execute(
                        text("""
                            INSERT INTO fix_suggestions (id, finding_id, title, description,
                                priority, code_before, code_after, language)
                            VALUES (:id, :finding_id, :title, :description,
                                :priority, :code_before, :code_after, :language)
                        """),
                        {
                            "id": fix_id,
                            "finding_id": finding_id,
                            "title": f"Fix for {finding_data.get('vulnerability_type', 'Unknown')}",
                            "description": fix_data.get("explanation", ""),
                            "priority": 1,
                            "code_before": fix_data.get("original_code", code_snippet),
                            "code_after": fix_data.get("fixed_code", ""),
                            "language": finding_data.get("language", "python"),
                        },
                    )

            conn.commit()

        logger.info(f"Persisted {len(findings)} findings for scan {scan_id}")

    except Exception as e:
        logger.error(f"Failed to persist findings: {e}")


def _parse_raw_output(raw_output: str) -> List[Dict[str, Any]]:
    """Try to parse findings from raw container output when JSON parsing fails."""
    findings = []
    for line in raw_output.split("\n"):
        line = line.strip()
        if line.startswith("{") and '"vulnerability_type"' in line:
            try:
                finding = json.loads(line)
                findings.append(finding)
            except json.JSONDecodeError:
                continue
    return findings