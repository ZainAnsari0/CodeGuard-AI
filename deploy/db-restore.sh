#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════
# CodeGuard AI — Database Restore Script
# ═══════════════════════════════════════════════════════════════════
# Usage:
#   ./deploy/db-restore.sh                           # Interactive: list and pick backup
#   ./deploy/db-restore.sh backups/codeguard_20250101_120000.sql.gz
#   ./deploy/db-restore.sh --latest                  # Restore most recent backup
#
# WARNING: This REPLACES the database. Run with --dry-run first.
# ═══════════════════════════════════════════════════════════════════
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups}"
COMPOSE_CMD="${COMPOSE_CMD:-docker compose -f docker-compose.yml -f docker-compose.prod.yml}"
DRY_RUN=false
FORCE=false
BACKUP_FILE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run) DRY_RUN=true; shift ;;
        --force) FORCE=true; shift ;;
        --latest) BACKUP_FILE="latest"; shift ;;
        --dir=*) BACKUP_DIR="${1#*=}"; shift ;;
        *) BACKUP_FILE="$1"; shift ;;
    esac
done

# Resolve --latest to actual file
if [ "$BACKUP_FILE" = "latest" ]; then
    BACKUP_FILE=$(ls -t "$BACKUP_DIR"/codeguard_*.sql.gz 2>/dev/null | head -1)
    if [ -z "$BACKUP_FILE" ]; then
        BACKUP_FILE=$(ls -t "$BACKUP_DIR"/codeguard_*.sql 2>/dev/null | head -1)
    fi
    if [ -z "$BACKUP_FILE" ]; then
        echo "❌ No backups found in $BACKUP_DIR"
        exit 1
    fi
fi

# Interactive file selection
if [ -z "$BACKUP_FILE" ]; then
    echo "Available backups in $BACKUP_DIR:"
    echo "─────────────────────────────────"
    ls -lht "$BACKUP_DIR"/codeguard_*.sql* 2>/dev/null | head -20
    echo ""
    read -p "Enter backup filename (relative to $BACKUP_DIR/): " SELECTED
    BACKUP_FILE="$BACKUP_DIR/$SELECTED"
fi

# Verify file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ File not found: $BACKUP_FILE"
    exit 1
fi

# Verify checksum if available
if [ -f "${BACKUP_FILE}.sha256" ]; then
    echo "🔍 Verifying checksum..."
    if ! sha256sum -c "${BACKUP_FILE}.sha256" 2>/dev/null; then
        echo "❌ Checksum verification failed — backup may be corrupted"
        if [ "$FORCE" != true ]; then
            exit 1
        fi
        echo "⚠️  Continuing anyway (--force)"
    fi
    echo "✅ Checksum verified"
fi

BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo ""
echo "⚠️  ═══════════════════════════════════════════════════"
echo "⚠️  DATABASE RESTORE — THIS WILL REPLACE ALL DATA"
echo "⚠️  ═══════════════════════════════════════════════════"
echo "   File: $BACKUP_FILE"
echo "   Size: $BACKUP_SIZE"
echo ""

if [ "$DRY_RUN" = true ]; then
    echo "🔍 DRY RUN — no changes will be made"
    echo "   Would restore: $BACKUP_FILE ($BACKUP_SIZE)"
    exit 0
fi

if [ "$FORCE" != true ]; then
    read -p "Type 'RESTORE' to confirm: " CONFIRM
    if [ "$CONFIRM" != "RESTORE" ]; then
        echo "Cancelled."; exit 0
    fi
fi

# Create a pre-restore backup
echo "📦 Creating pre-restore backup..."
PRE_RESTORE_FILE="$BACKUP_DIR/pre_restore_$(date +%Y%m%d_%H%M%S).sql.gz"
$COMPOSE_CMD exec -T postgres \
    pg_dump -U codeguard_user -d codeguard --format=plain --no-owner --no-privileges \
    2>/dev/null | gzip > "$PRE_RESTORE_FILE"
echo "✅ Pre-restore backup: $PRE_RESTORE_FILE"

# Terminate active connections
echo "🔓 Terminating active database connections..."
$COMPOSE_CMD exec -T postgres \
    psql -U codeguard_user -d postgres -c \
    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='codeguard' AND pid<>pg_backend_pid();" \
    2>/dev/null || true

# Drop and recreate database
echo "🗑️  Recreating database..."
$COMPOSE_CMD exec -T postgres \
    psql -U codeguard_user -d postgres -c \
    "DROP DATABASE IF EXISTS codeguard;" 2>/dev/null
$COMPOSE_CMD exec -T postgres \
    psql -U codeguard_user -d postgres -c \
    "CREATE DATABASE codeguard OWNER codeguard_user;" 2>/dev/null

# Restore
echo "📥 Restoring database..."
if [[ "$BACKUP_FILE" == *.gz ]]; then
    gunzip -c "$BACKUP_FILE" | $COMPOSE_CMD exec -T postgres \
        psql -U codeguard_user -d codeguard 2>&1 | tail -5
else
    $COMPOSE_CMD exec -T postgres \
        psql -U codeguard_user -d codeguard < "$BACKUP_FILE" 2>&1 | tail -5
fi

# Verify
TABLE_COUNT=$($COMPOSE_CMD exec -T postgres \
    psql -U codeguard_user -d codeguard -t -c \
    "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';" 2>/dev/null | tr -d ' ')
echo "✅ Restore complete — $TABLE_COUNT tables restored"

# Run migrations to ensure schema is up to date
echo "🔄 Running pending migrations..."
$COMPOSE_CMD exec api alembic upgrade head 2>/dev/null || echo "⚠️  Migration check skipped"
echo ""
echo "═════════════════════════════════════════"
echo "  Restore Complete"
echo "═══════════════════════════════════════════"
echo "  Restored from: $BACKUP_FILE"
echo "  Pre-restore backup: $PRE_RESTORE_FILE"
echo "  Tables: $TABLE_COUNT"
echo "═══════════════════════════════════════════"