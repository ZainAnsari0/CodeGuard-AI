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
COMPOSE_CMD="docker compose"

if [ "$ENV" != "staging" ] && [ "$ENV" != "production" ]; then
    echo "Usage: $0 [staging|production] [--rollback]"
    exit 1
fi

# Production uses the prod compose overlay
if [ "$ENV" = "production" ]; then
    COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod.yml"
    ENV_FILE="--env-file .env.production"
    HEALTH_URL="https://localhost/health"
else
    COMPOSE_FILES="-f docker-compose.yml"
    ENV_FILE=""
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
    ${COMPOSE_CMD} ${COMPOSE_FILES} ${ENV_FILE} build
    ${COMPOSE_CMD} ${COMPOSE_FILES} ${ENV_FILE} up -d

    echo "Rollback complete. Monitor health at: ${HEALTH_URL}"
    exit 0
fi

# ── Pre-deploy checks ──────────────────────────────────────
echo "[1/7] Running pre-deploy checks..."

# Check docker
if ! command -v docker &>/dev/null; then
    echo "ERROR: docker not found. Please install Docker."
    exit 1
fi
echo "  ✓ docker found"

# Check docker compose
if ! ${COMPOSE_CMD} version &>/dev/null; then
    echo "ERROR: docker compose not found."
    exit 1
fi
echo "  ✓ docker compose found"

# Check .env.production for production
if [ "$ENV" = "production" ]; then
    if [ ! -f ".env.production" ]; then
        echo "ERROR: .env.production not found. Create it from .env.production template."
        exit 1
    fi

    # Check for default passwords
    if grep -q "CHANGE_ME" .env.production 2>/dev/null; then
        echo "WARNING: .env.production contains placeholder passwords. Update before deploying."
        echo "  Change all CHANGE_ME values to strong passwords."
        read -p "Continue anyway? [y/N] " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    echo "  ✓ .env.production found"
fi

# Check TLS certs for production
if [ "$ENV" = "production" ]; then
    if [ ! -f "certs/tls_cert.pem" ] || [ ! -f "certs/tls_private.key" ]; then
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

# ── Build images ────────────────────────────────────────────
echo "[3/7] Building Docker images..."
${COMPOSE_CMD} ${COMPOSE_FILES} ${ENV_FILE} build

# ── Database migration ─────────────────────────────────────
echo "[4/7] Running database migration..."
${COMPOSE_CMD} ${COMPOSE_FILES} ${ENV_FILE} up -d postgres redis
sleep 5

${COMPOSE_CMD} ${COMPOSE_FILES} ${ENV_FILE} up -d api
sleep 10

# Run Alembic migration
docker exec codeguard_api alembic upgrade head 2>/dev/null || \
    echo "  (Alembic migration skipped — may not be needed)"

# ── Deploy all services ─────────────────────────────────────
echo "[5/7] Starting all services..."
${COMPOSE_CMD} ${COMPOSE_FILES} ${ENV_FILE} up -d

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
    echo "  Check logs: ${COMPOSE_CMD} ${COMPOSE_FILES} ${ENV_FILE} logs api"
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
    FRONTEND_STATUS=$(curl -sf -o /dev/null -w "%{http_code}" "http://localhost:3000/" 2>/dev/null || echo "000")
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
if [ "$ENV" = "production" ]; then
    echo " Grafana: http://localhost:3001"
    echo " Prometheus: http://localhost:9090"
fi
echo "=========================================="