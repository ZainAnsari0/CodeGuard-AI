#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════
# CodeGuard AI — Database Backup Script
# ═══════════════════════════════════════════════════════════════════
# Usage:
#   ./deploy/db-backup.sh                     # Compressed backup (default)
#   ./deploy/db-backup.sh --no-compress       # Plain SQL backup
#   ./deploy/db-backup.sh --upload            # Backup + upload to S3
#   ./deploy/db-backup.sh --retention=14      # Keep 14 days of backups
#
# Environment:
#   BACKUP_DIR      — Local backup directory (default: ./backups)
#   RETENTION_DAYS   — Days to keep backups (default: 30)
#   POSTGRES_HOST   — PostgreSQL host (default: localhost)
#   POSTGRES_PORT   — PostgreSQL port (default: 5432)
#   POSTGRES_DB     — Database name (default: codeguard)
#   POSTGRES_USER   — Database user (default: codeguard_user)
# ═══════════════════════════════════════════════════════════════════
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_DB="${POSTGRES_DB:-codeguard}"
POSTGRES_USER="${POSTGRES_USER:-codeguard_user}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
COMPRESS=true
UPLOAD=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --no-compress) COMPRESS=false; shift ;;
        --compress) COMPRESS=true; shift ;;
        --upload) UPLOAD=true; shift ;;
        --retention=*) RETENTION_DAYS="${1#*=}"; shift ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

mkdir -p "$BACKUP_DIR"

echo "🗄️  Starting database backup..."
echo "   Timestamp: $TIMESTAMP"
echo "   Host: $POSTGRES_HOST:$POSTGRES_PORT"
echo "   Database: $POSTGRES_DB"

if [ "$COMPRESS" = true ]; then
    BACKUP_FILE="$BACKUP_DIR/codeguard_${TIMESTAMP}.sql.gz"
    PGPASSWORD="${PGPASSWORD:-}" pg_dump \
        -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" \
        -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
        --format=plain --no-owner --no-privileges \
        2>/dev/null | gzip > "$BACKUP_FILE"
else
    BACKUP_FILE="$BACKUP_DIR/codeguard_${TIMESTAMP}.sql"
    PGPASSWORD="${PGPASSWORD:-}" pg_dump \
        -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" \
        -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
        --format=plain --no-owner --no-privileges \
        2>/dev/null > "$BACKUP_FILE"
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Backup failed"; exit 1
fi

BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
sha256sum "$BACKUP_FILE" > "${BACKUP_FILE}.sha256"
echo "✅ Backup created: $BACKUP_FILE ($BACKUP_SIZE)"

# Cleanup old backups
find "$BACKUP_DIR" -name "codeguard_*.sql*" -mtime +$RETENTION_DAYS -delete 2>/dev/null || true
echo "🧹 Cleaned up backups older than $RETENTION_DAYS days"

if [ "$UPLOAD" = true ] && command -v aws &>/dev/null; then
    S3_BUCKET="${S3_BUCKET:-s3://codeguard-backups/database}"
    aws s3 cp "$BACKUP_FILE" "$S3_BUCKET/$(basename $BACKUP_FILE)"
    aws s3 cp "${BACKUP_FILE}.sha256" "$S3_BUCKET/$(basename ${BACKUP_FILE}).sha256"
    echo "☁️  Uploaded to $S3_BUCKET"
fi