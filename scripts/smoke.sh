#!/usr/bin/env sh
set -eu
BASE_URL="${BASE_URL:-http://localhost:8000}"
CURL_EXTRA=""
case "$BASE_URL" in
  https://localhost:*|https://127.0.0.1:*) CURL_EXTRA="--insecure" ;;
esac
curl --fail --silent --show-error $CURL_EXTRA "$BASE_URL/health/live" >/dev/null
curl --fail --silent --show-error $CURL_EXTRA "$BASE_URL/api/health/ready" >/dev/null
curl --fail --silent --show-error $CURL_EXTRA "$BASE_URL/api/openapi.json" >/dev/null
echo "Smoke checks passed for $BASE_URL"
