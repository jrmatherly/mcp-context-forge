#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Atlassian auto-registration for MCP Context Forge.

Registers the Atlassian Rovo MCP server (Jira + Confluence + Compass) as a
federated gateway with OAuth 2.0 (3LO), optionally registers a custom
Bitbucket MCP server, and creates a virtual server.

The OAuth consent flow requires user interaction in a browser — this script
only pre-registers the gateway configuration.  Tools appear after the first
user completes OAuth authorization at auth.atlassian.com.

Environment variables:
    MCPGATEWAY_URL              - Gateway base URL (default: http://gateway:4444)
    MCF_DOMAIN                  - Public domain for OAuth callback (default: localhost:4444)
    ATLASSIAN_OAUTH_CLIENT_ID   - OAuth 2.0 (3LO) client ID (required)
    ATLASSIAN_OAUTH_CLIENT_SECRET - OAuth 2.0 (3LO) client secret (required)
    ATLASSIAN_OAUTH_SCOPES      - Comma-separated scopes (has sensible defaults)
    BITBUCKET_OAUTH_CLIENT_ID   - Bitbucket OAuth consumer key (optional)
    BITBUCKET_OAUTH_CLIENT_SECRET - Bitbucket OAuth consumer secret (optional)
    BITBUCKET_MCP_URL           - Bitbucket MCP server URL (default: http://bitbucket-mcp-server:8000/mcp)
    JWT_ALGORITHM               - JWT signing algorithm (default: HS256)
    JWT_SECRET_KEY              - JWT secret key for HS* algorithms
    JWT_PRIVATE_KEY_PATH        - Path to private key for RS* algorithms
    JWT_PUBLIC_KEY_PATH         - Path to public key for RS* algorithms
    JWT_AUDIENCE                - JWT audience claim (default: mcpgateway-api)
    JWT_ISSUER                  - JWT issuer claim (default: mcpgateway)
    PLATFORM_ADMIN_EMAIL        - Admin email for JWT (default: admin@apollosai.dev)
    TOKEN_EXPIRY                - JWT expiry in minutes (default: 10080)
"""

# Standard
import json
import os
import sys
import time
import urllib.error
import urllib.request

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

GATEWAY_URL = os.environ.get("MCPGATEWAY_URL", "http://gateway:4444")
MCF_DOMAIN = os.environ.get("MCF_DOMAIN", "localhost:4444")

# Atlassian OAuth (required)
ATLASSIAN_CLIENT_ID = os.environ.get("ATLASSIAN_OAUTH_CLIENT_ID", "")
ATLASSIAN_CLIENT_SECRET = os.environ.get("ATLASSIAN_OAUTH_CLIENT_SECRET", "")
ATLASSIAN_SCOPES = os.environ.get(
    "ATLASSIAN_OAUTH_SCOPES",
    "read:jira-work,write:jira-work,read:jira-user," "read:confluence-content.all,write:confluence-content," "read:confluence-space.summary",
)

# Bitbucket OAuth (optional — only registered if both are set)
BITBUCKET_CLIENT_ID = os.environ.get("BITBUCKET_OAUTH_CLIENT_ID", "")
BITBUCKET_CLIENT_SECRET = os.environ.get("BITBUCKET_OAUTH_CLIENT_SECRET", "")
# Bitbucket MCP server URL — must point to a running bitbucket-mcp-server instance
BITBUCKET_MCP_URL = os.environ.get("BITBUCKET_MCP_URL", "http://bitbucket-mcp-server:8000/mcp")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def wait_for_service(url: str, name: str, attempts: int = 60, interval: int = 2) -> None:
    """Block until *url* returns HTTP 200 or exhaust retries."""
    for i in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(url, timeout=5) as r:
                if r.status == 200:
                    print(f"  {name} is healthy")
                    return
        except Exception:
            pass
        print(f"  Waiting for {name}... ({i}/{attempts})")
        time.sleep(interval)
    print(f"  {name} not healthy after {attempts * interval}s")
    sys.exit(1)


def generate_admin_token() -> str:
    """Create a JWT with admin-bypass claims (teams: null + is_admin: true).

    Builds the token directly with PyJWT to avoid depending on mcpgateway
    internals (the package isn't pip-installed in the container image).
    """
    # Standard
    import pathlib
    import uuid

    # Third-Party
    import jwt as pyjwt

    email = os.environ.get("PLATFORM_ADMIN_EMAIL", "admin@apollosai.dev")
    expiry = int(os.environ.get("TOKEN_EXPIRY", "10080"))
    algo = os.environ.get("JWT_ALGORITHM", "HS256")
    issuer = os.environ.get("JWT_ISSUER", "mcpgateway")
    audience = os.environ.get("JWT_AUDIENCE", "mcpgateway-api")

    now = int(time.time())
    payload = {
        "username": email,
        "sub": email,
        "iat": now,
        "iss": issuer,
        "aud": audience,
        "jti": str(uuid.uuid4()),
        "user": {
            "email": email,
            "full_name": "Atlassian Registration",
            "is_admin": True,
            "auth_provider": "cli",
        },
        "exp": now + expiry * 60,
        # Admin bypass requires explicit null — not missing, not empty list
        "teams": None,
    }

    if algo.startswith("RS"):
        key = pathlib.Path(os.environ["JWT_PRIVATE_KEY_PATH"]).read_text()
    else:
        key = os.environ.get("JWT_SECRET_KEY", "my-test-key")

    return pyjwt.encode(payload, key, algorithm=algo)


def api(method: str, path: str, data: dict | None = None, token: str = "") -> dict | list:
    """Call the Context Forge Gateway REST API."""
    url = f"{GATEWAY_URL}{path}"
    req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    if data:
        req.data = json.dumps(data).encode()
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read()
        return json.loads(body) if body else {}


def _infer_scheme() -> str:
    """Infer HTTP scheme from MCF_DOMAIN (https unless clearly local)."""
    domain = MCF_DOMAIN.split(":")[0]
    if domain in ("localhost", "127.0.0.1", "0.0.0.0"):
        return "http"
    return "https"


def _build_callback_url() -> str:
    """Build the OAuth callback URL from MCF_DOMAIN."""
    return f"{_infer_scheme()}://{MCF_DOMAIN}/oauth/callback"


# ---------------------------------------------------------------------------
# Step 1 — Register Atlassian Rovo gateway (idempotent)
# ---------------------------------------------------------------------------


def register_atlassian_gateway(cf_token: str) -> str:
    """Register Atlassian's hosted MCP server as a gateway with OAuth config."""
    print("Step 1: Registering Atlassian Rovo gateway...")

    callback_url = _build_callback_url()
    scopes = [s.strip() for s in ATLASSIAN_SCOPES.split(",") if s.strip()]

    gw_payload = {
        "name": "atlassian-rovo",
        "url": "https://mcp.atlassian.com/v1/mcp",
        "description": ("Atlassian Rovo MCP Server — Jira, Confluence, and Compass " "tools via OAuth 2.0 (3LO) per-user delegation"),
        "transport": "STREAMABLEHTTP",
        "auth_type": "oauth",
        "oauth_config": {
            "grant_type": "authorization_code",
            "issuer": "https://auth.atlassian.com",
            "authorization_url": "https://auth.atlassian.com/authorize?audience=api.atlassian.com",
            "token_url": "https://auth.atlassian.com/oauth/token",
            "redirect_uri": callback_url,
            "scopes": scopes,
            "client_id": ATLASSIAN_CLIENT_ID,
            "client_secret": ATLASSIAN_CLIENT_SECRET,
        },
        "tags": ["atlassian", "jira", "confluence", "compass", "oauth"],
        "visibility": "public",
    }

    # Check for existing gateway
    gateway_id = None
    try:
        gateways = api("GET", "/gateways", token=cf_token)
        for gw in gateways:
            if gw.get("name") == "atlassian-rovo":
                gateway_id = gw["id"]
                break
    except Exception as exc:
        print(f"  Note: {exc}")

    if gateway_id:
        print(f"  Gateway already exists: {gateway_id}")
        return gateway_id

    # Create new
    try:
        result = api("POST", "/gateways", gw_payload, token=cf_token)
        gateway_id = result.get("id") if isinstance(result, dict) else None
        if not gateway_id:
            print(f"  ERROR: Gateway created but no 'id' in response: {result}")
            sys.exit(1)
        print(f"  Created gateway: {gateway_id}")
        return gateway_id
    except Exception as exc:
        print(f"  Gateway registration failed: {exc}")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Step 1b — Register Bitbucket gateway (conditional, idempotent)
# ---------------------------------------------------------------------------


def register_bitbucket_gateway(cf_token: str) -> str | None:
    """Register Bitbucket OAuth gateway if credentials are provided."""
    if not BITBUCKET_CLIENT_ID or not BITBUCKET_CLIENT_SECRET:
        print("  Bitbucket: Skipped (BITBUCKET_OAUTH_CLIENT_ID/SECRET not set)")
        return None

    print("Step 1b: Registering Bitbucket gateway...")

    callback_url = _build_callback_url()

    gw_payload = {
        "name": "atlassian-bitbucket",
        "url": BITBUCKET_MCP_URL,
        "description": ("Custom Bitbucket Cloud MCP Server — repository, pull request, " "and pipeline tools via Bitbucket OAuth"),
        "transport": "STREAMABLEHTTP",
        "auth_type": "oauth",
        "oauth_config": {
            "grant_type": "authorization_code",
            "authorization_url": "https://bitbucket.org/site/oauth2/authorize",
            "token_url": "https://bitbucket.org/site/oauth2/access_token",
            "redirect_uri": callback_url,
            "scopes": [],
            "client_id": BITBUCKET_CLIENT_ID,
            "client_secret": BITBUCKET_CLIENT_SECRET,
        },
        "tags": ["atlassian", "bitbucket", "git", "oauth"],
        "visibility": "public",
    }

    # Check for existing gateway
    gateway_id = None
    try:
        gateways = api("GET", "/gateways", token=cf_token)
        for gw in gateways:
            if gw.get("name") == "atlassian-bitbucket":
                gateway_id = gw["id"]
                break
    except Exception as exc:
        print(f"  Note: {exc}")

    if gateway_id:
        print(f"  Gateway already exists: {gateway_id}")
        return gateway_id

    try:
        result = api("POST", "/gateways", gw_payload, token=cf_token)
        gateway_id = result.get("id") if isinstance(result, dict) else None
        if not gateway_id:
            print(f"  ERROR: Bitbucket gateway created but no 'id' in response: {result}")
            return None
        print(f"  Created gateway: {gateway_id}")
        return gateway_id
    except Exception as exc:
        print(f"  Bitbucket gateway registration failed: {exc}")
        return None


# ---------------------------------------------------------------------------
# Step 2 — Check for existing tools (single request, no polling)
# ---------------------------------------------------------------------------


def _check_existing_tools(cf_token: str, gateway_id: str, label: str) -> list[str]:
    """Check once for any pre-existing tools for the gateway.

    OAuth gateways cannot auto-discover tools until a user completes
    the consent flow, so polling would just consume the full timeout.
    This does a single check in case a user already authorized previously.
    """
    try:
        tools = api("GET", "/tools", token=cf_token)
        if isinstance(tools, list):
            gw_tools = [t for t in tools if isinstance(t, dict) and t.get("gatewayId") == gateway_id]
        else:
            gw_tools = []

        if gw_tools:
            tool_ids = [t["id"] for t in gw_tools]
            print(f"  Found {len(tool_ids)} existing tool(s) for {label}")
            for t in gw_tools:
                print(f"    - {t['name']} ({t['id'][:8]}...)")
            return tool_ids
        else:
            print(f"  No tools yet for {label} (expected — requires OAuth consent)")
            return []

    except Exception as exc:
        print(f"  Could not check tools for {label}: {exc}")
        return []


# ---------------------------------------------------------------------------
# Step 3 — Create virtual server (idempotent)
# ---------------------------------------------------------------------------


def create_virtual_server(
    cf_token: str,
    tool_ids: list[str],
    bitbucket_tool_ids: list[str] | None = None,
) -> None:
    """Create the admin-atlassian virtual server."""
    print("Step 3: Creating virtual server...")

    all_tool_ids = list(tool_ids)
    if bitbucket_tool_ids is not None:
        all_tool_ids.extend(bitbucket_tool_ids)

    # Stable deterministic UUID: "atla" in hex = 61746c61
    srv = {
        "server": {
            "id": "00000000-0000-0000-0000-0061746c6131",
            "name": "admin-atlassian",
            "description": (
                "Atlassian tools — Jira issue management, Confluence page "
                "search and creation, and Compass service catalog. "
                "Users access tools scoped to their own Atlassian permissions "
                "via per-user OAuth delegation."
            ),
            "tags": ["atlassian", "jira", "confluence"],
            "associated_tools": all_tool_ids,
            "visibility": "public",
        }
    }

    try:
        api("POST", "/servers", srv, token=cf_token)
        print(f"  Created virtual server: admin-atlassian ({srv['server']['id']})")
    except urllib.error.HTTPError as exc:
        if exc.code == 409:
            print(f"  Virtual server exists: admin-atlassian ({srv['server']['id']})")
        else:
            print(f"  Failed to create virtual server: {exc}")
    except Exception as exc:
        print(f"  Failed to create virtual server: {exc}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    print("=== Atlassian Registration ===")
    print()

    # Validate required config
    if not ATLASSIAN_CLIENT_ID or not ATLASSIAN_CLIENT_SECRET:
        print("ERROR: ATLASSIAN_OAUTH_CLIENT_ID and ATLASSIAN_OAUTH_CLIENT_SECRET are required")
        sys.exit(1)

    # Health check (only gateway — Atlassian is cloud-hosted)
    wait_for_service(f"{GATEWAY_URL}/health", "Gateway")

    # Authentication
    print()
    print("Generating admin token...")
    cf_token = generate_admin_token()
    print()

    # Step 1: Register gateways
    rovo_gw_id = register_atlassian_gateway(cf_token)
    print()
    bb_gw_id = register_bitbucket_gateway(cf_token)
    print()

    # Step 2: Attempt tool discovery (graceful — may return empty)
    # OAuth gateways require user consent before tools appear.
    # Skip polling for OAuth-only gateways to avoid consuming the full timeout.
    print("Step 2: Tool discovery...")
    print("  OAuth gateways require user consent — tools appear after authorization.")
    print("  Checking for any pre-existing tools...")
    rovo_tool_ids = _check_existing_tools(cf_token, rovo_gw_id, "Atlassian Rovo")
    print()

    bb_tool_ids = None
    if bb_gw_id:
        bb_tool_ids = _check_existing_tools(cf_token, bb_gw_id, "Bitbucket")
        print()

    # Step 3: Create virtual server
    create_virtual_server(cf_token, rovo_tool_ids, bb_tool_ids)

    # Summary
    print()
    print("=== Atlassian registration complete ===")
    print(f"  Rovo Gateway : atlassian-rovo ({rovo_gw_id})")
    if bb_gw_id:
        print(f"  BB Gateway   : atlassian-bitbucket ({bb_gw_id})")
    print(f"  Rovo Tools   : {len(rovo_tool_ids)} discovered")
    if bb_gw_id:
        bb_count = len(bb_tool_ids) if bb_tool_ids is not None else 0
        print(f"  BB Tools     : {bb_count} discovered")
    print(f"  Virtual Server: admin-atlassian")

    if not rovo_tool_ids:
        print()
        print("  NOTE: No tools were discovered yet. A user must complete the")
        print("  OAuth consent flow at the MCF Admin UI before tools appear:")
        print(f"    {_infer_scheme()}://{MCF_DOMAIN}/admin/gateways")


if __name__ == "__main__":
    main()
