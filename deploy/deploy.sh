#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════
# CodeGuard AI — Production Deployment Script
# ═══════════════════════════════════════════════════════════════════
# Usage:
#   ./deploy/deploy.sh                    # Full production deploy
#   ./deploy/deploy.sh --skip-backup      # Deploy without backup
#   ./deploy/deploy.sh --skip-migrate     # Deploy without migrations
#   ./deploy/deploy.sh --rollback         # Rollback to previous version
#
# This script deploys CodeGuard AI as systemd services.
# ═══════════════════════════════════════════════════════════════════
set -euo pipefail

# ── Configuration ────────────────────────────────────────────────
ENV="${ENV:-production}"
BACKUP_BEFORE_DEPLOY=true
RUN_MIGRATIONS=true
HEALTH_TIMEOUT=120
HEALTH_INTERVAL=5
ROLLBACK=false
API_SERVICE="codeguard-api"
CELERY_SERVICE="codeguard-celery"
APP_DIR="${APP_DIR:-/opt/codeguard}"
VENV_DIR="${VENV_DIR:-${APP_DIR}/backend/venv}"

# ── Parse Arguments ──────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-backup) BACKUP_BEFORE_DEPLOY=false; shift ;;
        --skip-migrate) RUN_MIGRATIONS=false; shift ;;
        --rollback) ROLLBACK=true; shift ;;
        --env=*) ENV="${1#*=}"; shift ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

echo "═════════════════════════════════════════════════════════"
echo "  CodeGuard AI — Deployment"
echo "  Environment: $ENV"
echo "═════════════════════════════════════════════════════════"
echo ""

# ── Pre-deployment checks ────────────────────────────────────────
echo "🔍 Running pre-deployment checks..."

# Check Python is available
if ! command -v python3 &>/dev/null; then
    echo "❌ Python 3 is not installed"; exit 1
fi
echo "  ✅ Python 3 available"

# Check PostgreSQL is running
if ! systemctl is-active --quiet postgresql 2>/dev/null; then
    echo "⚠️  PostgreSQL may not be running"
else
    echo "  ✅ PostgreSQL running"
fi

# Check Redis is running (if enabled)
if systemctl is-active --quiet redis-server 2>/dev/null || systemctl is-active --quiet redis 2>/dev/null; then
    echo "  ✅ Redis running"
else
    echo "⚠️  Redis may not be running"
fi

# Check .env.production exists
if [ ! -f ".env.production" ] && [ ! -f ".env.production.local" ]; then
    echo "❌ Production environment file not found"; exit 1
fi
echo "  ✅ Production environment file found"

# Check certs exist
if [ ! -f "certs/jwt_private.pem" ] || [ ! -f "certs/jwt_public.pem" ]; then
    echo "⚠️  JWT certificates not found. Run: make certs-generate"
    echo "  Generating now..."
    bash backend/scripts/setup-tls.sh self-signed
fi
echo "  ✅ JWT certificates present"

# Check for placeholder secrets
for envfile in .env.production .env.production.local; do
    if [ -f "$envfile" ]; then
        if grep -qE "change_me|CHANGE_ME" "$envfile" 2>/dev/null; then
            echo "⚠️  $envfile contains placeholder values!"
            echo "   Replace all CHANGE_ME values before deploying."
            read -p "Continue anyway? [y/N]: " confirm
            [ "$confirm" != "y" ] && exit 1
        fi
    fi
done

# ── Rollback ────────────────────────────────────────────────────
if [ "$ROLLBACK" = true ]; then
    echo ""
    echo "⏪ Rolling back to previous deployment..."
    sudo systemctl restart "$API_SERVICE" || true
    sudo systemctl restart "$CELERY_SERVICE" || true
    echo "✅ Rollback complete (services restarted with previous code)"
    exit 0
fi

# ── Backup ───────────────────────────────────────────────────────
if [ "$BACKUP_BEFORE_DEPLOY" = true ]; then
    echo ""
    echo "📦 Creating pre-deployment database backup..."
    bash deploy/db-backup.sh
    echo "✅ Backup complete"
fi

# ── Pull latest code ─────────────────────────────────────────────
echo ""
echo "📥 Updating code..."
GIT_SHA=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
echo "   Git SHA: $GIT_SHA"

# ── Install dependencies ─────────────────────────────────────────
echo ""
echo "📦 Installing backend dependencies..."
cd backend
source venv/bin/activate 2>/dev/null || python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt -q
cd ..

echo "📦 Building frontend..."
cd frontend
npm install --silent
npm run build
cd ..

# ── Database Migrations ──────────────────────────────────────────
if [ "$RUN_MIGRATIONS" = true ]; then
    echo ""
    echo "🔄 Running database migrations..."
    cd backend
    source venv/bin/activate
    alembic upgrade head
    cd ..
    echo "✅ Migrations complete"
fi

# ── Deploy (Restart Services) ────────────────────────────────────
echo ""
echo "🚀 Restarting services..."

sudo systemctl restart "$API_SERVICE"
sudo systemctl restart "$CELERY_SERVICE"

# ── Health Check ──────────────────────────────────────────────────
echo ""
echo "🏥 Running post-deployment health check..."
ELAPSED=0
until [ $ELAPSED -ge $HEALTH_TIMEOUT ]; do
    STATUS=$(curl -sf http://localhost:8000/api/v1/health 2>/dev/null | python3 -c 'import json,sys; print(json.load(sys.stdin).get("status","unknown"))' 2>/dev/null || echo "unhealthy")

    if [ "$STATUS" = "healthy" ]; then
        echo "✅ API is healthy"
        break
    fi

    sleep $HEALTH_INTERVAL
    ELAPSED=$((ELAPSED + HEALTH_INTERVAL))
    echo "   ... API status: $STATUS (${ELAPSED}s/${HEALTH_TIMEOUT}s)"
done

if [ $ELAPSED -ge $HEALTH_TIMEOUT ]; then
    echo ""
    echo "❌ DEPLOYMENT FAILED — API health check timed out"
    echo "   Check logs: journalctl -u codeguard-api -n 100"
    echo "   Rollback:   ./deploy/deploy.sh --rollback"
    exit 1
fi

# ── Verify services ──────────────────────────────────────────────
echo ""
echo "📊 Service status:"
sudo systemctl is-active "$API_SERVICE"
sudo systemctl is-active "$CELERY_SERVICE"

echo ""
echo "═════════════════════════════════════════════════════════"
echo "  ✅ Deployment Complete"
echo "  Environment: $ENV"
echo "  Version:     $GIT_SHA"
echo "  Time:        $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "═════════════════════════════════════════════════════════"