#!/usr/bin/env bash
# CodeGuard AI — Database Backup Script
# Creates a compressed PostgreSQL backup and rotates old backups.
#
# Usage:
#   ./backup-db.sh                    # Create backup
#   ./backup-db.sh --keep 14          # Keep last 14 backups (default: 7)
#
# Add to crontab for daily backups:
#   0 2 * * * /path/to/backup-db.sh >> /var/log/codeguard-backup.log 2>&1

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${PROJECT_DIR}/backups"
KEEP_DAYS="${KEEP_DAYS:-7}"
KEEP_COUNT="${KEEP_COUNT:-7}"

# ── Configuration ──────────────────────────────────────────
POSTGRES_CONTAINER="${POSTGRES_CONTAINER:-codeguard_postgres}"
POSTGRES_DB="${POSTGRES_DB:-codeguard}"
POSTGRES_USER="${POSTGRES_USER:-codeguard_user}"

# ── Parse arguments ────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case $1 in
        --keep)
            KEEP_COUNT="$2"
            shift 2
            ;;
        --container)
            POSTGRES_CONTAINER="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--keep N] [--container NAME]"
            exit 1
            ;;
    esac
done

# ── Create backup directory ────────────────────────────────
mkdir -p "${BACKUP_DIR}"

# ── Generate backup filename ──────────────────────────────
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
BACKUP_FILE="${BACKUP_DIR}/codeguard_${POSTGRES_DB}_${TIMESTAMP}.sql.gz"

echo "=========================================="
echo " CodeGuard AI — Database Backup"
echo " Database: ${POSTGRES_DB}"
echo " Container: ${POSTGRES_CONTAINER}"
echo " Output: ${BACKUP_FILE}"
echo "=========================================="
echo ""

# ── Check container is running ────────────────────────────
if ! docker ps --format '{{.Names}}' | grep -q "^${POSTGRES_CONTAINER}$"; then
    echo "ERROR: PostgreSQL container '${POSTGRES_CONTAINER}' is not running."
    echo "Available containers:"
    docker ps --format '{{.Names}}' | grep -i postgres || echo "  (none)"
    exit 1
fi

# ── Create backup ──────────────────────────────────────────
echo "[1/3] Creating backup..."
docker exec "${POSTGRES_CONTAINER}" \
    pg_dump -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" --clean --if-exists \
    | gzip > "${BACKUP_FILE}"

if [ ! -f "${BACKUP_FILE}" ]; then
    echo "ERROR: Backup file was not created."
    exit 1
fi

# ── Verify backup integrity ────────────────────────────────
echo "[2/3] Verifying backup integrity..."
if gzip -t "${BACKUP_FILE}" 2>/dev/null; then
    BACKUP_SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
    echo "  ✓ Backup verified successfully (${BACKUP_SIZE})"
else
    echo "  ✗ Backup integrity check failed!"
    rm -f "${BACKUP_FILE}"
    exit 1
fi

# ── Rotate old backups ─────────────────────────────────────
echo "[3/3] Rotating old backups (keeping last ${KEEP_COUNT})..."
cd "${BACKUP_DIR}"
ls -1t codeguard_*.sql.gz 2>/dev/null | tail -n +$((KEEP_COUNT + 1)) | xargs -r rm -f
REMAINING=$(ls -1 codeguard_*.sql.gz 2>/dev/null | wc -l)
echo "  ${REMAINING} backup(s) retained"

# ── Summary ─────────────────────────────────────────────────
echo ""
echo "=========================================="
echo " Backup complete!"
echo " File: ${BACKUP_FILE}"
echo " Size: ${BACKUP_SIZE}"
echo "=========================================="