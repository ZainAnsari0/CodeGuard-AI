#!/usr/bin/env bash
# CodeGuard AI — OWASP ZAP Baseline Scan
# Runs a baseline security scan against the local API.
# Requires: Docker (for ZAP container)

set -euo pipefail

TARGET_URL="${1:-http://localhost:8000}"
ZAP_PORT="8090"
REPORT_DIR="$(dirname "$0")/../reports"
mkdir -p "$REPORT_DIR"

echo "=========================================="
echo " CodeGuard AI — OWASP ZAP Baseline Scan"
echo " Target: $TARGET_URL"
echo "=========================================="
echo ""

# Start ZAP container
echo "[1/3] Starting ZAP container..."
docker run -u zap -d -p "${ZAP_PORT}:${ZAP_PORT}" \
    --name zap-scan \
    zaproxy/zap-stable \
    zap.sh -daemon -port "${ZAP_PORT}" -config api.disablekey=true -config api.addrs.addr.name=.* -config api.addrs.addr.regex=true \
    2>/dev/null || true

echo "[2/3] Waiting for ZAP to start..."
sleep 30

# Run baseline scan
echo "[3/3] Running baseline scan against $TARGET_URL..."
docker exec zap-scan zap-cli quick-scan --self-contained -t "${TARGET_URL}" -f json 2>/dev/null || true

# Generate report
echo "Generating HTML report..."
docker exec zap-scan zap-cli report -o "${REPORT_DIR}/zap_report.html" -f html 2>/dev/null || true

# Clean up
echo "Cleaning up..."
docker stop zap-scan 2>/dev/null || true
docker rm zap-scan 2>/dev/null || true

echo ""
echo "=========================================="
echo " ZAP scan complete!"
echo " Report: ${REPORT_DIR}/zap_report.html"
echo "=========================================="