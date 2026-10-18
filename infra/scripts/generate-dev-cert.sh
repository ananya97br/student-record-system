#!/usr/bin/env sh
set -eu
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
CERT_DIR="$SCRIPT_DIR/../nginx/certs"
mkdir -p "$CERT_DIR"
CERT_DIR="$(CDPATH= cd -- "$CERT_DIR" && pwd)"
if [ ! -s "$CERT_DIR/dev.crt" ] || [ ! -s "$CERT_DIR/dev.key" ]; then
  openssl req -x509 -nodes -newkey rsa:2048 -days 825 \
    -keyout "$CERT_DIR/dev.key" -out "$CERT_DIR/dev.crt" \
    -subj "/C=XX/ST=Local/L=Local/O=Student Record System/CN=localhost" \
    -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"
  chmod 600 "$CERT_DIR/dev.key"
fi
echo "Development certificate ready in $CERT_DIR"
