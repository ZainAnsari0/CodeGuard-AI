"""CodeGuard AI - Benchmark Evaluation
Computes accuracy metrics from benchmark results:
precision, recall, F1, FPR, FNR, fix validation rate, per-CWE breakdown.
"""

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class BenchmarkResult:
    """Result of scanning a single benchmark sample."""

    sample_name: str
    category: str  # "vulnerable" or "benign"
    expected_findings: list[dict[str, Any]]
    actual_findings: list[dict[str, Any]]
    scan_time_ms: int
    parser_success: bool
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "sample_name": self.sample_name,
            "category": self.category,
            "expected_findings": self.expected_findings,
            "actual_findings": self.actual_findings,
            "scan_time_ms": self.scan_time_ms,
            "parser_success": self.parser_success,
            "error": self.error,
        }


class BenchmarkEvaluator:
    """Evaluate benchmark results and compute accuracy metrics."""

    def evaluate(self, results: list[BenchmarkResult]) -> dict[str, Any]:
        """Compute full evaluation metrics from a list of benchmark results."""
        vulnerable_results = [r for r in results if r.category == "vulnerable"]
        benign_results = [r for r in results if r.category == "benign"]

        true_positives = 0
        false_positives = 0
        true_negatives = 0
        false_negatives = 0

        # Vulnerable samples: should have findings
        for result in vulnerable_results:
            if result.actual_findings:
                # Check if the expected vulnerability type was found
                expected_types = {
                    f["vulnerability_type"].lower() for f in result.expected_findings
                } if result.expected_findings else set()
                actual_types = {
                    f["vulnerability_type"].lower() for f in result.actual_findings
                }

                if expected_types and expected_types & actual_types:
                    true_positives += 1
                elif not expected_types and result.actual_findings:
                    # Expected vulnerable but no specific type — any finding counts
                    true_positives += 1
                else:
                    # Found something but not the expected type — this is a false positive
                    false_positives += 1
            else:
                false_negatives += 1

        # Benign samples: should have NO findings
        for result in benign_results:
            if result.actual_findings:
                false_positives += 1
            else:
                true_negatives += 1

        total = true_positives + false_positives + true_negatives + false_negatives

        # Compute metrics
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        fpr = false_positives / (false_positives + true_negatives) if (false_positives + true_negatives) > 0 else 0.0
        fnr = false_negatives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
        accuracy = (true_positives + true_negatives) / total if total > 0 else 0.0

        # Per-CWE breakdown
        cwe_breakdown = self._per_cwe_breakdown(results)

        # Per-sample details
        sample_details = []
        for r in results:
            expected_count = len(r.expected_findings)
            actual_count = len(r.actual_findings)
            if r.category == "vulnerable":
                verdict = "detected" if actual_count > 0 else "missed"
            else:
                verdict = "clean" if actual_count == 0 else "false_positive"

            sample_details.append({
                "sample": r.sample_name,
                "category": r.category,
                "expected_findings": expected_count,
                "actual_findings": actual_count,
                "verdict": verdict,
                "scan_time_ms": r.scan_time_ms,
                "error": r.error,
            })

        return {
            "total_samples": total,
            "true_positives": true_positives,
            "false_positives": false_positives,
            "true_negatives": true_negatives,
            "false_negatives": false_negatives,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "fpr": round(fpr, 4),
            "fnr": round(fnr, 4),
            "accuracy": round(accuracy, 4),
            "cwe_breakdown": cwe_breakdown,
            "sample_details": sample_details,
        }

    def _per_cwe_breakdown(self, results: list[BenchmarkResult]) -> dict[str, dict[str, Any]]:
        """Compute per-CWE detection rates."""
        cwe_data: dict[str, dict[str, Any]] = {}

        for result in results:
            if result.category != "vulnerable":
                continue

            for expected in result.expected_findings:
                cwe_id = expected.get("cwe_id", "UNKNOWN")
                if cwe_id not in cwe_data:
                    cwe_data[cwe_id] = {
                        "vulnerability_type": expected.get("vulnerability_type", "Unknown"),
                        "expected_count": 0,
                        "detected_count": 0,
                    }
                cwe_data[cwe_id]["expected_count"] += 1

                # Check if this CWE was detected
                actual_cwes = {
                    f.get("cwe_id", "").upper() for f in result.actual_findings
                }
                if cwe_id.upper() in actual_cwes:
                    cwe_data[cwe_id]["detected_count"] += 1

        # Compute detection rates
        for cwe_id, data in cwe_data.items():
            expected = data["expected_count"]
            detected = data["detected_count"]
            data["detection_rate"] = round(detected / expected, 4) if expected > 0 else 0.0

        return cwe_data

    def compare_versions(
        self,
        baseline_metrics: dict[str, Any],
        improved_metrics: dict[str, Any],
    ) -> dict[str, Any]:
        """Compare two benchmark runs (e.g., v1.0.0 vs v1.1.0 prompts)."""
        return {
            "precision_delta": round(improved_metrics["precision"] - baseline_metrics["precision"], 4),
            "recall_delta": round(improved_metrics["recall"] - baseline_metrics["recall"], 4),
            "f1_delta": round(improved_metrics["f1"] - baseline_metrics["f1"], 4),
            "fpr_delta": round(improved_metrics["fpr"] - baseline_metrics["fpr"], 4),
            "fnr_delta": round(improved_metrics["fnr"] - baseline_metrics["fnr"], 4),
            "accuracy_delta": round(improved_metrics["accuracy"] - baseline_metrics["accuracy"], 4),
            "baseline": {
                k: baseline_metrics[k]
                for k in ["precision", "recall", "f1", "fpr", "fnr", "accuracy"]
            },
            "improved": {
                k: improved_metrics[k]
                for k in ["precision", "recall", "f1", "fpr", "fnr", "accuracy"]
            },
        }