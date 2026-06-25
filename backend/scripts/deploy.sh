#!/usr/bin/env bash
# CodeGuard AI — Deployment Script
# Deploys to staging or production with health checks and rollback capability.
#
# Usage:
#   ./deploy.sh staging          # Deploy to staging
#   ./deploy.sh production       # Deploy to production
#   ./deploy.sh production --rollback  # Rollback to previous version

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# ── Configuration ──────────────────────────────────────────
ENV="${1:-staging}"
ROLLBACK="${2:-}"
APP_DIR="${APP_DIR:-/opt/codeguard}"
VENV_DIR="${APP_DIR}/backend/venv"

if [ "$ENV" != "staging" ] && [ "$ENV" != "production" ]; then
    echo "Usage: $0 [staging|production] [--rollback]"
    exit 1
fi

# Set environment-specific values
if [ "$ENV" = "production" ]; then
    ENV_FILE=".env.production.local"
    HEALTH_URL="https://localhost/health"
else
    ENV_FILE=".env.staging"
    HEALTH_URL="http://localhost:8000/health"
fi

echo "=========================================="
echo " CodeGuard AI — Deployment"
echo " Environment: ${ENV}"
echo " Rollback: ${ROLLBACK:-none}"
echo "=========================================="
echo ""

cd "${PROJECT_DIR}"

# ── Rollback mode ──────────────────────────────────────────
if [ "$ROLLBACK" = "--rollback" ]; then
    echo "Rolling back to previous deployment..."

    # Get current and previous tags
    CURRENT_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "unknown")
    PREV_TAG=$(git tag --sort=-version:refname | sed -n '2p' 2>/dev/null || echo "unknown")

    if [ "$PREV_TAG" = "unknown" ]; then
        echo "ERROR: No previous tag found for rollback."
        exit 1
    fi

    echo "  Current: ${CURRENT_TAG}"
    echo "  Rolling back to: ${PREV_TAG}"

    git checkout "$PREV_TAG"

    # Reinstall and rebuild
    cd backend && source venv/bin/activate && pip install -r requirements.txt -q
    cd .. && cd frontend && npm ci && npm run build

    # Restart services
    sudo systemctl restart codeguard-api codeguard-celery codeguard-celery-beat

    echo "Rollback complete. Monitor health at: ${HEALTH_URL}"
    exit 0
fi

# ── Pre-deploy checks ──────────────────────────────────────
echo "[1/7] Running pre-deploy checks..."

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "ERROR: python3 not found."
    exit 1
fi
echo "  ✓ python3 found"

# Check Node.js
if ! command -v node &>/dev/null; then
    echo "WARNING: node not found. JavaScript scanning will fall back to regex."
else
    echo "  ✓ node found"
fi

# Check PostgreSQL
if ! systemctl is-active --quiet postgresql 2>/dev/null; then
    echo "WARNING: PostgreSQL may not be running."
else
    echo "  ✓ PostgreSQL running"
fi

# Check .env.production for production
if [ "$ENV" = "production" ]; then
    if [ ! -f "${ENV_FILE}" ]; then
        echo "ERROR: ${ENV_FILE} not found. Create it from .env.production template."
        exit 1
    fi

    # Check for default passwords
    if grep -q "CHANGE_ME" "${ENV_FILE}" 2>/dev/null; then
        echo "WARNING: ${ENV_FILE} contains placeholder passwords. Update before deploying."
        echo "  Change all CHANGE_ME values to strong passwords."
        read -p "Continue anyway? [y/N] " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    echo "  ✓ ${ENV_FILE} found"
fi

# Check TLS certs for production
if [ "$ENV" = "production" ]; then
    if [ ! -f "certs/tls_cert.pem" ] && [ ! -f "certs/fullchain.pem" ]; then
        echo "WARNING: TLS certificates not found in certs/."
        echo "  Run: bash backend/scripts/setup-tls.sh"
        read -p "Continue without TLS? [y/N] " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        echo "  ✓ TLS certificates found"
    fi
fi

# ── Pull latest code ──────────────────────────────────────
echo "[2/7] Pulling latest code..."
git pull origin main 2>/dev/null || echo "  (no remote or already up to date)"

# ── Tag release ─────────────────────────────────────────────
TIMESTAMP=$(date '+%Y%m%d%H%M%S')
RELEASE_TAG="v$(cat backend/app/core/config.py 2>/dev/null | grep PROJECT_VERSION | head -1 | sed "s/.*= '\(.*\)'.*/\1/" || echo '1.0.0')-${TIMESTAMP}"
echo "  Release tag: ${RELEASE_TAG}"
git tag "$RELEASE_TAG" 2>/dev/null || true

# ── Install dependencies ────────────────────────────────────
echo "[3/7] Installing dependencies..."
cd backend
source venv/bin/activate 2>/dev/null || { python3 -m venv venv && source venv/bin/activate; }
pip install -r requirements.txt -q
cd ..
cd frontend && npm ci && npm run build && cd ..

# ── Database migration ─────────────────────────────────────
echo "[4/7] Running database migration..."
cd backend
source venv/bin/activate
alembic upgrade head 2>/dev/null || echo "  (Alembic migration skipped — may not be needed)"
cd ..

# ── Deploy all services ─────────────────────────────────────
echo "[5/7] Restarting services..."
sudo systemctl restart codeguard-api codeguard-celery codeguard-celery-beat

# ── Wait for services ──────────────────────────────────────
echo "[6/7] Waiting for services to become healthy..."
MAX_RETRIES=30
RETRY_INTERVAL=5
RETRIES=0

while [ $RETRIES -lt $MAX_RETRIES ]; do
    if curl -sf "${HEALTH_URL}" > /dev/null 2>&1; then
        echo "  ✓ Health check passed"
        break
    fi

    RETRIES=$((RETRIES + 1))
    echo "  Waiting... (${RETRIES}/${MAX_RETRIES})"
    sleep $RETRY_INTERVAL
done

if [ $RETRIES -eq $MAX_RETRIES ]; then
    echo "  ✗ Health check failed after ${MAX_RETRIES} retries"
    echo "  Check logs: journalctl -u codeguard-api -n 50"
    exit 1
fi

# ── Post-deploy smoke tests ─────────────────────────────────
echo "[7/7] Running smoke tests..."

# Test API health
API_RESPONSE=$(curl -sf "${HEALTH_URL}" 2>/dev/null || echo "{}")
if echo "$API_RESPONSE" | grep -q "healthy"; then
    echo "  ✓ API health check passed"
else
    echo "  ✗ API health check failed"
fi

# Test frontend
FRONTEND_URL=$(echo "$HEALTH_URL" | sed 's|/health$|/|')
if [ "$ENV" = "production" ]; then
    FRONTEND_STATUS=$(curl -sf -o /dev/null -w "%{http_code}" "https://localhost/" 2>/dev/null || echo "000")
else
    FRONTEND_STATUS=$(curl -sf -o /dev/null -w "%{http_code}" "http://localhost:5173/" 2>/dev/null || echo "000")
fi

if [ "$FRONTEND_STATUS" = "200" ]; then
    echo "  ✓ Frontend responding (HTTP ${FRONTEND_STATUS})"
else
    echo "  ⚠ Frontend returned HTTP ${FRONTEND_STATUS}"
fi

# ── Summary ─────────────────────────────────────────────────
echo ""
echo "=========================================="
echo " Deployment complete!"
echo " Environment: ${ENV}"
echo " Tag: ${RELEASE_TAG}"
echo " Health: ${HEALTH_URL}"
echo "=========================================="