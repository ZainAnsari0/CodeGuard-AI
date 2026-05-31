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
#   COMPOSE_CMD     — Docker compose command
#   RETENTION_DAYS  — Days to keep backups (default: 30)
# ═══════════════════════════════════════════════════════════════════
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups}"
COMPOSE_CMD="${COMPOSE_CMD:-docker compose -f docker-compose.yml -f docker-compose.prod.yml}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
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

if [ "$COMPRESS" = true ]; then
    BACKUP_FILE="$BACKUP_DIR/codeguard_${TIMESTAMP}.sql.gz"
    $COMPOSE_CMD exec -T postgres \
        pg_dump -U codeguard_user -d codeguard --format=plain --no-owner --no-privileges \
        2>/dev/null | gzip > "$BACKUP_FILE"
else
    BACKUP_FILE="$BACKUP_DIR/codeguard_${TIMESTAMP}.sql"
    $COMPOSE_CMD exec -T postgres \
        pg_dump -U codeguard_user -d codeguard --format=plain --no-owner --no-privileges \
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