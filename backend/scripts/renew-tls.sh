#!/usr/bin/env bash
# CodeGuard AI — TLS Certificate Renewal
# Renews Let's Encrypt certificates and reloads nginx.
# Add to crontab: 0 3 * * * /path/to/renew-tls.sh >> /var/log/tls-renewal.log 2>&1

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
CERTS_DIR="${PROJECT_DIR}/../certs"
DOMAIN="${DOMAIN:-localhost}"

echo "$(date '+%Y-%m-%d %H:%M:%S') — Starting TLS renewal for ${DOMAIN}"

# ── Renew certificate ──────────────────────────────────────
if ! sudo certbot renew --quiet --force-renewal 2>/dev/null; then
    echo "ERROR: certbot renewal failed. Check certbot logs."
    exit 1
fi

# ── Copy renewed certs ─────────────────────────────────────
LE_DIR="/etc/letsencrypt/live/${DOMAIN}"

if [ -d "${LE_DIR}" ]; then
    sudo cp "${LE_DIR}/privkey.pem" "${CERTS_DIR}/tls_private.key"
    sudo cp "${LE_DIR}/fullchain.pem" "${CERTS_DIR}/fullchain.pem"
    sudo cp "${LE_DIR}/cert.pem" "${CERTS_DIR}/tls_cert.pem"
    chmod 600 "${CERTS_DIR}/tls_private.key"
    chmod 644 "${CERTS_DIR}/tls_cert.pem" "${CERTS_DIR}/fullchain.pem"
    echo "Copied renewed certificates to ${CERTS_DIR}"
else
    echo "ERROR: Let's Encrypt directory not found at ${LE_DIR}"
    exit 1
fi

# ── Reload nginx ──────────────────────────────────────────
echo "Reloading nginx..."
sudo systemctl reload nginx 2>/dev/null || sudo nginx -s reload 2>/dev/null || \
    echo "WARNING: Could not reload nginx — reload manually"

echo "$(date '+%Y-%m-%d %H:%M:%S') — TLS renewal complete for ${DOMAIN}"