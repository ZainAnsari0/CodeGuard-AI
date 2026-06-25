"""
Tests for the LLM Output Parser and Prompt Manager.
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ai.parser import (
    LLMOutputParser,
    ScanResult,
    VulnerabilityFinding,
    FixSuggestion,
    LLMOutputParseError,
)


class TestJSONExtraction:
    """Test JSON extraction from various LLM output formats."""

    def setup_method(self):
        self.parser = LLMOutputParser()

    def test_pure_json(self):
        """Test extracting pure JSON."""
        text = '{"findings": [], "summary": "Safe code", "language": "python"}'
        result = self.parser.extract_json_from_text(text)
        assert result is not None
        assert result["summary"] == "Safe code"

    def test_json_in_markdown_code_block(self):
        """Test extracting JSON from markdown code block."""
        text = """Here is the analysis:

```json
{"findings": [{"vulnerability_type": "SQL Injection", "severity": "critical"}], "summary": "Vulnerable", "language": "python"}
```

Let me know if you need more details."""
        result = self.parser.extract_json_from_text(text)
        assert result is not None
        assert result["findings"][0]["vulnerability_type"] == "SQL Injection"

    def test_json_in_plain_code_block(self):
        """Test extracting JSON from plain code block."""
        text = """```
{"findings": [], "summary": "Clean", "language": "js"}
```"""
        result = self.parser.extract_json_from_text(text)
        assert result is not None
        assert result["language"] == "js"

    def test_json_embedded_in_text(self):
        """Test extracting JSON surrounded by text."""
        text = """I found the following issues:

{"findings": [{"vulnerability_type": "XSS", "severity": "high"}], "summary": "XSS found", "language": "js"}

Please review these findings."""
        result = self.parser.extract_json_from_text(text)
        assert result is not None
        assert result["findings"][0]["vulnerability_type"] == "XSS"

    def test_empty_input(self):
        """Test with empty input."""
        assert self.parser.extract_json_from_text("") is None
        assert self.parser.extract_json_from_text("   ") is None

    def test_no_json(self):
        """Test with text that has no JSON."""
        text = "This is just plain text with no JSON content at all."
        assert self.parser.extract_json_from_text(text) is None


class TestVulnerabilityAnalysis:
    """Test vulnerability analysis parsing."""

    def setup_method(self):
        self.parser = LLMOutputParser()

    def test_valid_scan_result(self):
        """Test parsing a valid scan result."""
        raw = """```json
{
    "findings": [
        {
            "vulnerability_type": "SQL Injection",
            "severity": "critical",
            "cwe_id": "CWE-89",
            "file_path": "app.py",
            "line_number": 42,
            "code_snippet": "cursor.execute(query)",
            "explanation": "User input directly interpolated into SQL query",
            "remediation": "Use parameterized queries",
            "confidence": 0.95
        }
    ],
    "summary": "Found SQL injection vulnerability",
    "language": "python",
    "total_findings": 1
}
```"""
        result = self.parser.parse_vulnerability_analysis(raw)
        assert isinstance(result, ScanResult)
        assert len(result.findings) == 1
        assert result.findings[0].vulnerability_type == "SQL Injection"
        assert result.findings[0].severity == "critical"
        assert result.findings[0].cwe_id == "CWE-89"

    def test_severity_normalization(self):
        """Test that severity values are normalized."""
        raw = '{"findings": [{"vulnerability_type": "XSS", "severity": "CRITICAL", "explanation": "test", "remediation": "fix"}], "summary": "", "language": "js"}'
        result = self.parser.parse_vulnerability_analysis(raw)
        assert result.findings[0].severity == "critical"

    def test_missing_fields_get_defaults(self):
        """Test that missing optional fields get reasonable defaults."""
        raw = '{"findings": [{"vulnerability_type": "Buffer Overflow", "severity": "high"}], "summary": "", "language": "c"}'
        result = self.parser.parse_vulnerability_analysis(raw)
        assert result.findings[0].vulnerability_type == "Buffer Overflow"
        assert result.findings[0].cwe_id is None
        assert result.findings[0].confidence == 0.7  # default

    def test_empty_output_raises_error(self):
        """Test that empty output raises an error."""
        with pytest.raises(LLMOutputParseError):
            self.parser.parse_vulnerability_analysis("")

    def test_non_json_creates_fallback_finding(self):
        """Test that non-JSON text creates a fallback finding."""
        result = self.parser.parse_vulnerability_analysis("This code has a buffer overflow vulnerability in the input handling.")
        assert len(result.findings) == 1
        assert result.findings[0].vulnerability_type == "Unknown"


class TestFixSuggestion:
    """Test fix suggestion parsing."""

    def setup_method(self):
        self.parser = LLMOutputParser()

    def test_valid_fix_suggestion(self):
        """Test parsing a valid fix suggestion."""
        raw = """```json
{
    "original_code": "cursor.execute(query)",
    "fixed_code": "cursor.execute(query, params)",
    "explanation": "Use parameterized queries to prevent SQL injection",
    "confidence": 0.9
}
```"""
        result = self.parser.parse_fix_suggestion(raw, original_code="cursor.execute(query)")
        assert isinstance(result, FixSuggestion)
        assert result.fixed_code == "cursor.execute(query, params)"
        assert result.confidence == 0.9

    def test_fix_with_code_block_fallback(self):
        """Test extracting fix from markdown code block when JSON parsing fails."""
        raw = """Here's the fix:

```python
cursor.execute(query, params)
```

This uses parameterized queries to prevent SQL injection."""
        result = self.parser.parse_fix_suggestion(raw, original_code="cursor.execute(query)")
        assert "cursor.execute(query, params)" in result.fixed_code

    def test_empty_output_raises_error(self):
        """Test that empty output raises an error."""
        with pytest.raises(LLMOutputParseError):
            self.parser.parse_fix_suggestion("", original_code="code")


class TestPromptManager:
    """Test prompt template management."""

    def test_load_and_render_template(self):
        """Test loading and rendering a template."""
        from app.ai.prompts import PromptManager
        manager = PromptManager()

        result = manager.render_template("vulnerability_analysis", {
            "language": "python",
            "code_snippet": "x = request.args.get('id')\nquery = f'SELECT * FROM users WHERE id = {x}'",
            "file_path": "app.py",
            "vulnerability_type": None,
        })

        assert "python" in result
        assert "request.args.get" in result
        assert "app.py" in result
        assert "findings" in result.lower() or "JSON" in result

    def test_list_templates(self):
        """Test listing available templates."""
        from app.ai.prompts import PromptManager
        manager = PromptManager()
        templates = manager.list_templates()
        assert "vulnerability_analysis" in templates
        assert "fix_generation" in templates
        assert "explanation" in templates

    def test_template_info(self):
        """Test getting template metadata."""
        from app.ai.prompts import PromptManager
        manager = PromptManager()
        info = manager.get_template_info("vulnerability_analysis")
        assert info["exists"] is True
        # Current version is tracked in app.ai.prompts.versions.PROMPT_VERSIONS
        assert info["current_version"] == "1.1.0"

    def test_fix_generation_template(self):
        """Test the fix generation template renders correctly."""
        from app.ai.prompts import PromptManager
        manager = PromptManager()

        result = manager.render_template("fix_generation", {
            "vulnerability_type": "SQL Injection",
            "severity": "critical",
            "cwe_id": "CWE-89",
            "language": "python",
            "original_code": "cursor.execute(f'SELECT * FROM users WHERE id = {user_id}')",
            "explanation": "Direct string interpolation allows SQL injection",
        })

        assert "SQL Injection" in result
        assert "cursor.execute" in result
        assert "CWE-89" in result

    def test_explanation_template(self):
        """Test the explanation template renders correctly."""
        from app.ai.prompts import PromptManager
        manager = PromptManager()

        result = manager.render_template("explanation", {
            "vulnerability_type": "Cross-Site Scripting",
            "severity": "high",
            "cwe_id": "CWE-79",
            "language": "javascript",
            "code_snippet": "element.innerHTML = userInput;",
        })

        assert "Cross-Site Scripting" in result
        assert "high" in result
        assert "CWE-79" in result