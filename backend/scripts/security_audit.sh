#!/usr/bin/env bash
# CodeGuard AI - Backend Security Audit
# Runs bandit, safety, and secret detection checks.

set -euo pipefail

echo "=========================================="
echo " CodeGuard AI - Backend Security Audit"
echo "=========================================="
echo ""

ERRORS=0

# 1. Bandit - Python security linter
echo "--- [1/3] Running Bandit security scan ---"
if command -v bandit &>/dev/null; then
    if bandit -r app/ -ll -ii -f json -o /tmp/bandit_report.json 2>/dev/null; then
        echo "Bandit: No high/medium severity issues found."
    else
        echo "Bandit: Issues found. Full report:"
        bandit -r app/ -ll -ii 2>/dev/null || true
        ERRORS=$((ERRORS + 1))
    fi
else
    echo "WARNING: bandit not installed. Install with: pip install bandit"
    echo "Skipping Bandit check."
fi
echo ""

# 2. Safety - dependency vulnerability check
echo "--- [2/3] Running Safety dependency check ---"
if command -v safety &>/dev/null; then
    if safety check -r requirements.txt --json -o /tmp/safety_report.json 2>/dev/null; then
        echo "Safety: No known vulnerabilities in dependencies."
    else
        echo "Safety: Vulnerabilities found. Full report:"
        safety check -r requirements.txt 2>/dev/null || true
        ERRORS=$((ERRORS + 1))
    fi
else
    echo "WARNING: safety not installed. Install with: pip install safety"
    echo "Skipping Safety check."
fi
echo ""

# 3. Check for hardcoded secrets
echo "--- [3/3] Running secret detection scan ---"
if python3 scripts/check_secrets.py 2>/dev/null; then
    echo "Secret detection: No obvious secrets found."
else
    echo "Secret detection: Potential secrets found!"
    ERRORS=$((ERRORS + 1))
fi
echo ""

echo "=========================================="
if [ "$ERRORS" -eq 0 ]; then
    echo " Security audit PASSED - No critical issues"
else
    echo " Security audit FAILED - $ERRORS check(s) had issues"
fi
echo "=========================================="
exit $ERRORS