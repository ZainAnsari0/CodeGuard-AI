"""CodeGuard AI - Scan Tasks
Celery tasks for running security scans using direct AST analysis.

Scans run in-process using the Python AST scanner and JS Acorn scanner.
No Docker containers are used — code is only parsed (never executed).

Workflow:
  1. Create temporary workspace for the scan
  2. Run Python AST scanner on .py files (in-process)
  3. Run JavaScript Acorn scanner on .js files (in-process, via subprocess)
  4. Run AI fallback chain for explanation and fix generation
  5. Persist findings to the database
  6. Clean up temporary workspace
"""

import json
import logging
import os
import re
import shutil
import uuid
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, TypedDict, NotRequired

class FindingDict(TypedDict):
    vulnerability_type: str
    severity: str
    title: str
    description: str
    analyzer_type: str
    cwe_id: NotRequired[Optional[int]]
    cvss_score: NotRequired[Optional[float]]
    file_path: str
    line_start: NotRequired[int]
    line_end: NotRequired[int]
    line_number: NotRequired[int]
    code_snippet: str
    status: NotRequired[str]
    confidence: NotRequired[Optional[float]]
    finding_metadata: NotRequired[Optional[Dict[str, Any]]]
    explanation: NotRequired[Optional[str]]
    explanation_provider: NotRequired[Optional[str]]


from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from app.models.system_event import SystemEvent

from app.tasks.celery_app import celery_app
from app.core.config import settings
from app.ai.fallback_chain import ai_chain
from app.ai.prompts.manager import PromptManager
from app.ai.parser import LLMOutputParser
from app.services.temp_workspace import workspace_service
from app.services.ast_validators import ast_validator
from app.services.ai_enrichment_service import ai_enrichment_service

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
            db_url = parsed.render_as_string(hide_password=False)
        else:
            db_url = parsed.render_as_string(hide_password=False)

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


def _increment_scan_progress(scan_id: str):
    """Increment the files_completed count in the analysis metadata."""
    try:
        engine = _get_sync_engine()
        with engine.connect() as conn:
            res = conn.execute(
                text("SELECT analysis_metadata FROM analyses WHERE id = :scan_id"),
                {"scan_id": scan_id}
            )
            row = res.fetchone()
            if row and row[0]:
                meta_str = row[0]
                meta = json.loads(meta_str) if isinstance(meta_str, str) else meta_str
                meta["files_completed"] = meta.get("files_completed", 0) + 1
                conn.execute(
                    text("UPDATE analyses SET analysis_metadata = :meta WHERE id = :scan_id"),
                    {"meta": json.dumps(meta), "scan_id": scan_id}
                )
                conn.commit()
    except Exception as e:
        logger.error(f"Failed to increment scan progress: {e}")


def _log_system_event_sync(
    event_type: str,
    severity: str,
    message: str,
    user_id: Optional[str] = None,
    metadata: Optional[dict] = None
):
    """Log a system event synchronously from a Celery task."""
    try:
        engine = _get_sync_engine()
        with Session(engine) as session:
            event = SystemEvent(
                id=str(uuid.uuid4()),
                event_type=event_type,
                severity=severity,
                user_id=user_id,
                message=message,
                metadata_=metadata,
                created_at=datetime.now(timezone.utc),
            )
            session.add(event)
            session.commit()
    except Exception as e:
        logger.error(f"Failed to log system event sync: {e}", exc_info=True)


# ---------------------------------------------------------------------------
# Regex-based vulnerability patterns for rule-based analysis when no AI
# providers are available. These cover the most critical CWEs.
# ---------------------------------------------------------------------------
_VULN_PATTERNS = [
    # SQL Injection (CWE-89)
    {
        "pattern": re.compile(
            r"SELECT\s+.*?\$\{[^}]+\}"
            r"|INSERT\s+.*?\$\{[^}]+\}"
            r"|UPDATE\s+.*?\$\{[^}]+\}"
            r"|DELETE\s+.*?\$\{[^}]+\}"
            r"|SELECT\s+.*?'\s*\+\s*\w+\s*\+\s*'"
            r"|SELECT\s+.*?\.format\s*\("
            r"|SELECT\s+.*?%\([^)]+\)[sd]",
            re.IGNORECASE | re.DOTALL,
        ),
        "vulnerability_type": "SQL Injection",
        "cwe_id": "CWE-89",
        "severity": "critical",
        "explanation": "User input is concatenated directly into a SQL query string, allowing an attacker to modify the intended SQL command.",
        "remediation": "Use parameterized queries (prepared statements) instead of string concatenation or template literals.",
    },
    # Hardcoded Credentials (CWE-798)
    {
        "pattern": re.compile(
            r"(?:password|passwd|secret|api_key|apikey|token|auth_key)\s*[:=]\s*[\"'][^\"']{4,}[\"']",
            re.IGNORECASE,
        ),
        "vulnerability_type": "Hardcoded Credentials",
        "cwe_id": "CWE-798",
        "severity": "high",
        "explanation": "Hardcoded secrets embedded in source code are accessible to anyone with access to the code repository.",
        "remediation": "Store secrets in environment variables or a secrets manager. Never commit credentials to source control.",
    },
    # Cross-Site Scripting (CWE-79)
    {
        "pattern": re.compile(
            r"\.innerHTML\s*=\s*.*?(?:req|request|query|params|input|user)"
            r"|document\.write\s*\(.*?(?:req|request|query|params|input|user)",
            re.IGNORECASE,
        ),
        "vulnerability_type": "Cross-Site Scripting (XSS)",
        "cwe_id": "CWE-79",
        "severity": "high",
        "explanation": "User-controlled data is inserted into HTML without proper escaping, allowing script injection.",
        "remediation": "Escape all user-supplied data before rendering in HTML. Use textContent instead of innerHTML.",
    },
    # Code Injection (CWE-94)
    {
        "pattern": re.compile(
            r"\beval\s*\(\s*.*?(?:req|request|query|params|input|user|body)",
            re.IGNORECASE,
        ),
        "vulnerability_type": "Code Injection",
        "cwe_id": "CWE-94",
        "severity": "critical",
        "explanation": "User input is passed to eval(), allowing arbitrary code execution.",
        "remediation": "Never use eval() with user-controlled input. Use JSON.parse() for data or Function() with strict allowlisting.",
    },
    # Command Injection (CWE-78)
    {
        "pattern": re.compile(
            r"(?:exec|execSync|spawn|execFile)\s*\(\s*.*?(?:req|request|query|params|input|user|body)",
            re.IGNORECASE,
        ),
        "vulnerability_type": "Command Injection",
        "cwe_id": "CWE-78",
        "severity": "critical",
        "explanation": "User input is passed to a system command execution function, allowing arbitrary command injection.",
        "remediation": "Never pass user input directly to shell commands. Use allowlisted inputs or parameterized APIs.",
    },
]


async def _run_ai_analysis(file_id: str, file_path: str, content: str, language: str) -> List[FindingDict]:
    """Analyze a single file using the AI fallback chain.

    Uses AIEnrichmentService for PromptCache-backed analysis.
    Returns a list of finding dicts suitable for _persist_findings().
    """
    prompt_manager = PromptManager()
    parser = LLMOutputParser()

    prompt = prompt_manager.render_template(
        "vulnerability_analysis",
        {
            "code_snippet": content,
            "language": language,
            "file_path": file_path,
        },
    )

    # Check prompt cache before making the AI call
    model = getattr(settings, "DEFAULT_MODEL", "llama3:8b")
    cached = await ai_enrichment_service.cache.get("vulnerability_analysis", prompt, model)
    if cached:
        logger.info(f"AI analysis cache hit for {file_path}")
        findings = cached.get("findings", [])
        for f in findings:
            f["analyzer_type"] = f.get("analyzer_type", "ai")
            f["file_path"] = file_path
        return findings

    ai_result = await ai_chain.generate(prompt=prompt)
    raw_response = ai_result.get("response", "")
    provider_used = ai_result.get("provider_used", "unknown")
    logger.info(f"AI response from {provider_used} for {file_path}: {raw_response[:200]}...")

    scan_result = parser.parse_vulnerability_analysis(raw_response)
    logger.info(f"Parsed {len(scan_result.findings)} findings from AI for {file_path}")

    findings = []
    for pf in scan_result.findings:
        finding_dict = pf.model_dump()
        finding_dict["analyzer_type"] = "ai"
        finding_dict["file_path"] = file_path
        findings.append(finding_dict)

    # Cache the AI analysis result
    await ai_enrichment_service.cache.set(
        "vulnerability_analysis", prompt, model,
        {"findings": findings, "provider_used": provider_used},
    )

    return findings


async def _enrich_sast_finding_with_ai(
    finding: FindingDict,
    content: str,
    language: str,
) -> FindingDict:
    """Enrich a single SAST finding with AI-generated explanation and fix.

    Uses AIEnrichmentService for consistent caching and provider fallback.
    If the AI chain is unavailable, the finding is returned unchanged
    (the SAST engine's built-in remediation is already useful).
    """
    try:
        vuln_type = finding.get("vulnerability_type", "Unknown")
        severity = str(finding.get("severity", "high"))
        cwe_id = finding.get("cwe_id", "")
        code_snippet = finding.get("code_snippet", "")

        # Generate explanation via the enrichment service (uses PromptCache)
        explanation_data, provider = await ai_enrichment_service.generate_explanation(
            vulnerability_type=vuln_type,
            severity=severity,
            cwe_id=cwe_id,
            code_snippet=content or code_snippet,
            language=language,
        )

        # Merge AI explanation into the finding
        if explanation_data.get("description"):
            finding["description"] = explanation_data["description"]
        if explanation_data.get("remediation"):
            finding["remediation"] = explanation_data["remediation"]

        # Store the full explanation as JSON for persistence
        finding["ai_explanation"] = explanation_data
        finding["ai_enriched"] = True
        finding["ai_provider"] = provider

        # Generate fix for critical/high SAST findings
        if severity.lower() in ("critical", "high"):
            try:
                fix_data, fix_provider = await ai_enrichment_service.generate_fix(
                    vulnerability_type=vuln_type,
                    severity=severity,
                    cwe_id=cwe_id,
                    language=language,
                    original_code=code_snippet,
                    explanation=explanation_data.get("remediation", ""),
                )
                finding["fix_suggestion"] = fix_data
            except Exception as e:
                logger.warning(f"Fix generation failed for SAST finding: {e}")

        logger.info(
            f"AI enriched SAST finding: {vuln_type} in {finding.get('file_path')} "
            f"(provider={provider})"
        )

    except Exception as e:
        logger.warning(f"AI enrichment failed for SAST finding: {e}")

    return finding


def _is_false_positive_credential(match_text: str, full_content: str, match_start: int) -> bool:
    """Check if a hardcoded-credential regex match is a false positive.

    Filters out:
      - SQL context: 'password = ${password}' inside SQL template literals
      - Template expressions: quoted values containing ${...} interpolation
      - Parameterized placeholders: password = :password (SQL named params)

    Returns True if this match should be suppressed (it's a false positive).
    """
    # 1. If the quoted value contains template literal interpolation, it's dynamic
    if "${" in match_text or "#{" in match_text:
        return True

    # 2. Check surrounding context for SQL keywords — if the match is inside a
    #    SQL statement, the quoted value is a SQL string literal, not a credential
    #    e.g., AND password = '...' inside a SELECT/INSERT/UPDATE/DELETE
    context_window = 300  # chars before match to check for SQL keywords
    preceding = full_content[max(0, match_start - context_window):match_start]
    sql_keywords = re.compile(
        r'\b(?:SELECT|INSERT|INTO|UPDATE|DELETE|FROM|WHERE|SET|VALUES|AND|OR)\b',
        re.IGNORECASE,
    )
    if sql_keywords.search(preceding):
        return True

    return False


def _regex_analysis(content: str, file_path: str, language: str) -> List[FindingDict]:
    """Run regex-based vulnerability detection as a local fallback.

    Used when no AI providers (cloud or Ollama) are reachable.
    """
    findings = []
    seen_types = set()

    for vpat in _VULN_PATTERNS:
        match = vpat["pattern"].search(content)
        if match and vpat["vulnerability_type"] not in seen_types:
            # Filter false positives for hardcoded credential detections
            if vpat["vulnerability_type"] == "Hardcoded Credentials":
                if _is_false_positive_credential(match.group(0), content, match.start()):
                    continue

            seen_types.add(vpat["vulnerability_type"])
            line_no = content[:match.start()].count("\n") + 1
            lines = content.split("\n")
            snippet_start = max(0, line_no - 2)
            snippet_end = min(len(lines), line_no + 2)
            code_snippet = "\n".join(lines[snippet_start:snippet_end])

            findings.append({
                "vulnerability_type": vpat["vulnerability_type"],
                "severity": vpat["severity"],
                "cwe_id": vpat["cwe_id"],
                "file_path": file_path,
                "line_number": line_no,
                "line_start": line_no,
                "line_end": line_no + 1,
                "code_snippet": code_snippet,
                "explanation": vpat["explanation"],
                "remediation": vpat["remediation"],
                "confidence": 0.85,
                "analyzer_type": "regex",
                "title": vpat["vulnerability_type"],
                "description": vpat["explanation"],
            })

    return findings


def _run_python_scanner(file_path: str, content: str) -> List[FindingDict]:
    """Run the Python AST scanner on a file's content directly in-process.

    This replaces the previous Docker container-based scanning.
    The scanner analyzes the AST of the source code — it never executes
    the code.
    """
    import sys as _sys
    # Ensure backend/ root is on sys.path so 'scanner' package is importable
    # regardless of the working directory set by the process manager (e.g. Render).
    _backend_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _backend_root not in _sys.path:
        _sys.path.insert(0, _backend_root)
    from scanner.python_scanner import PythonScanner

    scanner = PythonScanner()
    findings = scanner.scan_content(content, file_path)
    return findings


def _run_js_scanner(file_path: str, content: str) -> List[FindingDict]:
    """Run the SAST-based JavaScript scanner on a file's content.

    Pipeline: SAST engine (taint tracking + AST patterns) → legacy Acorn scanner → regex.

    The SAST engine (scanner/sast/index.js) provides forward taint analysis
    with data-flow traces, catching injection vulnerabilities that pattern
    matching alone misses. Falls back to legacy js_scanner.js if the SAST
    engine is unavailable, and to regex if Node.js is missing.
    """
    import subprocess

    sast_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "scanner", "sast", "index.js"
    )

    if os.path.exists(sast_path):
        import tempfile
        tmp_dir = tempfile.mkdtemp(prefix="codeguard_sast_scan_")
        try:
            tmp_file = os.path.join(tmp_dir, os.path.basename(file_path))
            with open(tmp_file, "w", errors="replace") as f:
                f.write(content)

            try:
                result = subprocess.run(
                    ["node", sast_path, tmp_file],
                    capture_output=True,
                    text=True,
                    timeout=60,
                )

                if result.returncode == 0:
                    report = json.loads(result.stdout)
                    findings = report.get("findings", [])
                    # Remap file paths from temp path back to original
                    for finding in findings:
                        if "file_path" in finding:
                            finding["file_path"] = file_path
                    logger.info(
                        f"SAST engine found {len(findings)} findings in {file_path} "
                        f"(scopes={report.get('scopes_analyzed', '?')}, "
                        f"taint_sources={report.get('taint_sources_detected', '?')})"
                    )
                    return findings
                else:
                    logger.warning(f"SAST engine returned non-zero exit code: {result.returncode}")
                    logger.debug(f"SAST stderr: {result.stderr[:500]}")
                    # Fall through to legacy scanner

            except FileNotFoundError:
                logger.warning("Node.js not available for SAST scanning")
                # Fall through to legacy scanner
            except subprocess.TimeoutExpired:
                logger.warning(f"SAST engine timed out for {file_path}")
                # Fall through to legacy scanner
            except json.JSONDecodeError:
                logger.warning(f"SAST engine returned invalid JSON for {file_path}")
                # Fall through to legacy scanner

        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    # Fallback: legacy Acorn-based scanner
    legacy_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "scanner", "js_scanner.js"
    )

    if os.path.exists(legacy_path):
        import tempfile
        tmp_dir = tempfile.mkdtemp(prefix="codeguard_js_scan_")
        try:
            tmp_file = os.path.join(tmp_dir, os.path.basename(file_path))
            with open(tmp_file, "w", errors="replace") as f:
                f.write(content)

            try:
                result = subprocess.run(
                    ["node", legacy_path, tmp_file],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

                if result.returncode != 0:
                    logger.warning(f"Legacy JS scanner returned non-zero exit code: {result.returncode}")
                    return _regex_analysis(content, file_path, "javascript")

                findings = json.loads(result.stdout)
                if isinstance(findings, dict) and "findings" in findings:
                    findings = findings["findings"]

                for finding in findings:
                    if "file_path" in finding:
                        finding["file_path"] = file_path

                return findings

            except FileNotFoundError:
                logger.warning("Node.js not available for JS scanning, falling back to regex")
                return _regex_analysis(content, file_path, "javascript")
            except subprocess.TimeoutExpired:
                logger.warning(f"Legacy JS scanner timed out for {file_path}")
                return _regex_analysis(content, file_path, "javascript")
            except json.JSONDecodeError:
                logger.warning(f"Legacy JS scanner returned invalid JSON for {file_path}")
                return _regex_analysis(content, file_path, "javascript")

        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    # Final fallback: regex analysis
    logger.warning(f"No JS scanner available for {file_path}, using regex analysis")
    return _regex_analysis(content, file_path, "javascript")


async def _run_scan_async(
    scan_id: str,
    file_ids: List[str],
    user_id: str,
    upload_dir: str,
    scan_config: Dict[str, Any],
) -> Dict[str, Any]:
    """Async entry point for the full scan pipeline.

    Runs both the in-process AST scanner and the AI analysis pass within
    a single event loop.
    """
    # Fetch all file metadata once to deduplicate DB queries
    file_records = []
    engine = _get_sync_engine()
    with engine.connect() as conn:
        for fid in file_ids:
            file_res = conn.execute(
                text("SELECT id, file_path, content, language FROM code_files WHERE id = :fid"),
                {"fid": fid},
            )
            file_row = file_res.fetchone()
            if file_row:
                file_records.append({
                    "id": file_row[0],
                    "file_path": file_row[1],
                    "content": file_row[2],
                    "language": file_row[3],
                })

    # --- Stage 1: In-process AST scanning ---
    all_ast_findings: List[Dict[str, Any]] = []

    for file_row in file_records:
        fid = file_row["id"]
        file_path = file_row["file_path"]
        content = file_row["content"]
        language = file_row["language"]
        logger.info(f"Running AST scanner on {file_path} (language={language})")

        if language.lower() in ("python", "py"):
            try:
                findings = _run_python_scanner(file_path, content)
                all_ast_findings.extend(findings)
                logger.info(f"Python scanner found {len(findings)} findings in {file_path}")
            except Exception as e:
                logger.warning(f"Python scanner failed for {file_path}: {e}")
                # Fall back to regex analysis
                regex_findings = _regex_analysis(content, file_path, "python")
                all_ast_findings.extend(regex_findings)

        elif language.lower() in ("javascript", "js", "typescript", "ts"):
            try:
                findings = _run_js_scanner(file_path, content)
                all_ast_findings.extend(findings)
                logger.info(f"JS scanner found {len(findings)} findings in {file_path}")
            except Exception as e:
                logger.warning(f"JS scanner failed for {file_path}: {e}")
                regex_findings = _regex_analysis(content, file_path, "javascript")
                all_ast_findings.extend(regex_findings)

        else:
            # Unknown language — use regex analysis as baseline
            regex_findings = _regex_analysis(content, file_path, language)
            all_ast_findings.extend(regex_findings)

    # Persist AST findings
    _persist_findings(scan_id, file_ids, all_ast_findings)

    # --- Stage 2: AI-powered analysis ---
    # Two purposes:
    #   a) General AI code review (catches things SAST/regex may miss)
    #   b) Enrich SAST findings with detailed AI explanations
    ai_findings: List[Dict[str, Any]] = []
    prompt_manager = PromptManager()
    parser = LLMOutputParser()

    # Check whether any AI provider is available
    provider_status = ai_chain.get_provider_status()
    ai_available = any(provider_status.values())
    logger.info(f"AI provider availability: {provider_status}")

    # 2a: Enrich SAST findings with AI explanations
    sast_findings = [f for f in all_ast_findings if f.get("analyzer_type") == "sast-js"]
    if ai_available and sast_findings:
        logger.info(f"Enriching {len(sast_findings)} SAST findings with AI explanations")
        # Build a file_id → (content, language) map for AI enrichment
        file_content_map = {
            fr["file_path"]: (fr["content"], fr["language"]) for fr in file_records
        }

        for finding in sast_findings:
            try:
                fp = finding.get("file_path", "")
                file_data = file_content_map.get(fp, ("", "javascript"))
                await _enrich_sast_finding_with_ai(
                    finding,
                    content=file_data[0],
                    language=file_data[1],
                )
            except Exception as e:
                logger.debug(f"AI enrichment failed for one finding: {e}")
        # Update persisted findings with AI-enriched data
        _update_sast_findings_with_ai(scan_id, sast_findings)

    # 2b: General AI code review for all files
    for file_row in file_records:
        fid = file_row["id"]
        file_path = file_row["file_path"]
        content = file_row["content"]
        language = file_row["language"]
        logger.info(f"Analyzing file {file_path} with AI (available={ai_available})...")

        if ai_available:
            try:
                file_ai_findings = await _run_ai_analysis(fid, file_path, content, language)
                ai_findings.extend(file_ai_findings)
            except Exception as ai_err:
                logger.error(f"AI analysis failed for file {fid}: {ai_err}", exc_info=True)
                logger.info(f"Falling back to regex analysis for {file_path}")
                regex_findings = _regex_analysis(content, file_path, language)
                ai_findings.extend(regex_findings)
        else:
            logger.info(f"No AI providers available, using regex analysis for {file_path}")
            regex_findings = _regex_analysis(content, file_path, language)
            ai_findings.extend(regex_findings)

        _increment_scan_progress(scan_id)

    if ai_findings:
        logger.info(f"Persisting {len(ai_findings)} AI/regex-detected findings")
        _persist_findings(scan_id, file_ids, ai_findings)
    else:
        logger.info("No AI or regex findings detected")

    total_findings_count = len(all_ast_findings) + len(ai_findings)
    sast_count = len(sast_findings)
    legacy_ast_count = len(all_ast_findings) - sast_count

    _update_analysis_status(
        scan_id,
        "completed",
        metadata={
            "total_findings": total_findings_count,
            "sast_findings": sast_count,
            "ast_findings": legacy_ast_count,
            "ai_findings": len(ai_findings),
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "scan_method": "sast+taint" if sast_count > 0 else "direct_ast",
        },
    )

    return {
        "status": "completed",
        "scan_id": scan_id,
        "total_findings": total_findings_count,
        "sast_findings": sast_count,
        "ast_findings": legacy_ast_count,
        "ai_findings": len(ai_findings),
    }


def _update_sast_findings_with_ai(scan_id: str, sast_findings: List[Dict[str, Any]]) -> None:
    """Update SAST findings in the database with AI-enriched explanations.

    After the AI fallback chain provides detailed explanations for SAST
    findings, this function updates the corresponding database rows so
    the frontend can display AI-generated descriptions alongside the
    SAST data-flow traces.

    Now also persists explanation JSON, explanation_provider, and
    explanation_generated_at on the findings table, and ast_validated,
    validation_warnings, confidence on the fix_suggestions table.
    """
    if not sast_findings:
        return

    try:
        engine = _get_sync_engine()
        with engine.connect() as conn:
            for finding in sast_findings:
                if not finding.get("ai_enriched"):
                    continue

                # Find the finding by matching on scan_id, file_path, line, and CWE
                file_path = finding.get("file_path", "")
                line_start = finding.get("line_start", finding.get("line_number", 0))
                cwe_id = finding.get("cwe_id", "")

                result = conn.execute(
                    text(
                        "SELECT id FROM findings "
                        "WHERE analysis_id = :scan_id "
                        "AND file_path = :file_path "
                        "AND line_start = :line_start "
                        "AND cwe_id = :cwe_id "
                        "AND analyzer_type = 'sast-js' "
                        "LIMIT 1"
                    ),
                    {
                        "scan_id": scan_id,
                        "file_path": file_path,
                        "line_start": line_start,
                        "cwe_id": cwe_id,
                    },
                )
                row = result.fetchone()
                if not row:
                    continue

                finding_id = row.id

                # Update description + explanation fields
                update_fields = {}
                if finding.get("description"):
                    update_fields["description"] = finding["description"]

                # Persist AI explanation JSON
                if finding.get("ai_explanation"):
                    update_fields["explanation"] = json.dumps(finding["ai_explanation"])
                if finding.get("ai_provider"):
                    update_fields["explanation_provider"] = finding["ai_provider"]
                if finding.get("ai_enriched"):
                    update_fields["explanation_generated_at"] = datetime.now(timezone.utc).isoformat()

                if update_fields:
                    set_clause = ", ".join([f"{k} = :{k}" for k in update_fields])
                    update_fields["finding_id"] = finding_id
                    conn.execute(
                        text(f"UPDATE findings SET {set_clause} WHERE id = :finding_id"),
                        update_fields,
                    )

                # Store fix suggestion if AI provided one (now with validation fields)
                fix_data = finding.get("fix_suggestion")
                if fix_data and isinstance(fix_data, dict):
                    # Check if a fix suggestion already exists for this finding
                    existing_fix = conn.execute(
                        text("SELECT id FROM fix_suggestions WHERE finding_id = :fid"),
                        {"fid": finding_id},
                    ).fetchone()

                    if not existing_fix:
                        conn.execute(
                            text(
                                "INSERT INTO fix_suggestions "
                                "(id, finding_id, title, description, "
                                "priority, code_before, code_after, language, "
                                "ast_validated, validation_warnings, confidence) "
                                "VALUES (:id, :finding_id, :title, :description, "
                                ":priority, :code_before, :code_after, :language, "
                                ":ast_validated, :validation_warnings, :confidence)"
                            ),
                            {
                                "id": str(uuid.uuid4()),
                                "finding_id": finding_id,
                                "title": f"AI Fix for {finding.get('vulnerability_type', 'Unknown')}",
                                "description": fix_data.get("explanation", ""),
                                "priority": 1,
                                "code_before": fix_data.get("original_code", finding.get("code_snippet", "")),
                                "code_after": fix_data.get("fixed_code", ""),
                                "language": "javascript",
                                "ast_validated": fix_data.get("ast_validated"),
                                "validation_warnings": json.dumps(fix_data.get("validation_warnings")) if fix_data.get("validation_warnings") else None,
                                "confidence": str(fix_data.get("confidence", "")) if fix_data.get("confidence") else None,
                            },
                        )

            conn.commit()

        logger.info(f"Updated {len(sast_findings)} SAST findings with AI enrichment")

    except Exception as e:
        logger.error(f"Failed to update SAST findings with AI data: {e}")


@celery_app.task(name="run_scan_task", bind=True, max_retries=2)
def run_scan_task(self, scan_id: str, file_ids: List[str], user_id: str) -> Dict[str, Any]:
    """Run a security scan using in-process AST analysis.

    Task lifecycle: PENDING -> RUNNING -> COMPLETED/FAILED

    This task performs static analysis only — code is parsed via AST,
    never executed. No Docker containers are used.

    Args:
        self: Celery task instance (injected by bind=True)
        scan_id: Analysis ID for this scan
        file_ids: List of CodeFile IDs to scan
        user_id: ID of the user who initiated the scan
    """
    logger.info(f"Starting scan task for {scan_id} with {len(file_ids)} files")

    try:
        _update_analysis_status(scan_id, "running")
        _log_system_event_sync(
            event_type="scan_started",
            severity="info",
            message=f"Security scan {scan_id} started.",
            user_id=user_id,
            metadata={"scan_id": scan_id, "file_count": len(file_ids)}
        )
    except Exception as e:
        logger.error(f"Failed to set scan status to running: {e}")

    try:
        # Verify workspace exists (files were uploaded here)
        upload_dir = workspace_service.get_workspace_path(scan_id)
        if not upload_dir:
            # Try fallback upload directory
            base_upload_dir = getattr(settings, "UPLOAD_DIR", "/tmp/codeguard_uploads")
            upload_dir = os.path.join(base_upload_dir, scan_id)
            if not os.path.isdir(upload_dir):
                logger.error(f"Upload directory not found: {upload_dir}")
                _update_analysis_status(scan_id, "failed", error="Upload directory not found")
                _log_system_event_sync(
                    event_type="scan_failed",
                    severity="error",
                    message=f"Security scan {scan_id} failed: Upload directory not found.",
                    user_id=user_id,
                    metadata={"scan_id": scan_id, "error": "Upload directory not found"}
                )
                return {"status": "failed", "error": "Upload directory not found"}

        scan_config = {
            "file_ids": file_ids,
            "user_id": user_id,
            "scan_id": scan_id,
        }

        # Run the entire async pipeline in a single event loop
        result = asyncio.run(_run_scan_async(scan_id, file_ids, user_id, upload_dir, scan_config))
        _log_system_event_sync(
            event_type="scan_completed",
            severity="info",
            message=f"Security scan {scan_id} completed successfully.",
            user_id=user_id,
            metadata={"scan_id": scan_id, **result}
        )
        return result

    except Exception as e:
        logger.error(f"Scan task failed: {e}", exc_info=True)
        if self.request.retries < self.max_retries:
            _log_system_event_sync(
                event_type="scan_failed",
                severity="warning",
                message=f"Security scan {scan_id} failed on attempt {self.request.retries + 1}. Retrying...",
                user_id=user_id,
                metadata={"scan_id": scan_id, "error": str(e), "retry": True}
            )
            raise self.retry(exc=e, countdown=60)
        else:
            _update_analysis_status(scan_id, "failed", error=str(e)[:500])
            _log_system_event_sync(
                event_type="scan_failed",
                severity="error",
                message=f"Security scan {scan_id} failed: {str(e)[:200]}",
                user_id=user_id,
                metadata={"scan_id": scan_id, "error": str(e)}
            )
    finally:
        # Clean up temporary workspace to prevent disk space accumulation
        workspace_service.cleanup_workspace(scan_id)


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
                update_fields["summary"] = json.dumps(metadata)

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


def _persist_findings(scan_id: str, file_ids: List[str], findings: List[FindingDict]) -> None:
    """Persist parsed findings and fix suggestions to the database.

    Uses synchronous DB access since Celery workers are sync.
    """
    try:
        from app.models.analysis import Severity

        engine = _get_sync_engine()

        with engine.connect() as conn:
            # Build file_path -> code_file_id mapping for correct file association
            file_id_map = {}
            for fid in file_ids:
                file_result = conn.execute(
                    text("SELECT id, file_path FROM code_files WHERE id = :fid"),
                    {"fid": fid},
                )
                file_row = file_result.fetchone()
                if file_row:
                    file_id_map[file_row.file_path] = file_row.id

            # Get analysis project_id
            analysis_result = conn.execute(
                text("SELECT project_id FROM analyses WHERE id = :scan_id"),
                {"scan_id": scan_id},
            )
            analysis_row = analysis_result.fetchone()
            project_id = analysis_row.project_id if analysis_row else None

            for finding_data in findings:
                finding_id = str(uuid.uuid4())

                # Normalize severity to the PostgreSQL enum value (lowercase)
                # The DB enum stores: 'critical', 'high', 'medium', 'low', 'info'
                severity_raw = finding_data.get("severity", "medium").lower()
                severity_map = {
                    "critical": "critical",
                    "high": "high",
                    "medium": "medium",
                    "low": "low",
                    "info": "info",
                }
                severity_db = severity_map.get(severity_raw, "medium")

                code_snippet = finding_data.get("code_snippet", "")
                line_start = finding_data.get("line_number", finding_data.get("line_start", 0))
                line_end = finding_data.get("line_end", line_start)

                # Match finding to its source file using file_path
                finding_file_path = finding_data.get("file_path", "")
                code_file_id = file_id_map.get(finding_file_path, file_ids[0] if file_ids else None)

                conn.execute(
                    text("""
                        INSERT INTO findings (id, code_file_id, project_id, analysis_id,
                            analyzer_type, vulnerability_type, severity, title, description,
                            cwe_id, cvss_score, file_path, line_start, line_end,
                            code_snippet, status, confidence, finding_metadata,
                            explanation, explanation_provider, explanation_generated_at)
                        VALUES (:id, :code_file_id, :project_id, :analysis_id,
                            :analyzer_type, :vulnerability_type, :severity, :title, :description,
                            :cwe_id, :cvss_score, :file_path, :line_start, :line_end,
                            :code_snippet, :status, :confidence, :finding_metadata,
                            :explanation, :explanation_provider, :explanation_generated_at)
                    """),
                    {
                        "id": finding_id,
                        "code_file_id": code_file_id,
                        "project_id": project_id,
                        "analysis_id": scan_id,
                        "analyzer_type": finding_data.get("analyzer_type", "sast"),
                        "vulnerability_type": finding_data.get("vulnerability_type", "Unknown"),
                        "severity": severity_db,
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
                                        "code_snippet", "confidence", "analyzer_type", "cvss_score",
                                        "ai_explanation", "ai_enriched", "ai_provider", "fix_suggestion")
                        }),
                        "explanation": json.dumps(finding_data.get("ai_explanation")) if finding_data.get("ai_explanation") else None,
                        "explanation_provider": finding_data.get("ai_provider"),
                        "explanation_generated_at": datetime.now(timezone.utc).isoformat() if finding_data.get("ai_enriched") else None,
                    },
                )

                # Persist fix suggestion if present
                fix_data = finding_data.get("fix_suggestion")
                if fix_data:
                    fix_id = str(uuid.uuid4())
                    conn.execute(
                        text("""
                            INSERT INTO fix_suggestions (id, finding_id, title, description,
                                priority, code_before, code_after, language,
                                ast_validated, validation_warnings, confidence)
                            VALUES (:id, :finding_id, :title, :description,
                                :priority, :code_before, :code_after, :language,
                                :ast_validated, :validation_warnings, :confidence)
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
                            "ast_validated": fix_data.get("ast_validated"),
                            "validation_warnings": json.dumps(fix_data.get("validation_warnings")) if fix_data.get("validation_warnings") else None,
                            "confidence": float(fix_data.get("confidence")) if fix_data.get("confidence") is not None else None,
                        },
                    )

            conn.commit()

        logger.info(f"Persisted {len(findings)} findings for scan {scan_id}")

    except Exception as e:
        logger.error(f"Failed to persist findings: {e}")


def _parse_raw_output(raw_output: str) -> List[FindingDict]:
    """Try to parse findings from raw scanner output when JSON parsing fails."""
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