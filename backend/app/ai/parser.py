"""
CodeGuard AI - LLM Structured Output Parser
Parses raw LLM output into validated Pydantic models with robust error handling.
"""

import json
import re
import logging
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


# ─── Pydantic Models ───

class VulnerabilityFinding(BaseModel):
    """A single vulnerability finding."""
    vulnerability_type: str
    severity: str = "medium"
    cwe_id: Optional[str] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    explanation: str = ""
    remediation: str = ""
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)

    @field_validator("severity", mode="before")
    @classmethod
    def normalize_severity(cls, v):
        if isinstance(v, str):
            v = v.lower().strip()
            mapping = {
                "critical": "critical", "crit": "critical",
                "high": "high", "important": "high",
                "medium": "medium", "moderate": "medium", "med": "medium", "warning": "medium",
                "low": "low", "minor": "low", "info": "info", "informational": "info",
            }
            return mapping.get(v, "medium")
        return "medium"


class FixSuggestion(BaseModel):
    """AI-generated fix suggestion."""
    original_code: str
    fixed_code: str
    explanation: str = ""
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)


class ScanResult(BaseModel):
    """Complete scan result from AI analysis."""
    findings: List[VulnerabilityFinding] = []
    summary: str = ""
    language: str = ""
    total_findings: int = 0


class ExplanationResult(BaseModel):
    """Educational explanation of a vulnerability."""
    title: str = ""
    description: str = ""
    impact: str = ""
    exploitation: str = ""
    remediation: str = ""
    references: List[str] = []


# ─── Custom Exceptions ───

class LLMOutputParseError(Exception):
    """Raised when LLM output cannot be parsed into expected format."""

    def __init__(self, message: str, raw_output: Optional[str] = None):
        super().__init__(message)
        self.raw_output = raw_output


class LLMOutputValidationError(Exception):
    """Raised when parsed LLM output fails Pydantic validation."""

    def __init__(self, message: str, errors: Optional[List[Dict]] = None):
        super().__init__(message)
        self.errors = errors or []


# ─── Parser ───

class LLMOutputParser:
    """Parses raw LLM text output into structured Pydantic models."""

    @staticmethod
    def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from text that may contain markdown code blocks or extra content.

        Handles:
        - Pure JSON strings
        - JSON wrapped in ```json...``` markdown blocks
        - JSON wrapped in ```...``` code blocks
        - JSON embedded in text with content before/after
        - Partial or malformed JSON (best effort)
        """
        if not text or not text.strip():
            return None

        text = text.strip()

        # Try direct parse first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try extracting from markdown code blocks
        patterns = [
            r"```json\s*\n?(.*?)\n?\s*```",  # ```json\n{...}\n```
            r"```\s*\n?(.*?)\n?\s*```",        # ```\n{...}\n```
        ]
        for pattern in patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                try:
                    return json.loads(match.strip())
                except json.JSONDecodeError:
                    continue

        # Try finding JSON object or array boundaries
        for start_char, end_char in [("{", "}"), ("[", "]")]:
            start_idx = text.find(start_char)
            if start_idx == -1:
                continue
            # Find matching closing bracket
            depth = 0
            in_string = False
            escape_next = False
            for i in range(start_idx, len(text)):
                if escape_next:
                    escape_next = False
                    continue
                if text[i] == "\\":
                    escape_next = True
                    continue
                if text[i] == '"':
                    in_string = not in_string
                    continue
                if in_string:
                    continue
                if text[i] == start_char:
                    depth += 1
                elif text[i] == end_char:
                    depth -= 1
                    if depth == 0:
                        try:
                            return json.loads(text[start_idx:i + 1])
                        except json.JSONDecodeError:
                            break

        logger.warning("Could not extract JSON from LLM output")
        return None

    @staticmethod
    def _normalize_finding(finding: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize a finding dict to match expected schema."""
        normalized = {}

        # Map common field name variations
        field_mappings = {
            "vulnerability_type": ["vulnerability_type", "type", "vuln_type", "vulnerability", "name"],
            "severity": ["severity", "level", "risk", "risk_level"],
            "cwe_id": ["cwe_id", "cwe", "cweId"],
            "file_path": ["file_path", "file", "filename", "path"],
            "line_number": ["line_number", "line", "lineNumber", "line_start"],
            "code_snippet": ["code_snippet", "code", "snippet", "vulnerable_code"],
            "explanation": ["explanation", "description", "details", "explain", "desc"],
            "remediation": ["remediation", "fix", "solution", "recommendation", "suggestion"],
            "confidence": ["confidence", "score", "certainty"],
        }

        for target_field, source_fields in field_mappings.items():
            for source in source_fields:
                if source in finding:
                    normalized[target_field] = finding[source]
                    break

        # Set defaults for missing required fields
        normalized.setdefault("vulnerability_type", "Unknown Vulnerability")
        normalized.setdefault("explanation", "")
        normalized.setdefault("remediation", "")
        normalized.setdefault("severity", "medium")
        normalized.setdefault("confidence", 0.7)

        return normalized

    def parse_vulnerability_analysis(self, raw_output: str) -> ScanResult:
        """Parse raw LLM output into a ScanResult.

        Tries multiple parsing strategies:
        1. Direct JSON extraction
        2. Markdown code block extraction
        3. Best-effort field normalization
        """
        if not raw_output or not raw_output.strip():
            raise LLMOutputParseError("Empty LLM output", raw_output=raw_output)

        # Step 1: Try to extract JSON
        parsed = self.extract_json_from_text(raw_output)

        if parsed is None:
            # Fallback: create a single finding from the raw text
            logger.warning("No JSON found in LLM output, creating finding from raw text")
            return ScanResult(
                findings=[VulnerabilityFinding(
                    vulnerability_type="Unknown",
                    explanation=raw_output[:500],
                    severity="medium",
                    confidence=0.3,
                )],
                summary="Raw LLM output (JSON parsing failed)",
                language="unknown",
                total_findings=1,
            )

        # Step 2: Try to parse as ScanResult directly
        try:
            return ScanResult(**parsed)
        except Exception as e:
            logger.debug(f"Direct ScanResult parse failed, trying extraction: {e}")

        # Step 3: Try to extract findings list
        findings_data = parsed.get("findings", parsed.get("vulnerabilities", parsed.get("results", [])))

        if isinstance(findings_data, list):
            findings = []
            for f in findings_data:
                if isinstance(f, dict):
                    try:
                        normalized = self._normalize_finding(f)
                        findings.append(VulnerabilityFinding(**normalized))
                    except Exception as e:
                        logger.warning(f"Skipping invalid finding: {e}")
                        continue

            if findings:
                return ScanResult(
                    findings=findings,
                    summary=parsed.get("summary", ""),
                    language=parsed.get("language", ""),
                    total_findings=len(findings),
                )

        # Step 4: Single finding wrapped in an object
        if isinstance(parsed, dict) and ("vulnerability_type" in parsed or "type" in parsed):
            try:
                normalized = self._normalize_finding(parsed)
                finding = VulnerabilityFinding(**normalized)
                return ScanResult(
                    findings=[finding],
                    summary=parsed.get("summary", ""),
                    language=parsed.get("language", ""),
                    total_findings=1,
                )
            except Exception as e:
                logger.warning(f"Failed to parse single finding: {e}")

        raise LLMOutputParseError(
            "Could not parse LLM output into vulnerability findings",
            raw_output=raw_output[:200],
        )

    def parse_fix_suggestion(self, raw_output: str, original_code: str = "") -> FixSuggestion:
        """Parse fix suggestion from LLM output."""
        if not raw_output or not raw_output.strip():
            raise LLMOutputParseError("Empty LLM output", raw_output=raw_output)

        parsed = self.extract_json_from_text(raw_output)

        if parsed:
            try:
                return FixSuggestion(
                    original_code=parsed.get("original_code", original_code),
                    fixed_code=parsed.get("fixed_code", parsed.get("fix", parsed.get("solution", ""))),
                    explanation=parsed.get("explanation", parsed.get("description", "")),
                    confidence=float(parsed.get("confidence", 0.7)),
                )
            except (ValueError, TypeError) as e:
                logger.warning(f"Fix suggestion validation error: {e}")

        # Fallback: try to extract code from markdown blocks
        code_blocks = re.findall(r"```(?:\w+)?\s*\n(.*?)\n```", raw_output, re.DOTALL)
        if code_blocks:
            return FixSuggestion(
                original_code=original_code,
                fixed_code=code_blocks[0].strip(),
                explanation=raw_output[:500],
                confidence=0.5,
            )

        raise LLMOutputParseError(
            "Could not parse LLM output into fix suggestion",
            raw_output=raw_output[:200],
        )

    def parse_explanation(self, raw_output: str) -> ExplanationResult:
        """Parse educational explanation from LLM output."""
        if not raw_output or not raw_output.strip():
            raise LLMOutputParseError("Empty LLM output", raw_output=raw_output)

        parsed = self.extract_json_from_text(raw_output)

        if parsed:
            try:
                return ExplanationResult(**{
                    "title": parsed.get("title", ""),
                    "description": parsed.get("description", ""),
                    "impact": parsed.get("impact", ""),
                    "exploitation": parsed.get("exploitation", ""),
                    "remediation": parsed.get("remediation", ""),
                    "references": parsed.get("references", []),
                })
            except Exception as e:
                logger.warning(f"Explanation validation error: {e}")

        raise LLMOutputParseError(
            "Could not parse LLM output into explanation",
            raw_output=raw_output[:200],
        )