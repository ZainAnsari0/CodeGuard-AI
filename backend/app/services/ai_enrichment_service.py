"""
CodeGuard AI - AI Enrichment Service
Unified service for AI-powered enrichment of findings: explanation generation,
fix generation, and AST validation.

Consolidates the enrichment logic previously scattered across:
  - scan_tasks.py (_enrich_sast_finding_with_ai, _run_ai_analysis)
  - scan_orchestrator.py (ScanOrchestrator._analyze_single_finding)

Uses PromptCache for deduplication, AIFallbackChain for resilient provider
selection, and ASTValidator for fix verification.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

from app.ai.fallback_chain import ai_chain
from app.ai.prompts.manager import PromptManager
from app.ai.parser import LLMOutputParser
from app.services.ast_validators import ast_validator
from app.services.cache import prompt_cache
from app.core.config import settings

logger = logging.getLogger(__name__)

AI_CONCURRENCY = getattr(settings, "AI_MAX_CONCURRENCY", 3)  # Max parallel LLM calls


class AIEnrichmentService:
    """Unified service for AI enrichment of findings.

    Provides a single entry point for both scan-time (batch) and
    on-demand (per-finding) enrichment, ensuring consistent caching,
    provider fallback, and validation behaviour.
    """

    def __init__(self):
        self.prompt_manager = PromptManager()
        self.parser = LLMOutputParser()
        self.cache = prompt_cache

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def generate_explanation(
        self,
        vulnerability_type: str,
        severity: str,
        cwe_id: str,
        code_snippet: str,
        language: str,
        model: Optional[str] = None,
    ) -> Tuple[Dict[str, Any], str]:
        """Generate a vulnerability explanation using the fallback chain.

        Checks PromptCache first; on cache miss, generates via AI and
        stores the result in the cache.

        Returns:
            (explanation_data, provider_used)
        """
        model = model or getattr(settings, "DEFAULT_MODEL", "llama3:8b")

        # Render prompt for cache key lookup
        rendered_prompt = self.prompt_manager.render_template(
            "explanation",
            {
                "vulnerability_type": vulnerability_type,
                "severity": severity,
                "cwe_id": cwe_id or "",
                "language": language,
                "code_snippet": (code_snippet or "")[:500],
            },
        )

        # Check cache
        cached = await self.cache.get("explanation", rendered_prompt, model)
        if cached:
            logger.info("Explanation cache hit for %s/%s", vulnerability_type, model)
            return cached, cached.get("provider_used", "cache")

        # Generate via AI fallback chain
        prompt = self.prompt_manager.render_template(
            "explanation",
            {
                "vulnerability_type": vulnerability_type,
                "severity": severity,
                "cwe_id": cwe_id or "",
                "language": language,
                "code_snippet": code_snippet or "",
            },
        )

        result = await ai_chain.generate(
            prompt=prompt,
            finding={
                "vulnerability_type": vulnerability_type,
                "severity": severity,
                "cwe_id": cwe_id,
            },
        )

        raw_response = result.get("response", "")
        provider_used = result.get("provider_used", "unknown")

        try:
            parsed = self.parser.parse_explanation(raw_response)
            explanation_data = parsed.model_dump() if hasattr(parsed, "model_dump") else parsed
        except Exception:
            explanation_data = {"raw_explanation": raw_response}

        explanation_data["provider_used"] = provider_used

        # Store in cache
        await self.cache.set("explanation", rendered_prompt, model, explanation_data)

        return explanation_data, provider_used

    async def generate_fix(
        self,
        vulnerability_type: str,
        severity: str,
        cwe_id: str,
        language: str,
        original_code: str,
        explanation: str,
        model: Optional[str] = None,
    ) -> Tuple[Dict[str, Any], str]:
        """Generate a fix suggestion with AST validation.

        Returns:
            (fix_data, provider_used)  where fix_data includes
            ast_validated and validation_warnings.
        """
        model = model or getattr(settings, "DEFAULT_MODEL", "llama3:8b")

        prompt = self.prompt_manager.render_template(
            "fix_generation",
            {
                "vulnerability_type": vulnerability_type,
                "severity": severity,
                "cwe_id": cwe_id or "",
                "language": language,
                "original_code": original_code,
                "explanation": explanation,
            },
        )

        result = await ai_chain.generate(
            prompt=prompt,
            finding={
                "vulnerability_type": vulnerability_type,
                "severity": severity,
                "cwe_id": cwe_id,
            },
        )

        raw_response = result.get("response", "")
        provider_used = result.get("provider_used", "unknown")

        try:
            parsed = self.parser.parse_fix_suggestion(raw_response, original_code=original_code)
            fix_data = parsed.model_dump() if hasattr(parsed, "model_dump") else parsed
        except Exception:
            fix_data = {
                "original_code": original_code,
                "fixed_code": "",
                "explanation": raw_response,
                "confidence": 0.0,
            }

        # AST validation
        fixed_code = fix_data.get("fixed_code", "")
        validation = ast_validator.validate_fix(
            original_code=original_code,
            fixed_code=fixed_code,
            language=language,
        )
        fix_data["ast_validated"] = validation["valid"]
        fix_data["validation_warnings"] = validation.get("warnings", [])

        return fix_data, provider_used

    async def enrich_finding(
        self,
        finding: Dict[str, Any],
        code_snippets: Optional[Dict[str, str]] = None,
        language: str = "python",
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Enrich a single finding dict with AI explanation and optional fix.

        Used by the scan pipeline (scan_tasks.py) for batch enrichment.
        Returns the finding dict with added keys:
          - 'ai_explanation': parsed ExplanationResult dict
          - 'fix_suggestion': parsed fix dict (for critical/high only)
          - 'ai_enriched': True
          - 'ai_provider': provider name
        """
        vuln_type = finding.get("vulnerability_type", "unknown")
        severity = finding.get("severity", "medium")
        cwe_id = finding.get("cwe_id", "")
        code_snippet = finding.get("code_snippet", "")
        file_path = finding.get("file_path", "")

        # Use full file content when available for better context
        if code_snippets and file_path in code_snippets:
            full_code = code_snippets[file_path]
        else:
            full_code = code_snippet

        # Generate explanation
        try:
            explanation_data, provider = await self.generate_explanation(
                vulnerability_type=vuln_type,
                severity=str(severity),
                cwe_id=cwe_id,
                code_snippet=full_code,
                language=language,
                model=model,
            )
            finding["ai_explanation"] = explanation_data
            finding["ai_enriched"] = True
            finding["ai_provider"] = provider
        except Exception as e:
            logger.warning("Explanation generation failed for %s: %s", vuln_type, e)
            return finding

        # Generate fix for critical/high severity findings
        severity_str = str(severity).lower()
        if severity_str in ("critical", "high"):
            try:
                fix_data, fix_provider = await self.generate_fix(
                    vulnerability_type=vuln_type,
                    severity=severity_str,
                    cwe_id=cwe_id,
                    language=language,
                    original_code=code_snippet,
                    explanation=explanation_data.get("remediation", ""),
                    model=model,
                )
                finding["fix_suggestion"] = fix_data
            except Exception as e:
                logger.warning("Fix generation failed for %s: %s", vuln_type, e)

        return finding

    async def enrich_findings_batch(
        self,
        findings: List[Dict[str, Any]],
        code_snippets: Optional[Dict[str, str]] = None,
        language: str = "python",
        model: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Enrich a batch of findings with bounded concurrency.

        Only enriches findings that don't already have ai_enriched=True.
        """
        model = model or getattr(settings, "DEFAULT_MODEL", "llama3:8b")
        semaphore = asyncio.Semaphore(AI_CONCURRENCY)

        async def _enrich_with_semaphore(finding: Dict[str, Any]) -> Dict[str, Any]:
            async with semaphore:
                return await self.enrich_finding(finding, code_snippets, language, model)

        # Only enrich findings that aren't already enriched
        to_enrich = [f for f in findings if not f.get("ai_enriched")]
        if not to_enrich:
            return findings

        tasks = [_enrich_with_semaphore(f) for f in to_enrich]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Replace enriched findings in the original list
        enriched_map = {}
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning("Batch enrichment failed for finding: %s", result)
            elif result is not None:
                key = (result.get("file_path"), result.get("line_start", result.get("line_number")), result.get("vulnerability_type"))
                enriched_map[key] = result

        final = []
        for f in findings:
            key = (f.get("file_path"), f.get("line_start", f.get("line_number")), f.get("vulnerability_type"))
            if key in enriched_map:
                final.append(enriched_map[key])
            else:
                final.append(f)

        return final

    async def enrich_finding_and_persist(
        self,
        finding_id: str,
        scan_id: str,
        db,
    ) -> Dict[str, Any]:
        """On-demand enrichment: fetch a finding from DB, enrich, persist, return.

        Uses AsyncSession for the API endpoint path.

        Returns:
            Dict with the enriched finding data including explanation and fix.
        """
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        from app.models.analysis import Finding, FixSuggestion
        import uuid

        stmt = select(Finding).where(
            Finding.id == finding_id,
            Finding.analysis_id == scan_id,
        ).options(selectinload(Finding.fix_suggestions))
        result = await db.execute(stmt)
        finding = result.scalar_one_or_none()

        if not finding:
            return {"error": "Finding not found"}

        # Check if already enriched
        already_has_explanation = finding.explanation is not None
        already_has_fix = len(finding.fix_suggestions) > 0

        # Determine language
        language = "python"
        if finding.finding_metadata and isinstance(finding.finding_metadata, dict):
            language = finding.finding_metadata.get("language", "python")
        elif finding.file_path:
            ext = finding.file_path.rsplit(".", 1)[-1].lower() if "." in finding.file_path else ""
            lang_map = {"py": "python", "js": "javascript", "ts": "typescript", "jsx": "javascript", "tsx": "typescript"}
            language = lang_map.get(ext, "python")

        # Generate explanation if missing
        if not already_has_explanation:
            try:
                explanation_data, provider = await self.generate_explanation(
                    vulnerability_type=finding.vulnerability_type,
                    severity=finding.severity.value if hasattr(finding.severity, "value") else str(finding.severity),
                    cwe_id=finding.cwe_id or "",
                    code_snippet=finding.code_snippet or "",
                    language=language,
                )
                # Persist explanation
                finding.explanation = json.dumps(explanation_data)
                finding.explanation_provider = provider
                finding.explanation_generated_at = datetime.now(timezone.utc)
            except Exception as e:
                logger.warning("On-demand explanation failed for %s: %s", finding_id, e)

        # Generate fix if missing and severity is critical/high
        severity_str = finding.severity.value if hasattr(finding.severity, "value") else str(finding.severity)
        if not already_has_fix and severity_str in ("critical", "high"):
            try:
                fix_data, fix_provider = await self.generate_fix(
                    vulnerability_type=finding.vulnerability_type,
                    severity=severity_str,
                    cwe_id=finding.cwe_id or "",
                    language=language,
                    original_code=finding.code_snippet or "",
                    explanation=finding.description or "",
                )

                fixed_code = fix_data.get("fixed_code", "")
                new_fix = FixSuggestion(
                    id=str(uuid.uuid4()),
                    finding_id=finding.id,
                    title=f"Fix for {finding.vulnerability_type}",
                    description=fix_data.get("explanation", ""),
                    priority=1,
                    code_before=fix_data.get("original_code", finding.code_snippet or ""),
                    code_after=fixed_code,
                    language=language,
                    ast_validated=fix_data.get("ast_validated"),
                    validation_warnings=fix_data.get("validation_warnings"),
                    confidence=float(fix_data.get("confidence")) if fix_data.get("confidence") else None,
                )
                db.add(new_fix)
            except Exception as e:
                logger.warning("On-demand fix generation failed for %s: %s", finding_id, e)

        await db.commit()
        await db.refresh(finding)

        # Build response
        explanation_parsed = None
        if finding.explanation:
            try:
                explanation_parsed = json.loads(finding.explanation) if isinstance(finding.explanation, str) else finding.explanation
            except (json.JSONDecodeError, TypeError):
                explanation_parsed = None

        fix_suggestions_data = []
        for fs in finding.fix_suggestions:
            fix_suggestions_data.append({
                "id": str(fs.id),
                "title": fs.title,
                "description": fs.description,
                "priority": fs.priority,
                "code_before": fs.code_before,
                "code_after": fs.code_after,
                "language": fs.language,
                "ast_validated": fs.ast_validated,
                "validation_warnings": fs.validation_warnings,
                "confidence": float(fs.confidence) if fs.confidence else None,
            })

        return {
            "id": str(finding.id),
            "vulnerability_type": finding.vulnerability_type,
            "severity": severity_str,
            "title": finding.title,
            "description": finding.description,
            "cwe_id": finding.cwe_id,
            "file_path": finding.file_path,
            "line_start": finding.line_start,
            "line_end": finding.line_end,
            "code_snippet": finding.code_snippet,
            "status": finding.status,
            "confidence": finding.confidence,
            "explanation": explanation_parsed,
            "explanation_provider": finding.explanation_provider,
            "fix_suggestions": fix_suggestions_data,
            "explanation_cached": already_has_explanation,
        }


# Singleton instance
ai_enrichment_service = AIEnrichmentService()