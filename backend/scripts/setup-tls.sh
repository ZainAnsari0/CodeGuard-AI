#!/usr/bin/env bash
# CodeGuard AI — TLS Certificate Setup
# Generates self-signed certs for local/dev or uses certbot for production.
#
# Usage:
#   ./setup-tls.sh              # Generate self-signed certs (dev/localhost)
#   ./setup-tls.sh production   # Request Let's Encrypt certs (requires domain)
#   ./setup-tls.sh self-signed  # Explicitly request self-signed certs

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
CERTS_DIR="${PROJECT_DIR}/../certs"

# ── Configuration ──────────────────────────────────────────
DOMAIN="${DOMAIN:-localhost}"
KEY_FILE="${CERTS_DIR}/jwt_private.pem"
CERT_FILE="${CERTS_DIR}/jwt_public.pem"
TLS_KEY="${CERTS_DIR}/tls_private.key"
TLS_CERT="${CERTS_DIR}/tls_cert.pem"
TLS_FULLCHAIN="${CERTS_DIR}/fullchain.pem"

MODE="${1:-self-signed}"

echo "=========================================="
echo " CodeGuard AI — TLS Certificate Setup"
echo " Mode: ${MODE}"
echo " Domain: ${DOMAIN}"
echo " Certs dir: ${CERTS_DIR}"
echo "=========================================="
echo ""

# ── Create certs directory ─────────────────────────────────
mkdir -p "${CERTS_DIR}"

generate_jwt_rs256_keys() {
    echo "[1/2] generating RS256 JWT key pair..."

    if [ -f "${KEY_FILE}" ]; then
        echo "  JWT private key already exists — skipping."
    else
        openssl genrsa -out "${KEY_FILE}" 4096
        chmod 600 "${KEY_FILE}"
        echo "  Generated: ${KEY_FILE}"
    fi

    if [ -f "${CERT_FILE}" ]; then
        echo "  JWT public key already exists — skipping."
    else
        openssl rsa -in "${KEY_FILE}" -pubout -out "${CERT_FILE}"
        chmod 644 "${CERT_FILE}"
        echo "  Generated: ${CERT_FILE}"
    fi
}

generate_self_signed_tls() {
    echo "[2/2] generating self-signed TLS certificate..."

    if [ -f "${TLS_CERT}" ] && [ -f "${TLS_KEY}" ]; then
        echo "  TLS certificate already exists — skipping."
        return
    fi

    openssl req -x509 \
        -days 365 \
        -newkey rsa:4096 \
        -keyout "${TLS_KEY}" \
        -out "${TLS_CERT}" \
        -subj "/C=PK/ST=Punjab/L=Lahore/O=CodeGuard AI/CN=${DOMAIN}" \
        -addext "subjectAltName=DNS:${DOMAIN},DNS:www.${DOMAIN},IP:127.0.0.1"

    cp "${TLS_CERT}" "${TLS_FULLCHAIN}"

    chmod 600 "${TLS_KEY}"
    chmod 644 "${TLS_CERT}"

    echo "  Generated: ${TLS_KEY}"
    echo "  Generated: ${TLS_CERT}"
    echo "  Generated: ${TLS_FULLCHAIN}"
}

request_letsencrypt() {
    echo "[2/2] Requesting Let's Encrypt certificate for ${DOMAIN}..."

    if ! command -v certbot &>/dev/null; then
        echo "  certbot not found. Installing..."
        if command -v apt-get &>/dev/null; then
            sudo apt-get update -qq && sudo apt-get install -y -qq certbot
        elif command -v yum &>/dev/null; then
            sudo yum install -y certbot
        else
            echo "ERROR: Cannot install certbot. Please install it manually."
            exit 1
        fi
    fi

    # Stop nginx if running (certbot needs port 80)
    docker compose -f "${PROJECT_DIR}/../docker-compose.yml" \
        -f "${PROJECT_DIR}/../docker-compose.prod.yml" \
        stop frontend 2>/dev/null || true

    echo "  Requesting certificate..."
    sudo certbot certonly --standalone \
        -d "${DOMAIN}" \
        -d "www.${DOMAIN}" \
        --non-interactive --agree-tos --email "admin@${DOMAIN}"

    local le_dir="/etc/letsencrypt/live/${DOMAIN}"
    cp "${le_dir}/privkey.pem" "${TLS_KEY}"
    cp "${le_dir}/fullchain.pem" "${TLS_FULLCHAIN}"
    cp "${le_dir}/cert.pem" "${TLS_CERT}"

    chmod 600 "${TLS_KEY}"
    chmod 644 "${TLS_CERT}" "${TLS_FULLCHAIN}"

    echo "  Copied Let's Encrypt certs to ${CERTS_DIR}"

    # Restart nginx
    docker compose -f "${PROJECT_DIR}/../docker-compose.yml" \
        -f "${PROJECT_DIR}/../docker-compose.prod.yml" \
        start frontend 2>/dev/null || true
}

validate_certs() {
    echo ""
    echo "Validating certificates..."

    if [ -f "${KEY_FILE}" ] && [ -f "${CERT_FILE}" ]; then
        echo "  ✓ JWT RS256 keys present"
    else
        echo "  ✗ JWT RS256 keys missing"
        return 1
    fi

    if [ -f "${TLS_KEY}" ] && [ -f "${TLS_CERT}" ]; then
        echo "  ✓ TLS certificate present"
        echo "  Certificate details:"
        openssl x509 -in "${TLS_CERT}" -noout -subject -dates 2>/dev/null || echo "  (unable to read cert details)"
    else
        echo "  ✗ TLS certificate missing"
        return 1
    fi

    return 0
}

# ── Main ───────────────────────────────────────────────────
case "${MODE}" in
    production)
        generate_jwt_rs256_keys
        request_letsencrypt
        ;;
    self-signed|"")
        generate_jwt_rs256_keys
        generate_self_signed_tls
        ;;
    *)
        echo "Usage: $0 [self-signed|production]"
        echo "  self-signed  — Generate self-signed certs (default, for dev/localhost)"
        echo "  production   — Request Let's Encrypt certs (requires domain + port 80)"
        exit 1
        ;;
esac

validate_certs

echo ""
echo "=========================================="
echo " TLS setup complete!"
echo " Mode: ${MODE}"
echo " JWT key: ${KEY_FILE}"
echo " TLS cert: ${TLS_CERT}"
echo "=========================================="