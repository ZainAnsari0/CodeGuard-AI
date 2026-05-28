"""
CodeGuard AI - Prompt Template Versions
Tracks version metadata for prompt templates.
"""

PROMPT_VERSIONS = {
    "vulnerability_analysis": {
        "current": "1.1.0",
        "versions": {
            "1.0.0": {
                "description": "Initial vulnerability analysis prompt for scanning code",
                "date": "2026-05-16",
                "changes": "Initial release",
            },
            "1.1.0": {
                "description": "Improved vulnerability analysis with anti-false-positive rules and CWE-specific guidance",
                "date": "2026-05-28",
                "changes": [
                    "Added explicit anti-false-positive rules (check mitigations first)",
                    "Added CWE-specific guidance for SQL Injection, XSS, Path Traversal, Hardcoded Credentials, Insecure Deserialization, and Code Injection",
                    "Added confidence calibration instructions (only >0.8 for confirmed exploitable)",
                    "Added rule that false positives are worse than false negatives",
                ],
            },
        },
    },
    "fix_generation": {
        "current": "1.1.0",
        "versions": {
            "1.0.0": {
                "description": "Initial fix generation prompt for creating security patches",
                "date": "2026-05-16",
                "changes": "Initial release",
            },
            "1.1.0": {
                "description": "Improved fix generation with minimal-change constraints and CWE-specific fix patterns",
                "date": "2026-05-28",
                "changes": [
                    "Added minimal-change rule (only fix the vulnerability, no refactoring)",
                    "Added syntax validation requirement",
                    "Added no-regression rule (don't introduce new vulnerabilities)",
                    "Added no-placeholders rule (provide actual code, not comments)",
                    "Added CWE-specific fix patterns for all major vulnerability types",
                    "Added good fix and bad fix examples",
                ],
            },
        },
    },
    "explanation": {
        "current": "1.1.0",
        "versions": {
            "1.0.0": {
                "description": "Initial explanation prompt for educational vulnerability descriptions",
                "date": "2026-05-16",
                "changes": "Initial release",
            },
            "1.1.0": {
                "description": "Improved explanation prompt with structured format and CWE references",
                "date": "2026-05-28",
                "changes": [
                    "Added structured explanation format (title, description, impact, exploitation, remediation, references)",
                    "Added educational tone guidelines",
                    "Added CWE reference links in output format",
                    "Added instruction to reference specific lines of code",
                ],
            },
        },
    },
}