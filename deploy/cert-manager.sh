#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════
# CodeGuard AI — TLS Certificate Management
# ═══════════════════════════════════════════════════════════════════
# Usage:
#   ./deploy/cert-manager.sh setup          # Initial Let's Encrypt certbot setup
#   ./deploy/cert-manager.sh renew          # Renew Let's Encrypt certificates
#   ./deploy/cert-manager.sh self-signed    # Generate self-signed certs (dev/staging)
#   ./deploy/cert-manager.sh check          # Check certificate expiry
#
# For production with Let's Encrypt:
#   1. Set DOMAIN and EMAIL environment variables
#   2. Run: ./deploy/cert-manager.sh setup
#   3. Add to crontab: 0 0 * * * /path/to/deploy/cert-manager.sh renew
# ═══════════════════════════════════════════════════════════════════
set -euo pipefail

DOMAIN="${DOMAIN:-codeguard.example.com}"
EMAIL="${EMAIL:-admin@codeguard.example.com}"
CERT_DIR="${CERT_DIR:-./certs}"
CERTBOT_WEBROOT="/var/www/certbot"

command=${1:-help}

case $command in
    setup)
        echo "🔐 Setting up Let's Encrypt for $DOMAIN..."
        mkdir -p "$CERT_DIR" "$CERTBOT_WEBROOT"

        # Check certbot is installed
        if ! command -v certbot &>/dev/null; then
            echo "❌ certbot is not installed. Install it first:"
            echo "   sudo apt install certbot   (Debian/Ubuntu)"
            echo "   sudo dnf install certbot    (Fedora)"
            exit 1
        fi

        # Initial certificate request
        echo "   Requesting initial certificate..."
        sudo certbot certonly \
            --webroot \
            --webroot-path="$CERTBOT_WEBROOT" \
            --email "$EMAIL" \
            --agree-tos \
            --no-eff-email \
            --non-interactive \
            -d "$DOMAIN" \
            -d "www.$DOMAIN"

        # Copy certs to expected location
        echo "   Installing certificates..."
        cp "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" "$CERT_DIR/fullchain.pem" 2>/dev/null || true
        cp "/etc/letsencrypt/live/$DOMAIN/privkey.pem" "$CERT_DIR/tls_private.key" 2>/dev/null || true
        chmod 600 "$CERT_DIR/tls_private.key"

        echo "   Setting up auto-renewal cron job..."
        (crontab -l 2>/dev/null; echo "0 0 * * * $(pwd)/deploy/cert-manager.sh renew >> /var/log/codeguard-cert-renew.log 2>&1") | sort -u | crontab -
        echo "✅ Certificate setup complete. Auto-renewal cron installed."
        ;;

    renew)
        echo "🔄 Renewing TLS certificates for $DOMAIN..."

        if command -v certbot &>/dev/null; then
            sudo certbot renew --quiet

            # Copy renewed certs
            cp "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" "$CERT_DIR/fullchain.pem" 2>/dev/null || true
            cp "/etc/letsencrypt/live/$DOMAIN/privkey.pem" "$CERT_DIR/tls_private.key" 2>/dev/null || true
            chmod 600 "$CERT_DIR/tls_private.key"

            # Reload nginx to pick up new certs
            echo "   Reloading nginx..."
            sudo systemctl reload nginx 2>/dev/null || \
                sudo nginx -s reload 2>/dev/null || \
                echo "   ⚠️  Could not reload nginx — reload manually"
            echo "✅ Certificates renewed and nginx reloaded"
        else
            echo "❌ certbot is not installed. Cannot renew certificates."
            exit 1
        fi
        ;;

    self-signed)
        echo "🔑 Generating self-signed TLS certificate (for dev/staging)..."
        mkdir -p "$CERT_DIR"

        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout "$CERT_DIR/tls_private.key" \
            -out "$CERT_DIR/fullchain.pem" \
            -subj "/CN=localhost/O=CodeGuard AI/C=US" \
            -addext "subjectAltName=DNS:localhost,DNS:codeguard.local,IP:127.0.0.1" 2>/dev/null

        chmod 600 "$CERT_DIR/tls_private.key"
        echo "✅ Self-signed certificate generated in $CERT_DIR/"
        echo "   Certificate: $CERT_DIR/fullchain.pem"
        echo "   Private key:  $CERT_DIR/tls_private.key"
        ;;

    check)
        echo "🔍 Checking TLS certificate expiry..."
        if [ -f "$CERT_DIR/fullchain.pem" ]; then
            EXPIRY=$(openssl x509 -enddate -noout -in "$CERT_DIR/fullchain.pem" 2>/dev/null | cut -d= -f2)
            DAYSLEFT=$(( ($(date -d "$EXPIRY" +%s) - $(date +%s)) / 86400 ))
            echo "   Certificate expires: $EXPIRY ($DAYS_LEFT days remaining)"
            if [ "$DAYSLEFT" -lt 30 ]; then
                echo "   ⚠️  Certificate expires in less than 30 days — run: ./deploy/cert-manager.sh renew"
            else
                echo "   ✅ Certificate is valid"
            fi
        else
            echo "   ❌ No TLS certificate found at $CERT_DIR/fullchain.pem"
            echo "   Run: ./deploy/cert-manager.sh setup (Let's Encrypt) or ./deploy/cert-manager.sh self-signed (dev)"
        fi

        # Check JWT keys
        echo ""
        echo "🔑 Checking JWT keys..."
        if [ -f "$CERT_DIR/jwt_public.pem" ]; then
            JWT_EXPIRY=$(openssl rsa -pubin -in "$CERT_DIR/jwt_public.pem" -text -noout 2>/dev/null | head -2)
            echo "   ✅ JWT public key present"
        else
            echo "   ⚠️  No JWT public key found — run: bash backend/scripts/setup-tls.sh"
        fi
        ;;

    help|*)
        echo "CodeGuard AI — Certificate Manager"
        echo ""
        echo "Usage: ./deploy/cert-manager.sh <command>"
        echo ""
        echo "Commands:"
        echo "  setup          Request initial Let's Encrypt certificate (requires certbot)"
        echo "  renew          Renew existing Let's Encrypt certificates"
        echo "  self-signed    Generate self-signed certificate (dev/staging)"
        echo "  check          Check certificate expiry dates"
        echo ""
        echo "Environment variables:"
        echo "  DOMAIN          Domain name (default: codeguard.example.com)"
        echo "  EMAIL           Admin email for Let's Encrypt"
        echo "  CERT_DIR        Certificate directory (default: ./certs)"
        ;;
esac