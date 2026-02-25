#!/usr/bin/env bash
# Refreshes MindsDB bearer token, updates .env, and propagates to Context Forge gateway.
#
# With MINDSDB_HTTP_AUTH_TYPE=token (recommended), tokens are indefinitely valid.
# This script is a manual recovery tool for when:
#   - MindsDB is restarted with auth reset
#   - Token is invalidated or lost
#   - Switching from session-based to token-based auth
#
# If using session-based auth instead, schedule via cron every 20h and set
# http_permanent_session_lifetime explicitly in a mounted MindsDB config.json.
#
# Usage:
#   ./scripts/refresh-mindsdb-token.sh
#
# Required env vars: MINDSDB_PASSWORD, CONTEXT_FORGE_ADMIN_TOKEN
# Optional env vars: MINDSDB_HOST, MINDSDB_HTTP_PORT, MINDSDB_USERNAME,
#                    CONTEXT_FORGE_HOST
set -euo pipefail

MINDSDB_HOST="${MINDSDB_HOST:-localhost}"
MINDSDB_PORT="${MINDSDB_HTTP_PORT:-47334}"
MINDSDB_USER="${MINDSDB_USERNAME:-admin}"
MINDSDB_PASS="${MINDSDB_PASSWORD:?MINDSDB_PASSWORD is required}"
CONTEXT_FORGE_HOST="${CONTEXT_FORGE_HOST:-localhost:8000}"
CONTEXT_FORGE_ADMIN_TOKEN="${CONTEXT_FORGE_ADMIN_TOKEN:?CONTEXT_FORGE_ADMIN_TOKEN is required}"

# Step 1: Get new token from MindsDB
echo "Requesting token from MindsDB at ${MINDSDB_HOST}:${MINDSDB_PORT}..."
TOKEN=$(curl -sf -X POST \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"${MINDSDB_USER}\",\"password\":\"${MINDSDB_PASS}\"}" \
  "http://${MINDSDB_HOST}:${MINDSDB_PORT}/api/login" | jq -r '.token // .session')

if [ -z "${TOKEN}" ] || [ "${TOKEN}" = "null" ]; then
  echo "ERROR: Failed to obtain MindsDB token" >&2
  exit 1
fi

echo "Token obtained (${#TOKEN} chars)"

# Step 2: Update .env file (if present in current directory)
if [ -f .env ]; then
  if grep -q "^MINDSDB_AUTH_TOKEN=" .env 2>/dev/null; then
    sed -i'' -e "s|^MINDSDB_AUTH_TOKEN=.*|MINDSDB_AUTH_TOKEN=${TOKEN}|" .env
  else
    echo "MINDSDB_AUTH_TOKEN=${TOKEN}" >> .env
  fi
  echo "Updated .env with new token"
else
  echo "WARNING: No .env file found in current directory" >&2
fi

# Step 3: Propagate new token to Context Forge gateway record.
# Context Forge reads auth tokens from DB on each proxied request (not cached
# in memory), so this PUT takes effect immediately for all subsequent upstream calls.
GATEWAY_ID=$(curl -sf "http://${CONTEXT_FORGE_HOST}/gateways" \
  -H "Authorization: Bearer ${CONTEXT_FORGE_ADMIN_TOKEN}" | \
  jq -r '.[] | select(.name == "mindsdb") | .id')

if [ -n "${GATEWAY_ID}" ] && [ "${GATEWAY_ID}" != "null" ]; then
  curl -sf -X PUT "http://${CONTEXT_FORGE_HOST}/gateways/${GATEWAY_ID}" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer ${CONTEXT_FORGE_ADMIN_TOKEN}" \
    -d '{"auth_token": "'"${TOKEN}"'"}'
  echo "Context Forge gateway ${GATEWAY_ID} updated with new token"
else
  echo "WARNING: Could not find MindsDB gateway in Context Forge" >&2
  echo "Register the gateway first: POST /gateways with name='mindsdb'" >&2
fi

echo "MindsDB token refreshed successfully"
