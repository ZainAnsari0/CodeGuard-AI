#!/usr/bin/env bash
# CodeGuard AI - Frontend Security Audit
# Runs npm audit and eslint security checks.

set -euo pipefail

echo "=========================================="
echo " CodeGuard AI - Frontend Security Audit"
echo "=========================================="
echo ""

ERRORS=0

# 1. npm audit - dependency vulnerability check
echo "--- [1/2] Running npm audit ---"
if npm audit --audit-level=moderate 2>/dev/null; then
    echo "npm audit: No moderate or higher vulnerabilities found."
else
    echo "npm audit: Vulnerabilities found!"
    npm audit 2>/dev/null || true
    ERRORS=$((ERRORS + 1))
fi
echo ""

# 2. ESLint security plugin
echo "--- [2/2] Running ESLint security check ---"
if [ -f "node_modules/.bin/eslint" ]; then
    if npx eslint src/ --no-eslintrc --rule '{"no-eval": "error", "no-implied-eval": "error", "no-new-func": "error"}' --ext .ts,.tsx 2>/dev/null; then
        echo "ESLint security: No critical issues found."
    else
        echo "ESLint security: Issues found."
        ERRORS=$((ERRORS + 1))
    fi
else
    echo "WARNING: ESLint not available. Skipping security lint."
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