#!/usr/bin/env bash
# seed-llm-providers.sh — Idempotent LLM provider & model seeding for ContextForge Gateway
#
# Reads provider/model definitions from a JSON config file and creates them
# via the Gateway REST API. Skips providers/models that already exist (by name).
#
# Usage:
#   ./scripts/seed-llm-providers.sh                          # defaults
#   ./scripts/seed-llm-providers.sh --config custom.json     # custom config
#   ./scripts/seed-llm-providers.sh --dry-run                # preview only
#
# Environment:
#   GATEWAY_URL        Gateway base URL           (default: http://localhost:8080)
#   GATEWAY_TOKEN      Bearer token for auth      (default: auto-generate via generate-jwt.sh)
#   SEED_CONFIG        Path to seed config JSON   (default: scripts/llm-seed-config.json)
#
# Requires: curl, jq
set -euo pipefail

# --- Defaults ---------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
GATEWAY_URL="${GATEWAY_URL:-http://localhost:8080}"
SEED_CONFIG="${SEED_CONFIG:-${SCRIPT_DIR}/llm-seed-config.json}"
DRY_RUN=false
VERBOSE=false

# --- Parse args -------------------------------------------------------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --config)   SEED_CONFIG="$2"; shift 2 ;;
    --url)      GATEWAY_URL="$2"; shift 2 ;;
    --token)    GATEWAY_TOKEN="$2"; shift 2 ;;
    --dry-run)  DRY_RUN=true; shift ;;
    --verbose)  VERBOSE=true; shift ;;
    -h|--help)
      echo "Usage: $0 [--config FILE] [--url URL] [--token TOKEN] [--dry-run] [--verbose]"
      exit 0
      ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

# --- Dependency check -------------------------------------------------------
for cmd in curl jq; do
  command -v "$cmd" >/dev/null 2>&1 || { echo "Error: $cmd is required but not installed." >&2; exit 1; }
done

# --- Config file check ------------------------------------------------------
if [[ ! -f "$SEED_CONFIG" ]]; then
  echo "Error: Seed config not found: $SEED_CONFIG" >&2
  echo "Create one from the template: scripts/llm-seed-config.json" >&2
  exit 1
fi

# --- Auth token -------------------------------------------------------------
if [[ -z "${GATEWAY_TOKEN:-}" ]]; then
  echo "ℹ  No GATEWAY_TOKEN set, generating one via gateway container..."

  # Detect docker compose command
  if command -v "docker" >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
  elif command -v "docker-compose" >/dev/null 2>&1; then
    COMPOSE_CMD="docker-compose"
  else
    echo "Error: No GATEWAY_TOKEN set and docker compose not available." >&2
    echo "Set GATEWAY_TOKEN manually or run from the project directory with Docker running." >&2
    exit 1
  fi

  # Generate token inside the gateway container (uses container's env: PLATFORM_ADMIN_EMAIL, JWT keys, etc.)
  PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
  # Run inside container so PLATFORM_ADMIN_EMAIL, JWT_PRIVATE_KEY_PATH, etc. resolve from container env
  GATEWAY_TOKEN="$($COMPOSE_CMD -f "${PROJECT_DIR}/docker-compose.yml" exec -T gateway \
    sh -c 'python3 -m mcpgateway.utils.create_jwt_token \
      --username "${PLATFORM_ADMIN_EMAIL:-admin@apollosai.dev}" \
      --exp 10080 --admin' 2>/dev/null)"

  if [[ -z "$GATEWAY_TOKEN" ]]; then
    echo "Error: Failed to generate token from gateway container." >&2
    echo "Ensure the gateway service is running: docker compose up -d gateway" >&2
    exit 1
  fi
  echo "✓  Token generated (${#GATEWAY_TOKEN} chars)"
fi

AUTH_HEADER="Authorization: Bearer ${GATEWAY_TOKEN}"

# --- Helper: API call -------------------------------------------------------
api_call() {
  local method="$1" endpoint="$2" data="${3:-}"
  local url="${GATEWAY_URL}${endpoint}"
  local args=(-s -w "\n%{http_code}" -H "$AUTH_HEADER" -H "Content-Type: application/json")

  if [[ -n "$data" ]]; then
    args+=(-X "$method" -d "$data")
  else
    args+=(-X "$method")
  fi

  if $VERBOSE; then
    echo "  → $method $url" >&2
    [[ -n "$data" ]] && echo "    $(echo "$data" | jq -c .)" >&2
  fi

  curl "${args[@]}" "$url"
}

# --- Parse response (body + http_code on last line) -------------------------
parse_response() {
  local response="$1"
  local body http_code
  http_code="$(echo "$response" | tail -1)"
  body="$(echo "$response" | sed '$d')"
  echo "$http_code"
  echo "$body"
}

# --- Fetch existing providers -----------------------------------------------
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ContextForge LLM Provider Seeder"
echo "  Gateway: $GATEWAY_URL"
echo "  Config:  $SEED_CONFIG"
$DRY_RUN && echo "  Mode:    DRY RUN (no changes)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Get existing providers
echo "Fetching existing providers..."
response="$(api_call GET "/llm/providers")"
http_code="$(echo "$response" | tail -1)"
body="$(echo "$response" | sed '$d')"

if [[ "$http_code" != "200" ]]; then
  echo "Error: Failed to fetch providers (HTTP $http_code)" >&2
  echo "$body" >&2
  exit 1
fi

# Build lookup of existing provider names → IDs
declare -A EXISTING_PROVIDERS
while IFS='|' read -r pname pid; do
  EXISTING_PROVIDERS["$pname"]="$pid"
done < <(echo "$body" | jq -r '.providers[]? | "\(.name)|\(.id)"' 2>/dev/null || true)

echo "  Found ${#EXISTING_PROVIDERS[@]} existing provider(s)"

# Get existing models
response="$(api_call GET "/llm/models")"
http_code="$(echo "$response" | tail -1)"
body="$(echo "$response" | sed '$d')"

declare -A EXISTING_MODELS
if [[ "$http_code" == "200" ]]; then
  while IFS='|' read -r mname mid; do
    EXISTING_MODELS["$mname"]="$mid"
  done < <(echo "$body" | jq -r '.models[]? | "\(.model_name)|\(.id)"' 2>/dev/null || true)
fi

echo "  Found ${#EXISTING_MODELS[@]} existing model(s)"
echo ""

# --- Seed providers ---------------------------------------------------------
PROVIDERS_CREATED=0
PROVIDERS_SKIPPED=0
MODELS_CREATED=0
MODELS_SKIPPED=0

provider_count="$(jq '.providers | length' "$SEED_CONFIG")"

for i in $(seq 0 $((provider_count - 1))); do
  provider_json="$(jq -c ".providers[$i]" "$SEED_CONFIG")"
  provider_name="$(echo "$provider_json" | jq -r '.name')"

  echo "Provider: $provider_name"

  # Check if provider already exists
  if [[ -n "${EXISTING_PROVIDERS[$provider_name]:-}" ]]; then
    provider_id="${EXISTING_PROVIDERS[$provider_name]}"
    echo "  ⏭  Already exists (id: ${provider_id:0:8}...)"
    PROVIDERS_SKIPPED=$((PROVIDERS_SKIPPED + 1))
  else
    # Extract provider payload (without the 'models' key)
    create_payload="$(echo "$provider_json" | jq -c 'del(.models)')"

    if $DRY_RUN; then
      echo "  🔸 Would create: $(echo "$create_payload" | jq -c '{name, provider_type, api_base}')"
      provider_id="DRY_RUN_ID"
      PROVIDERS_CREATED=$((PROVIDERS_CREATED + 1))
    else
      response="$(api_call POST "/llm/providers" "$create_payload")"
      http_code="$(echo "$response" | tail -1)"
      body="$(echo "$response" | sed '$d')"

      if [[ "$http_code" == "201" ]]; then
        provider_id="$(echo "$body" | jq -r '.id')"
        echo "  ✅ Created (id: ${provider_id:0:8}...)"
        PROVIDERS_CREATED=$((PROVIDERS_CREATED + 1))
      elif [[ "$http_code" == "409" ]]; then
        echo "  ⏭  Already exists (conflict)"
        # Try to get the ID from the existing list
        provider_id="${EXISTING_PROVIDERS[$provider_name]:-unknown}"
        PROVIDERS_SKIPPED=$((PROVIDERS_SKIPPED + 1))
      else
        echo "  ❌ Failed (HTTP $http_code): $body" >&2
        continue
      fi
    fi
  fi

  # --- Seed models for this provider ----------------------------------------
  model_count="$(echo "$provider_json" | jq '.models // [] | length')"

  for j in $(seq 0 $((model_count - 1))); do
    model_json="$(echo "$provider_json" | jq -c ".models[$j]")"
    model_name="$(echo "$model_json" | jq -r '.model_name')"

    if [[ -n "${EXISTING_MODELS[$model_name]:-}" ]]; then
      echo "    ⏭  Model '$model_name' already exists"
      MODELS_SKIPPED=$((MODELS_SKIPPED + 1))
    else
      # Add provider_id to model payload
      model_payload="$(echo "$model_json" | jq -c --arg pid "$provider_id" '. + {provider_id: $pid}')"

      if $DRY_RUN; then
        echo "    🔸 Would create model: $(echo "$model_payload" | jq -c '{model_name, model_id, supports_chat}')"
        MODELS_CREATED=$((MODELS_CREATED + 1))
      else
        response="$(api_call POST "/llm/models" "$model_payload")"
        http_code="$(echo "$response" | tail -1)"
        body="$(echo "$response" | sed '$d')"

        if [[ "$http_code" == "201" ]]; then
          model_id="$(echo "$body" | jq -r '.id')"
          echo "    ✅ Model '$model_name' created (id: ${model_id:0:8}...)"
          MODELS_CREATED=$((MODELS_CREATED + 1))
        elif [[ "$http_code" == "409" ]]; then
          echo "    ⏭  Model '$model_name' already exists (conflict)"
          MODELS_SKIPPED=$((MODELS_SKIPPED + 1))
        else
          echo "    ❌ Model '$model_name' failed (HTTP $http_code): $body" >&2
        fi
      fi
    fi
  done

  echo ""
done

# --- Summary ----------------------------------------------------------------
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Summary"
echo "  Providers: $PROVIDERS_CREATED created, $PROVIDERS_SKIPPED skipped"
echo "  Models:    $MODELS_CREATED created, $MODELS_SKIPPED skipped"
$DRY_RUN && echo "  (DRY RUN — no actual changes made)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
