#!/bin/sh
# -*- coding: utf-8 -*-
# MindsDB config generator — init container that writes config.json to /shared/.
#
# MindsDB's environment variables only support API keys for default models.
# Full model configuration (provider, model_name, base_url, api_version)
# requires a config.json file loaded via MINDSDB_CONFIG_PATH.
#
# This script reads MINDSDB_LLM_*, MINDSDB_EMBEDDING_*, and MINDSDB_RERANKING_*
# env vars and writes /shared/mindsdb-config.json.  MindsDB mounts the same
# volume read-only and sets MINDSDB_CONFIG_PATH=/shared/mindsdb-config.json.
#
# If no provider env vars are set, writes an empty JSON object so the config
# path is always valid (MindsDB ignores empty config gracefully).
#
# See: MindsDB docs — setup/custom-config.mdx

set -e

CONFIG_PATH="/shared/mindsdb-config.json"

# Build a JSON section for one model type.
# Usage: build_section <json_key> <env_prefix>
# Returns the JSON fragment (with leading comma) or empty string.
build_section() {
    _key="$1"
    _prefix="$2"

    eval _provider="\${MINDSDB_${_prefix}_PROVIDER:-}"
    [ -z "$_provider" ] && return

    eval _model="\${MINDSDB_${_prefix}_MODEL:-}"
    eval _base_url="\${MINDSDB_${_prefix}_BASE_URL:-}"
    eval _api_version="\${MINDSDB_${_prefix}_API_VERSION:-}"

    _json="\"${_key}\": { \"provider\": \"${_provider}\""
    [ -n "$_model" ]       && _json="${_json}, \"model_name\": \"${_model}\""
    [ -n "$_base_url" ]    && _json="${_json}, \"base_url\": \"${_base_url}\""
    [ -n "$_api_version" ] && _json="${_json}, \"api_version\": \"${_api_version}\""
    _json="${_json} }"

    # Write to a temp marker so the caller knows we produced output
    echo "$_json" >> /tmp/_sections
}

rm -f /tmp/_sections

build_section "default_llm"              "LLM"
build_section "default_embedding_model"  "EMBEDDING"
build_section "default_reranking_model"  "RERANKING"

if [ -f /tmp/_sections ]; then
    # Join sections with commas
    BODY=$(awk 'NR>1{printf ", "}{printf "%s", $0}' /tmp/_sections)
    echo "{ ${BODY} }" > "${CONFIG_PATH}"
    echo "[mindsdb-config] Generated config:"
    cat "${CONFIG_PATH}"
else
    echo "{}" > "${CONFIG_PATH}"
    echo "[mindsdb-config] No providers configured — wrote empty config."
fi

rm -f /tmp/_sections
