#!/bin/sh
# -*- coding: utf-8 -*-
# MindsDB Docker entrypoint wrapper — generates config.json from env vars.
#
# MindsDB's environment variables only support API keys for default models.
# Full model configuration (provider, model_name, base_url, api_version)
# requires a config.json file loaded via MINDSDB_CONFIG_PATH.
#
# This script bridges the gap: it reads MINDSDB_LLM_*, MINDSDB_EMBEDDING_*,
# and MINDSDB_RERANKING_* env vars, assembles a config.json at runtime,
# and sets MINDSDB_CONFIG_PATH before exec-ing MindsDB.
#
# If no provider env vars are set, no config.json is generated and MindsDB
# starts with its built-in defaults (API keys still work via env vars).
#
# See: MindsDB docs — setup/custom-config.mdx

set -e

CONFIG_PATH="/tmp/mindsdb-config.json"

# Check if any model provider is configured
if [ -n "${MINDSDB_LLM_PROVIDER:-}" ] || \
   [ -n "${MINDSDB_EMBEDDING_PROVIDER:-}" ] || \
   [ -n "${MINDSDB_RERANKING_PROVIDER:-}" ]; then

    echo "[entrypoint] Generating MindsDB config from environment variables..."

    # Use Python (available in MindsDB image) to build valid JSON
    python3 -c "
import json, os

config = {}

sections = [
    ('default_llm', 'LLM'),
    ('default_embedding_model', 'EMBEDDING'),
    ('default_reranking_model', 'RERANKING'),
]

for section_key, prefix in sections:
    provider = os.environ.get(f'MINDSDB_{prefix}_PROVIDER', '')
    if not provider:
        continue

    section = {'provider': provider}

    model = os.environ.get(f'MINDSDB_{prefix}_MODEL', '')
    if model:
        section['model_name'] = model

    base_url = os.environ.get(f'MINDSDB_{prefix}_BASE_URL', '')
    if base_url:
        section['base_url'] = base_url

    api_version = os.environ.get(f'MINDSDB_{prefix}_API_VERSION', '')
    if api_version:
        section['api_version'] = api_version

    config[section_key] = section

with open('${CONFIG_PATH}', 'w') as f:
    json.dump(config, f, indent=2)

print(f'[entrypoint] Config written to ${CONFIG_PATH}:')
print(json.dumps(config, indent=2))
"

    export MINDSDB_CONFIG_PATH="${CONFIG_PATH}"
    echo "[entrypoint] MINDSDB_CONFIG_PATH=${CONFIG_PATH}"
else
    echo "[entrypoint] No model providers configured — using MindsDB defaults."
fi

# Exec the original MindsDB entrypoint
exec python3 -m mindsdb --api=http,mysql "$@"
