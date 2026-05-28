#!/bin/bash
# CodeGuard AI - RS256 JWT Key Generation Script
# Generates RSA key pairs for JWT token signing and verification.

set -e

KEYS_DIR="${1:-../certs}"
PRIVATE_KEY="$KEYS_DIR/jwt_private.pem"
PUBLIC_KEY="$KEYS_DIR/jwt_public.pem"

echo "CodeGuard AI - RS256 JWT Key Generation"
echo "========================================="

mkdir -p "$KEYS_DIR"

if [ -f "$PRIVATE_KEY" ] || [ -f "$PUBLIC_KEY" ]; then
    echo "Warning: Key files already exist in $KEYS_DIR/"
    read -p "Overwrite? (y/N): " confirm
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        echo "Aborted."
        exit 0
    fi
fi

echo "Generating RSA private key..."
openssl genrsa -out "$PRIVATE_KEY" 2048 2>/dev/null

echo "Generating RSA public key..."
openssl rsa -in "$PRIVATE_KEY" -pubout -out "$PUBLIC_KEY" 2>/dev/null

chmod 600 "$PRIVATE_KEY"
chmod 644 "$PUBLIC_KEY"

echo ""
echo "Keys generated successfully:"
echo "  Private key: $PRIVATE_KEY"
echo "  Public key:  $PUBLIC_KEY"
echo ""
echo "Add these to your .env file:"
echo "  JWT_ALGORITHM=RS256"
echo "  JWT_PRIVATE_KEY_PATH=/app/certs/jwt_private.pem"
echo "  JWT_PUBLIC_KEY_PATH=/app/certs/jwt_public.pem"