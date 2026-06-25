#!/usr/bin/env bash
# CodeGuard AI — Database Restore Script
# Restores a PostgreSQL database from a compressed backup file.
#
# Usage:
#   ./restore-db.sh backups/codeguard_codeguard_20260528_020000.sql.gz
#
# WARNING: This will stop API and Celery services during restore
#          to prevent data corruption from concurrent writes.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# ── Configuration ──────────────────────────────────────────
POSTGRES_DB="${POSTGRES_DB:-codeguard}"
POSTGRES_USER="${POSTGRES_USER:-codeguard_user}"
POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"

# ── Validate arguments ─────────────────────────────────────
if [ $# -ne 1 ]; then
    echo "Usage: $0 <backup_file.sql.gz>"
    echo ""
    echo "Available backups:"
    ls -1ht "${PROJECT_DIR}/backups/"codeguard_*.sql.gz 2>/dev/null || echo "  (no backups found)"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "${BACKUP_FILE}" ]; then
    echo "ERROR: Backup file not found: ${BACKUP_FILE}"
    exit 1
fi

# ── Confirm restore ─────────────────────────────────────────
echo "=========================================="
echo " CodeGuard AI — Database Restore"
echo "=========================================="
echo ""
echo "  Database: ${POSTGRES_DB}"
echo "  Host:     ${POSTGRES_HOST}:${POSTGRES_PORT}"
echo "  Backup:   ${BACKUP_FILE}"
echo ""
echo "  WARNING: This will:"
echo "  1. Stop API and Celery services"
echo "  2. Drop and recreate the database"
echo "  3. Restore from backup"
echo "  4. Restart all services"
echo ""
read -p "Are you sure you want to continue? [y/N] " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Restore cancelled."
    exit 0
fi

# ── Verify backup integrity ────────────────────────────────
echo ""
echo "[1/5] Verifying backup integrity..."
if ! gzip -t "${BACKUP_FILE}" 2>/dev/null; then
    echo "ERROR: Backup file is corrupted."
    exit 1
fi
echo "  ✓ Backup integrity verified"

# ── Check PostgreSQL is running ─────────────────────────────
echo "[2/5] Checking PostgreSQL..."
if ! psql -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -c "SELECT 1;" &>/dev/null; then
    echo "ERROR: Cannot connect to PostgreSQL at ${POSTGRES_HOST}:${POSTGRES_PORT}"
    exit 1
fi
echo "  ✓ PostgreSQL is accessible"

# ── Stop API and Celery services ────────────────────────────
echo "[3/5] Stopping API and Celery services..."
sudo systemctl stop codeguard-api 2>/dev/null || true
sudo systemctl stop codeguard-celery 2>/dev/null || true
sudo systemctl stop codeguard-celery-beat 2>/dev/null || true
echo "  ✓ Services stopped"

# ── Restore database ───────────────────────────────────────
echo "[4/5] Restoring database..."
gunzip -c "${BACKUP_FILE}" | PGPASSWORD="${PGPASSWORD:-}" psql \
    -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" \
    -U "${POSTGRES_USER}" -d "${POSTGRES_DB}"

if [ $? -eq 0 ]; then
    echo "  ✓ Database restored successfully"
else
    echo "  ✗ Database restore failed!"
    echo "  Restarting services anyway..."
fi

# ── Restart services ───────────────────────────────────────
echo "[5/5] Restarting services..."
sudo systemctl start codeguard-api 2>/dev/null || true
sudo systemctl start codeguard-celery 2>/dev/null || true
sudo systemctl start codeguard-celery-beat 2>/dev/null || true
echo "  ✓ Services restarted"

# ── Verify database connectivity ────────────────────────────
echo ""
echo "Verifying database connectivity..."
sleep 3

PGPASSWORD="${PGPASSWORD:-}" psql \
    -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" \
    -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -c "SELECT 1;" > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "  ✓ Database is accessible"
else
    echo "  ✗ Database connectivity check failed"
    echo "  Check service logs: journalctl -u codeguard-api -n 50"
fi

echo ""
echo "=========================================="
echo " Restore complete!"
echo " Backup: ${BACKUP_FILE}"
echo "=========================================="