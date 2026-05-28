"""Tests for the benchmark framework.

Verifies that:
1. Sample metadata loads correctly
2. Rule-based scanner detects known vulnerabilities
3. Rule-based scanner does not flag benign code
4. FPR target (< 15%) is met on benign samples
5. Detection rate on vulnerable samples is reasonable
"""

import pytest
from app.benchmark.runner import BenchmarkRunner, load_sample_metadata, load_sample_code
from app.benchmark.evaluate import BenchmarkEvaluator, BenchmarkResult


class TestSampleLoading:
    """Test that benchmark samples and metadata load correctly."""

    def test_vulnerable_metadata_loads(self):
        metadata = load_sample_metadata("vulnerable")
        assert len(metadata) > 0, "No vulnerable samples found"
        for sample in metadata:
            assert "file" in sample
            assert "expected_findings" in sample
            assert sample["category"] == "vulnerable"

    def test_benign_metadata_loads(self):
        metadata = load_sample_metadata("benign")
        assert len(metadata) > 0, "No benign samples found"
        for sample in metadata:
            assert "file" in sample
            assert "expected_findings" in sample
            assert sample["category"] == "benign"

    def test_vulnerable_samples_have_code(self):
        metadata = load_sample_metadata("vulnerable")
        for sample in metadata:
            code = load_sample_code("vulnerable", sample["file"])
            assert len(code) > 0, f"No code loaded for {sample['file']}"

    def test_benign_samples_have_code(self):
        metadata = load_sample_metadata("benign")
        for sample in metadata:
            code = load_sample_code("benign", sample["file"])
            assert len(code) > 0, f"No code loaded for {sample['file']}"


class TestRuleBasedScanner:
    """Test the rule-based fallback scanner against benchmark samples."""

    @pytest.fixture
    def runner(self):
        return BenchmarkRunner()

    def test_detects_sql_injection(self, runner):
        code = load_sample_code("vulnerable", "sql_injection.py")
        findings = runner._scan_rule_based(code, "python")
        vuln_types = {f["vulnerability_type"] for f in findings}
        assert "SQL Injection" in vuln_types, f"Failed to detect SQL Injection. Found: {vuln_types}"

    def test_detects_hardcoded_credentials(self, runner):
        code = load_sample_code("vulnerable", "hardcoded_credentials.py")
        findings = runner._scan_rule_based(code, "python")
        vuln_types = {f["vulnerability_type"] for f in findings}
        assert "Hardcoded Credentials" in vuln_types, f"Failed to detect hardcoded credentials. Found: {vuln_types}"

    def test_detects_eval_injection(self, runner):
        code = load_sample_code("vulnerable", "eval_injection.py")
        findings = runner._scan_rule_based(code, "python")
        vuln_types = {f["vulnerability_type"] for f in findings}
        assert "Eval Injection" in vuln_types, f"Failed to detect eval injection. Found: {vuln_types}"

    def test_detects_insecure_deserialization(self, runner):
        code = load_sample_code("vulnerable", "insecure_deserialization.py")
        findings = runner._scan_rule_based(code, "python")
        vuln_types = {f["vulnerability_type"] for f in findings}
        assert "Insecure Deserialization" in vuln_types, f"Failed to detect insecure deserialization. Found: {vuln_types}"

    def test_benign_sql_not_flagged(self, runner):
        code = load_sample_code("benign", "safe_sql_queries.py")
        findings = runner._scan_rule_based(code, "python")
        sql_findings = [f for f in findings if "SQL" in f["vulnerability_type"]]
        assert len(sql_findings) == 0, f"False positive: safe SQL queries flagged as {sql_findings}"

    def test_benign_eval_alternatives_not_flagged(self, runner):
        code = load_sample_code("benign", "safe_eval_alternatives.py")
        findings = runner._scan_rule_based(code, "python")
        eval_findings = [f for f in findings if "Eval" in f["vulnerability_type"]]
        # ast.literal_eval should NOT be flagged
        assert len(eval_findings) == 0, f"False positive: safe eval alternatives flagged as {eval_findings}"

    def test_benign_credential_handling_not_flagged(self, runner):
        code = load_sample_code("benign", "safe_credential_handling.py")
        findings = runner._scan_rule_based(code, "python")
        cred_findings = [f for f in findings if "Credentials" in f["vulnerability_type"]]
        assert len(cred_findings) == 0, f"False positive: env-var credentials flagged as {cred_findings}"


class TestBenchmarkEvaluation:
    """Test the benchmark evaluator."""

    def test_perfect_detection(self):
        evaluator = BenchmarkEvaluator()
        results = [
            BenchmarkResult(
                sample_name="test_vuln.py",
                category="vulnerable",
                expected_findings=[{"vulnerability_type": "SQL Injection", "cwe_id": "CWE-89"}],
                actual_findings=[{"vulnerability_type": "SQL Injection", "cwe_id": "CWE-89", "severity": "high", "confidence": 0.9}],
                scan_time_ms=100,
                parser_success=True,
            ),
            BenchmarkResult(
                sample_name="test_safe.py",
                category="benign",
                expected_findings=[],
                actual_findings=[],
                scan_time_ms=50,
                parser_success=True,
            ),
        ]
        metrics = evaluator.evaluate(results)
        assert metrics["precision"] == 1.0
        assert metrics["recall"] == 1.0
        assert metrics["f1"] == 1.0
        assert metrics["fpr"] == 0.0
        assert metrics["fnr"] == 0.0

    def test_false_positive_penalty(self):
        evaluator = BenchmarkEvaluator()
        results = [
            BenchmarkResult(
                sample_name="safe_code.py",
                category="benign",
                expected_findings=[],
                actual_findings=[{"vulnerability_type": "SQL Injection", "severity": "high", "cwe_id": "CWE-89", "confidence": 0.7}],
                scan_time_ms=100,
                parser_success=True,
            ),
        ]
        metrics = evaluator.evaluate(results)
        assert metrics["false_positives"] == 1
        assert metrics["precision"] == 0.0

    def test_fpr_below_threshold(self):
        """FPR should be below 15% on benign samples using rule-based scanner."""
        runner = BenchmarkRunner()
        benign_meta = load_sample_metadata("benign")

        false_positives = 0
        total_benign = len(benign_meta)

        for sample in benign_meta:
            code = load_sample_code("benign", sample["file"])
            findings = runner._scan_rule_based(code, "python")
            if findings:
                false_positives += 1

        fpr = false_positives / total_benign if total_benign > 0 else 0
        assert fpr <= 0.15, f"FPR {fpr:.2%} exceeds 15% threshold ({false_positives}/{total_benign} benign samples flagged)"

    def test_compare_versions(self):
        evaluator = BenchmarkEvaluator()
        baseline = {
            "precision": 0.85, "recall": 0.90, "f1": 0.87,
            "fpr": 0.10, "fnr": 0.10, "accuracy": 0.88,
        }
        improved = {
            "precision": 0.90, "recall": 0.92, "f1": 0.91,
            "fpr": 0.08, "fnr": 0.08, "accuracy": 0.91,
        }
        comparison = evaluator.compare_versions(baseline, improved)
        assert comparison["precision_delta"] == 0.05
        assert comparison["recall_delta"] == 0.02
        assert comparison["fpr_delta"] == -0.02