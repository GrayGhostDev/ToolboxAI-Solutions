#!/bin/bash
# ============================================
# SSL Certificate Generation Script
# ============================================
# Generates self-signed certificates for development and testing
# For production, use Let's Encrypt or a proper CA
# ============================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CERT_DIR="${SCRIPT_DIR}"
DAYS_VALID=365
COUNTRY="US"
STATE="California"
CITY="San Francisco"
ORG="ToolBoxAI Solutions"
OU="Development"
COMMON_NAME="${1:-toolboxai.local}"

echo "============================================"
echo "SSL Certificate Generation"
echo "============================================"
echo "Certificate Directory: ${CERT_DIR}"
echo "Common Name: ${COMMON_NAME}"
echo "Valid for: ${DAYS_VALID} days"
echo "============================================"

# Check if OpenSSL is installed
if ! command -v openssl &> /dev/null; then
    echo "❌ Error: OpenSSL is not installed"
    echo "Please install OpenSSL and try again"
    exit 1
fi

# Generate private key
echo "📝 Generating private key..."
openssl genrsa -out "${CERT_DIR}/privkey.pem" 4096

# Generate certificate signing request (CSR)
echo "📝 Generating certificate signing request..."
openssl req -new \
    -key "${CERT_DIR}/privkey.pem" \
    -out "${CERT_DIR}/csr.pem" \
    -subj "/C=${COUNTRY}/ST=${STATE}/L=${CITY}/O=${ORG}/OU=${OU}/CN=${COMMON_NAME}"

# Generate self-signed certificate
echo "📝 Generating self-signed certificate..."
openssl x509 -req \
    -days ${DAYS_VALID} \
    -in "${CERT_DIR}/csr.pem" \
    -signkey "${CERT_DIR}/privkey.pem" \
    -out "${CERT_DIR}/fullchain.pem" \
    -extfile <(printf "subjectAltName=DNS:${COMMON_NAME},DNS:*.${COMMON_NAME},DNS:localhost,IP:127.0.0.1")

# Generate Diffie-Hellman parameters (for stronger security)
echo "📝 Generating Diffie-Hellman parameters (this may take a while)..."
openssl dhparam -out "${CERT_DIR}/dhparam.pem" 2048

# Set proper permissions
chmod 600 "${CERT_DIR}/privkey.pem"
chmod 644 "${CERT_DIR}/fullchain.pem"
chmod 644 "${CERT_DIR}/dhparam.pem"

# Clean up CSR
rm -f "${CERT_DIR}/csr.pem"

echo ""
echo "✅ SSL certificates generated successfully!"
echo ""
echo "Files created:"
echo "  - ${CERT_DIR}/privkey.pem      (Private key - keep secure!)"
echo "  - ${CERT_DIR}/fullchain.pem    (Certificate)"
echo "  - ${CERT_DIR}/dhparam.pem      (DH parameters)"
echo ""
echo "Certificate details:"
openssl x509 -in "${CERT_DIR}/fullchain.pem" -noout -subject -dates -issuer
echo ""
echo "⚠️  WARNING: This is a self-signed certificate for development only!"
echo "⚠️  For production, use Let's Encrypt or a proper Certificate Authority"
echo ""
echo "To use with Nginx, update your server block:"
echo "  ssl_certificate     /etc/nginx/ssl/fullchain.pem;"
echo "  ssl_certificate_key /etc/nginx/ssl/privkey.pem;"
echo "  ssl_dhparam         /etc/nginx/ssl/dhparam.pem;"
echo ""
echo "To trust this certificate in your browser (macOS):"
echo "  sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain ${CERT_DIR}/fullchain.pem"
echo ""
