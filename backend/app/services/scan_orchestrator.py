"""
CodeGuard AI - Scan Orchestrator
Coordinates the complete scan pipeline: upload -> AST -> AI -> DB.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from app.ai.prompts.manager import PromptManager
from app.ai.parser import LLMOutputParser
from app.ai.fallback_chain import ai_chain
from app.services.ast_validators import ast_validator
from app.services.cache import prompt_cache
from app.core.config import settings

logger = logging.getLogger(__name__)

AI_CONCURRENCY = 3  # Max parallel LLM calls


class ScanOrchestrator:
    """Orchestrates the complete scan pipeline from upload to results storage."""

    def __init__(self):
        self.prompt_manager = PromptManager()
        self.parser = LLMOutputParser()

    async def run_full_scan(
        self,
        scan_id: str,
        ast_findings: List[Dict[str, Any]],
        code_snippets: Dict[str, str],
        language: str = "python",
    ) -> Dict[str, Any]:
        """Run the complete scan pipeline.

        Args:
            scan_id: Unique scan identifier
            ast_findings: Findings from AST analysis
            code_snippets: Dict of file_path -> file_content
            language: Primary language of the scanned code

        Returns:
            Dict with enriched findings and analysis metadata
        """
        results = {
            "scan_id": scan_id,
            "ast_findings": len(ast_findings),
            "ai_findings": 0,
            "total_findings": 0,
            "findings": ast_findings,
            "ai_enriched": False,
            "errors": [],
        }

        if not ast_findings:
            logger.info(f"Scan {scan_id}: No AST findings, skipping AI analysis")
            results["total_findings"] = 0
            return results

        # Enrich findings with AI analysis
        try:
            ai_results = await self._run_ai_analysis(
                ast_findings=ast_findings,
                code_snippets=code_snippets,
                language=language,
                scan_id=scan_id,
            )
            if ai_results:
                results["findings"] = self._merge_findings(ast_findings, ai_results)
                results["ai_findings"] = len(ai_results)
                results["ai_enriched"] = True
        except Exception as e:
            logger.warning(f"Scan {scan_id}: AI analysis failed, using AST-only results: {e}")
            results["errors"].append(f"AI analysis failed: {str(e)[:200]}")

        results["total_findings"] = len(results["findings"])
        return results

    async def _analyze_single_finding(
        self,
        finding: Dict[str, Any],
        code_snippets: Dict[str, str],
        language: str,
        model: str,
        semaphore: asyncio.Semaphore,
    ) -> Optional[Dict[str, Any]]:
        """Analyze a single finding with AI, respecting the concurrency semaphore."""
        async with semaphore:
            vuln_type = finding.get("vulnerability_type", "unknown")
            code_snippet = finding.get("code_snippet", "")
            file_path = finding.get("file_path", "")

            full_code = code_snippets.get(file_path, code_snippet)
            cache_key_code = full_code[:500]
            cache_key = self.prompt_manager.render_template(
                "explanation",
                {
                    "vulnerability_type": vuln_type,
                    "severity": finding.get("severity", "medium"),
                    "cwe_id": finding.get("cwe_id", ""),
                    "language": language,
                    "code_snippet": cache_key_code,
                },
            )

            cached = await prompt_cache.get("explanation", cache_key, model)
            if cached:
                return {**finding, "ai_explanation": cached}

            prompt = self.prompt_manager.render_template(
                "explanation",
                {
                    "vulnerability_type": vuln_type,
                    "severity": finding.get("severity", "medium"),
                    "cwe_id": finding.get("cwe_id", ""),
                    "language": language,
                    "code_snippet": full_code,
                },
            )

            response = await ai_chain.generate(
                prompt=prompt,
                system=None,
                finding=finding,
            )

            if not response or "response" not in response:
                return None

            parsed = self.parser.parse_explanation(response["response"])
            explanation_data = parsed.model_dump() if hasattr(parsed, "model_dump") else parsed

            await prompt_cache.set("explanation", cache_key, model, explanation_data)

            enriched = {**finding, "ai_explanation": explanation_data}

            if finding.get("severity") in ("critical", "high"):
                try:
                    fix_prompt = self.prompt_manager.render_template(
                        "fix_generation",
                        {
                            "vulnerability_type": vuln_type,
                            "severity": finding.get("severity", "high"),
                            "cwe_id": finding.get("cwe_id", ""),
                            "language": language,
                            "original_code": code_snippet,
                            "explanation": explanation_data.get("remediation", ""),
                        },
                    )

                    fix_response = await ai_chain.generate(
                        prompt=fix_prompt,
                        finding=finding,
                    )

                    if fix_response and "response" in fix_response:
                        fix_data = self.parser.parse_fix_suggestion(
                            fix_response["response"],
                            original_code=code_snippet,
                        )
                        fix_dict = fix_data.model_dump() if hasattr(fix_data, "model_dump") else fix_data

                        fixed_code = fix_dict.get("fixed_code", "")
                        validation = ast_validator.validate_fix(
                            original_code=code_snippet,
                            fixed_code=fixed_code,
                            language=language,
                        )
                        fix_dict["ast_validated"] = validation["valid"]
                        fix_dict["validation_warnings"] = validation.get("warnings", [])

                        enriched["fix_suggestion"] = fix_dict
                except Exception as e:
                    logger.warning("Fix generation failed for finding: %s", e)

            return enriched

    async def _run_ai_analysis(
        self,
        ast_findings: List[Dict[str, Any]],
        code_snippets: Dict[str, str],
        language: str,
        scan_id: str,
    ) -> Optional[List[Dict[str, Any]]]:
        """Run LLM analysis on findings in parallel with bounded concurrency."""
        model = settings.DEFAULT_MODEL

        important_findings = [
            f for f in ast_findings
            if f.get("severity") in ("critical", "high")
        ]
        if not important_findings:
            important_findings = ast_findings[:5]

        semaphore = asyncio.Semaphore(AI_CONCURRENCY)
        tasks = [
            self._analyze_single_finding(
                finding=finding,
                code_snippets=code_snippets,
                language=language,
                model=model,
                semaphore=semaphore,
            )
            for finding in important_findings
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        ai_findings = []
        for result in results:
            if isinstance(result, Exception):
                logger.warning("AI analysis failed for finding: %s", result)
                continue
            if result is not None:
                ai_findings.append(result)

        return ai_findings if ai_findings else None

    def _merge_findings(
        self,
        ast_findings: List[Dict[str, Any]],
        ai_results: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Merge AST findings with AI-enriched findings.

        AI-enriched findings replace their AST counterparts.
        """
        ai_lookup = {
            (f.get("file_path"), f.get("line_number"), f.get("vulnerability_type")): f
            for f in ai_results
        }

        merged = []
        for finding in ast_findings:
            key = (finding.get("file_path"), finding.get("line_number"), finding.get("vulnerability_type"))
            if key in ai_lookup:
                merged.append(ai_lookup[key])
            else:
                merged.append(finding)

        return merged


# Singleton instance
scan_orchestrator = ScanOrchestrator()