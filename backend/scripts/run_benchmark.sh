#!/usr/bin/env bash
# CodeGuard AI - Benchmark Runner Script
# Runs the scanner benchmark suite against known vulnerable and benign code samples.
#
# Usage:
#   python -m app.benchmark.runner              # Run with AI pipeline
#   python -m app.benchmark.runner --rule-based # Run rule-based only (no LLM)
#
# Or use this script:
#   ./scripts/run_benchmark.sh                 # Run with AI pipeline
#   ./scripts/run_benchmark.sh --rule-based    # Run rule-based only
#   ./scripts/run_benchmark.sh --compare       # Compare against baseline
#   ./scripts/run_benchmark.sh --save-baseline # Save results as new baseline

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
RESULTS_DIR="${PROJECT_DIR}/app/benchmark/results"

MODE="ai"
COMPARE=false
SAVE_BASELINE=false

for arg in "$@"; do
    case "$arg" in
        --rule-based) MODE="rule-based" ;;
        --compare) COMPARE=true ;;
        --save-baseline) SAVE_BASELINE=true ;;
        --help|-h)
            echo "Usage: $0 [--rule-based] [--compare] [--save-baseline]"
            exit 0
            ;;
    esac
done

mkdir -p "$RESULTS_DIR"
cd "$PROJECT_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULT_FILE="${RESULTS_DIR}/benchmark_${TIMESTAMP}.json"

if [ "$MODE" = "rule-based" ]; then
    echo "Running rule-based benchmark (no LLM)..."
    python -c "
from app.benchmark.runner import BenchmarkRunner
runner = BenchmarkRunner()
metrics = runner.run_all()
runner.save_results('${RESULT_FILE}')
"
else
    echo "Running AI-powered benchmark..."
    python -c "
from app.benchmark.runner import BenchmarkRunner
from app.ai.fallback_chain import ai_chain
from app.ai.prompts.manager import PromptManager
from app.ai.parser import LLMOutputParser
runner = BenchmarkRunner(ai_chain=ai_chain, prompt_manager=PromptManager(), parser=LLMOutputParser())
metrics = runner.run_all()
runner.save_results('${RESULT_FILE}')
"
fi

echo ""
echo "Results saved to: $RESULT_FILE"

if [ "$SAVE_BASELINE" = true ]; then
    cp "$RESULT_FILE" "${RESULTS_DIR}/baseline.json"
    echo "Saved as new baseline: ${RESULTS_DIR}/baseline.json"
fi