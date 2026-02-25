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
# Required env vars: MINDSDB_PASSWORD, MCPGATEWAY_BEARER_TOKEN
# Optional env vars: MINDSDB_HOST, MINDSDB_HTTP_PORT, MINDSDB_USERNAME,
#                    MCPGATEWAY_URL
set -euo pipefail

# Source .env if present (already-exported env vars take precedence)
if [ -f .env ]; then
  while IFS= read -r line || [ -n "$line" ]; do
    # Skip comments and blank lines
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    [[ -z "${line// /}" ]] && continue
    # Strip optional 'export ' prefix
    line="${line#export }"
    key="${line%%=*}"
    key="${key// /}"
    [ -z "$key" ] && continue
    # Only set if not already in the environment
    if [ -z "${!key+x}" ]; then
      val="${line#*=}"
      # Strip surrounding quotes (single or double)
      val="${val%\"}" && val="${val#\"}"
      val="${val%\'}" && val="${val#\'}"
      export "$key=$val"
    fi
  done < .env
fi

MINDSDB_HOST="${MINDSDB_HOST:-localhost}"
MINDSDB_PORT="${MINDSDB_HTTP_PORT:-47334}"
MINDSDB_USER="${MINDSDB_USERNAME:-admin}"
MINDSDB_PASS="${MINDSDB_PASSWORD:?MINDSDB_PASSWORD is required — set in .env or export before running}"
MCPGATEWAY_URL="${MCPGATEWAY_URL:-http://localhost:${PORT:-4444}}"
MCPGATEWAY_BEARER_TOKEN="${MCPGATEWAY_BEARER_TOKEN:?MCPGATEWAY_BEARER_TOKEN is required — set in .env or export before running}"

# Step 1: Get new token from MindsDB
# Credentials are piped via stdin to avoid exposure in ps/process lists.
echo "Requesting token from MindsDB at ${MINDSDB_HOST}:${MINDSDB_PORT}..."
TOKEN=$(printf '{"username":"%s","password":"%s"}' "${MINDSDB_USER}" "${MINDSDB_PASS}" | \
  curl -sf -X POST \
  -H "Content-Type: application/json" \
  --data-binary @- \
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
GATEWAY_ID=$(curl -sf "${MCPGATEWAY_URL}/gateways" \
  -H "Authorization: Bearer ${MCPGATEWAY_BEARER_TOKEN}" | \
  jq -r '.[] | select(.name == "mindsdb") | .id')

if [ -n "${GATEWAY_ID}" ] && [ "${GATEWAY_ID}" != "null" ]; then
  curl -sf -X PUT "${MCPGATEWAY_URL}/gateways/${GATEWAY_ID}" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer ${MCPGATEWAY_BEARER_TOKEN}" \
    -d '{"auth_token": "'"${TOKEN}"'"}'
  echo "Context Forge gateway ${GATEWAY_ID} updated with new token"
else
  echo "WARNING: Could not find MindsDB gateway in Context Forge" >&2
  echo "Register the gateway first: POST /gateways with name='mindsdb'" >&2
fi

echo "MindsDB token refreshed successfully"
