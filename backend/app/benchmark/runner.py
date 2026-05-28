"""CodeGuard AI - Benchmark Runner
Runs the scanner against known vulnerable and benign code samples,
collects results, and computes accuracy metrics.
"""

import json
import logging
import time
import os
from pathlib import Path
from typing import Any

from app.benchmark.evaluate import BenchmarkEvaluator, BenchmarkResult

logger = logging.getLogger(__name__)

SAMPLES_DIR = Path(__file__).parent / "samples"
VULNERABLE_DIR = SAMPLES_DIR / "vulnerable"
BENIGN_DIR = SAMPLES_DIR / "benign"


def load_sample_metadata(category: str) -> list[dict[str, Any]]:
    """Load metadata for all samples in a category (vulnerable/benign)."""
    meta_path = SAMPLES_DIR / category / "metadata.json"
    if not meta_path.exists():
        logger.warning(f"No metadata found at {meta_path}")
        return []
    with open(meta_path) as f:
        return json.load(f)


def load_sample_code(category: str, filename: str) -> str:
    """Load the source code for a sample."""
    filepath = SAMPLES_DIR / category / filename
    if not filepath.exists():
        logger.error(f"Sample file not found: {filepath}")
        return ""
    with open(filepath) as f:
        return f.read()


class BenchmarkRunner:
    """Run the CodeGuard scanner against benchmark samples and evaluate results."""

    def __init__(self, ai_chain=None, prompt_manager=None, parser=None):
        self.ai_chain = ai_chain
        self.prompt_manager = prompt_manager
        self.parser = parser
        self.evaluator = BenchmarkEvaluator()
        self.results: list[BenchmarkResult] = []
        self.metrics: dict[str, Any] = {}

    def run_all(self) -> dict[str, Any]:
        """Run the full benchmark suite and return evaluation metrics."""
        import asyncio
        logger.info("Starting benchmark run...")

        # Run vulnerable samples (should be detected)
        vulnerable_meta = load_sample_metadata("vulnerable")
        for sample in vulnerable_meta:
            result = self._run_sample("vulnerable", sample)
            self.results.append(result)

        # Run benign samples (should NOT be flagged)
        benign_meta = load_sample_metadata("benign")
        for sample in benign_meta:
            result = self._run_sample("benign", sample)
            self.results.append(result)

        # Evaluate
        self.metrics = self.evaluator.evaluate(self.results)
        self._log_summary()

        return self.metrics

    def _run_sample(self, category: str, sample_meta: dict[str, Any]) -> BenchmarkResult:
        """Run a single sample through the scanner."""
        filename = sample_meta["file"]
        language = sample_meta.get("language", "python")
        expected_findings = sample_meta.get("expected_findings", [])
        code = load_sample_code(category, filename)

        if not code:
            return BenchmarkResult(
                sample_name=filename,
                category=category,
                expected_findings=expected_findings,
                actual_findings=[],
                scan_time_ms=0,
                parser_success=False,
                error="Could not load sample code",
            )

        findings: list[dict] = []
        parser_success = True
        error = None
        start_time = time.time()

        try:
            if self.ai_chain and self.prompt_manager:
                # Run through the AI pipeline
                findings = self._scan_with_ai(code, language)
            else:
                # Fallback: use rule-based scanning only
                findings = self._scan_rule_based(code, language)
        except Exception as e:
            logger.error(f"Error scanning {filename}: {e}")
            error = str(e)
            parser_success = False

        scan_time_ms = int((time.time() - start_time) * 1000)

        return BenchmarkResult(
            sample_name=filename,
            category=category,
            expected_findings=expected_findings,
            actual_findings=findings,
            scan_time_ms=scan_time_ms,
            parser_success=parser_success,
            error=error,
        )

    def _scan_with_ai(self, code: str, language: str) -> list[dict]:
        """Run code through the AI analysis pipeline."""
        import asyncio

        prompt = self.prompt_manager.render_template(
            "vulnerability_analysis",
            {
                "language": language,
                "code_snippet": code,
            },
        )

        # ai_chain.generate is async — use asyncio.run() for proper cleanup
        response = asyncio.run(self.ai_chain.generate(prompt=prompt))

        raw_output = response.get("response", "")
        try:
            scan_result = self.parser.parse_vulnerability_analysis(raw_output)
            return [
                {
                    "vulnerability_type": f.vulnerability_type,
                    "severity": f.severity,
                    "cwe_id": f.cwe_id,
                    "confidence": f.confidence,
                }
                for f in scan_result.findings
            ]
        except Exception:
            parser_success = False
            return []

    def _scan_rule_based(self, code: str, language: str) -> list[dict]:
        """Run rule-based pattern matching as a baseline scanner."""
        findings = []

        patterns = {
            "SQL Injection": [
                (r"execute\s*\(\s*[\"']SELECT.*\+\s*\w", "CWE-89"),
                (r"execute\s*\(\s*f[\"']SELECT", "CWE-89"),
            ],
            "Hardcoded Credentials": [
                (r"password\s*=\s*[\"'][^\"']+[\"']", "CWE-798"),
                (r"api_key\s*=\s*[\"'][^\"']+[\"']", "CWE-798"),
                (r"secret\s*=\s*[\"'][^\"']+[\"']", "CWE-798"),
            ],
            "Eval Injection": [
                (r"\beval\s*\(", "CWE-95"),
                (r"\bexec\s*\(", "CWE-95"),
            ],
            "Path Traversal": [
                (r"os\.path\.join\s*\([^)]*\+\s*\w", "CWE-22"),
            ],
            "Insecure Deserialization": [
                (r"pickle\.loads?\s*\(", "CWE-502"),
                (r"yaml\.load\s*\([^)]*Loader\s*=\s*yaml\.Loader", "CWE-502"),
            ],
            "Cross-Site Scripting": [
                (r"return\s*f[\"'].*\{.*request\.", "CWE-79"),
            ],
        }

        import re

        for vuln_type, pattern_list in patterns.items():
            for pattern, cwe_id in pattern_list:
                try:
                    if re.search(pattern, code):
                        findings.append({
                            "vulnerability_type": vuln_type,
                            "severity": "high",
                            "cwe_id": cwe_id,
                            "confidence": 0.85,
                        })
                except re.error:
                    pass

        return findings

    def _log_summary(self):
        """Log a summary of benchmark results."""
        total = len(self.results)
        vulnerable = [r for r in self.results if r.category == "vulnerable"]
        benign = [r for r in self.results if r.category == "benign"]

        logger.info(f"Benchmark Results: {total} samples ({len(vulnerable)} vulnerable, {len(benign)} benign)")
        logger.info(f"  Precision: {self.metrics.get('precision', 'N/A')}")
        logger.info(f"  Recall: {self.metrics.get('recall', 'N/A')}")
        logger.info(f"  F1 Score: {self.metrics.get('f1', 'N/A')}")
        logger.info(f"  False Positive Rate: {self.metrics.get('fpr', 'N/A')}")
        logger.info(f"  False Negative Rate: {self.metrics.get('fnr', 'N/A')}")

    def to_json(self) -> str:
        """Export results as JSON."""
        return json.dumps({
            "results": [r.to_dict() for r in self.results],
            "metrics": self.metrics,
        }, indent=2)

    def save_results(self, filepath: str):
        """Save benchmark results to a file."""
        with open(filepath, "w") as f:
            f.write(self.to_json())
        logger.info(f"Benchmark results saved to {filepath}")