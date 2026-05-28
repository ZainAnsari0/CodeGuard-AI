"""CodeGuard AI - Benchmark Version Comparison
Run the benchmark with different prompt versions and compare results.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.benchmark.runner import BenchmarkRunner

logger = logging.getLogger(__name__)

RESULTS_DIR = Path(__file__).parent / "results"


def compare_prompt_versions(
    ai_chain=None,
    prompt_manager=None,
    parser=None,
) -> dict[str, Any]:
    """Run benchmark with current prompts and compare against baseline.

    Returns comparison metrics showing improvement or regression.
    """
    RESULTS_DIR.mkdir(exist_ok=True)

    # Run with current prompts
    runner = BenchmarkRunner(
        ai_chain=ai_chain,
        prompt_manager=prompt_manager,
        parser=parser,
    )
    current_metrics = runner.run_all()

    # Save current results
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    current_path = RESULTS_DIR / f"benchmark_{timestamp}.json"
    runner.save_results(str(current_path))

    # Check for baseline
    baseline_path = RESULTS_DIR / "baseline.json"
    baseline_metrics = None
    comparison = None

    if baseline_path.exists():
        with open(baseline_path) as f:
            baseline_data = json.load(f)
            baseline_metrics = baseline_data.get("metrics", {})

        from app.benchmark.evaluate import BenchmarkEvaluator
        evaluator = BenchmarkEvaluator()
        comparison = evaluator.compare_versions(baseline_metrics, current_metrics)

        logger.info(f"Comparison with baseline:")
        logger.info(f"  Precision: {comparison['baseline']['precision']} -> {comparison['improved']['precision']} (delta: {comparison['precision_delta']})")
        logger.info(f"  Recall: {comparison['baseline']['recall']} -> {comparison['improved']['recall']} (delta: {comparison['recall_delta']})")
        logger.info(f"  F1: {comparison['baseline']['f1']} -> {comparison['improved']['f1']} (delta: {comparison['f1_delta']})")
        logger.info(f"  FPR: {comparison['baseline']['fpr']} -> {comparison['improved']['fpr']} (delta: {comparison['fpr_delta']})")
    else:
        logger.info("No baseline found. Saving current results as baseline.")
        runner.save_results(str(baseline_path))

    result = {
        "timestamp": timestamp,
        "current_metrics": current_metrics,
        "comparison": comparison,
    }

    # Save full report
    report_path = RESULTS_DIR / f"comparison_{timestamp}.json"
    with open(report_path, "w") as f:
        json.dump(result, f, indent=2, default=str)

    return result