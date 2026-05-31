#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════
# CodeGuard AI — Production Deployment Script
# ═══════════════════════════════════════════════════════════════════
# Usage:
#   ./deploy/deploy.sh                    # Full production deploy
#   ./deploy/deploy.sh --skip-backup      # Deploy without backup
#   ./deploy/deploy.sh --skip-migrate     # Deploy without migrations
#   ./deploy/deploy.sh --rollback         # Rollback to previous version
#   ./deploy/deploy.sh --canary           # Canary deploy (single API container)
#
# This script implements a zero-downtime rolling deployment strategy.
# ═══════════════════════════════════════════════════════════════════
set -euo pipefail

# ── Configuration ────────────────────────────────────────────────
ENV="${ENV:-production}"
COMPOSE_CMD="docker compose -f docker-compose.yml -f docker-compose.prod.yml"
BACKUP_BEFORE_DEPLOY=true
RUN_MIGRATIONS=true
HEALTH_TIMEOUT=120
HEALTH_INTERVAL=5
ROLLBACK=false
CANARY=false
SERVICES="api celery celery-beat frontend"

# ── Parse Arguments ──────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-backup) BACKUP_BEFORE_DEPLOY=false; shift ;;
        --skip-migrate) RUN_MIGRATIONS=false; shift ;;
        --rollback) ROLLBACK=true; shift ;;
        --canary) CANARY=true; shift ;;
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

# Check Docker is running
if ! docker info &>/dev/null; then
    echo "❌ Docker is not running"; exit 1
fi
echo "  ✅ Docker daemon running"

# Check .env.production exists
if [ ! -f ".env.production" ]; then
    echo "❌ .env.production not found"; exit 1
fi
echo "  ✅ .env.production found"

# Check certs exist
if [ ! -f "certs/jwt_private.pem" ] || [ ! -f "certs/jwt_public.pem" ]; then
    echo "⚠️  JWT certificates not found. Run: make certs-generate"
    echo "  Generating now..."
    cd backend && bash generate_keys.sh ../certs && cd ..
fi
echo "  ✅ JWT certificates present"

# Check for placeholder secrets
if grep -qE "change_me|CHANGE_ME" .env.production 2>/dev/null; then
    echo "⚠️  .env.production contains placeholder values!"
    echo "   Replace all CHANGE_ME values before deploying."
    read -p "Continue anyway? [y/N]: " confirm
    [ "$confirm" != "y" ] && exit 1
fi

# ── Rollback ────────────────────────────────────────────────────
if [ "$ROLLBACK" = true ]; then
    echo ""
    echo "⏪ Rolling back to previous deployment..."
    $COMPOSE_CMD down api celery celery-beat
    $COMPOSE_CMD up -d api celery celery-beat
    echo "✅ Rollback complete"
    exit 0
fi

# ── Backup ───────────────────────────────────────────────────────
if [ "$BACKUP_BEFORE_DEPLOY" = true ]; then
    echo ""
    echo "📦 Creating pre-deployment database backup..."
    bash deploy/db-backup.sh
    echo "✅ Backup complete"
fi

# ── Build ────────────────────────────────────────────────────────
echo ""
echo "🔨 Building images..."
GIT_SHA=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
echo "   Git SHA: $GIT_SHA"

docker build -t codeguard-api:$GIT_SHA -t codeguard-api:latest ./backend
docker build --build-arg NGINX_ENV=prod -t codeguard-frontend:$GIT_SHA -t codeguard-frontend:latest ./frontend
docker build -f ./backend/Dockerfile.celery -t codeguard-celery:$GIT_SHA -t codeguard-celery:latest ./backend

echo "✅ Images built"

# ── Database Migrations ──────────────────────────────────────────
if [ "$RUN_MIGRATIONS" = true ]; then
    echo ""
    echo "🔄 Running database migrations..."
    $COMPOSE_CMD exec -T api alembic upgrade head
    echo "✅ Migrations complete"
fi

# ── Deploy (Rolling Update) ──────────────────────────────────────
echo ""
echo "🚀 Deploying services..."

if [ "$CANARY" = true ]; then
    # Canary: only update API, monitor health before proceeding
    echo "   Canary mode: deploying API first..."
    $COMPOSE_CMD up -d --no-deps --scale api=2 api

    echo "   Waiting for canary container to pass health check..."
    ELAPSED=0
    until [ $ELAPSED -ge $HEALTH_TIMEOUT ]; do
        if curl -sf http://localhost:8000/api/v1/health | grep -q "healthy"; then
            echo "   ✅ Canary is healthy"
            break
        fi
        sleep $HEALTH_INTERVAL
        ELAPSED=$((ELAPSED + HEALTH_INTERVAL))
        echo "   ... waiting (${ELAPSED}s/${HEALTH_TIMEOUT}s)"
    done

    if [ $ELAPSED -ge $HEALTH_TIMEOUT ]; then
        echo "   ❌ Canary health check failed — rolling back"
        $COMPOSE_CMD up -d --no-deps --scale api=1 api
        exit 1
    fi

    # Scale back to single instance
    $COMPOSE_CMD up -d --no-deps --scale api=1 api
    echo "   ✅ Canary deploy complete"
else
    # Full rolling deploy
    for SERVICE in $SERVICES; do
        echo "   Deploying $SERVICE..."
        $COMPOSE_CMD up -d --no-deps $SERVICE
        sleep 5  # Brief delay between services
    done
fi

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
    echo "   Run 'make logs-api' to see logs"
    echo "   Run 'make deploy-rollback' to revert"
    exit 1
fi

# ── Verify all services ─────────────────────────────────────────
echo ""
echo "📊 Service status:"
$COMPOSE_CMD ps

echo ""
echo "═════════════════════════════════════════════════════════"
echo "  ✅ Deployment Complete"
echo "  Environment: $ENV"
echo "  Version:     $GIT_SHA"
echo "  Time:        $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "═════════════════════════════════════════════════════════"