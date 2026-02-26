#!/usr/bin/env python3
"""MindsDB auto-registration for MCP Context Forge.

Registers MindsDB as a federated gateway, waits for tool discovery,
provisions teams, and creates team-scoped virtual servers.

Environment variables:
    MCPGATEWAY_URL          - Gateway base URL (default: http://gateway:4444)
    MINDSDB_URL             - MindsDB base URL (default: http://mindsdb:47334)
    MINDSDB_USERNAME        - MindsDB login username
    MINDSDB_PASSWORD        - MindsDB login password
    JWT_ALGORITHM           - JWT signing algorithm (default: HS256)
    JWT_SECRET_KEY          - JWT secret key for HS* algorithms
    JWT_PRIVATE_KEY_PATH    - Path to private key for RS* algorithms
    JWT_PUBLIC_KEY_PATH     - Path to public key for RS* algorithms
    JWT_AUDIENCE            - JWT audience claim (default: mcpgateway-api)
    JWT_ISSUER              - JWT issuer claim (default: mcpgateway)
    PLATFORM_ADMIN_EMAIL    - Admin email for JWT (default: admin@apollosai.dev)
    TOKEN_EXPIRY            - JWT expiry in minutes (default: 10080)
    TOOL_DISCOVERY_TIMEOUT  - Tool polling timeout in seconds (default: 120)
"""

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
MINDSDB_URL = os.environ.get("MINDSDB_URL", "http://mindsdb:47334")
TOOL_DISCOVERY_TIMEOUT = int(os.environ.get("TOOL_DISCOVERY_TIMEOUT", "120"))


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
    import pathlib
    import uuid

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
            "full_name": "MindsDB Registration",
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


def login_mindsdb() -> str:
    """Obtain a session token from MindsDB."""
    data = json.dumps({
        "username": os.environ["MINDSDB_USERNAME"],
        "password": os.environ["MINDSDB_PASSWORD"],
    }).encode()
    req = urllib.request.Request(
        f"{MINDSDB_URL}/api/login",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as r:
        result = json.loads(r.read())
        return result.get("token") or result.get("session") or ""


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


# ---------------------------------------------------------------------------
# Step 1 — Register or update the MindsDB gateway (idempotent)
# ---------------------------------------------------------------------------

def register_gateway(cf_token: str, mdb_token: str) -> str:
    """Ensure a 'mindsdb' gateway exists and return its ID."""
    print("Step 1: Registering MindsDB gateway...")

    gw_payload = {
        "name": "mindsdb",
        "url": f"{MINDSDB_URL}/mcp/sse",
        "description": (
            "MindsDB federated data gateway — query databases, warehouses, "
            "knowledge bases, and SaaS applications via SQL"
        ),
        "transport": "SSE",
        "auth_type": "bearer",
        "auth_token": mdb_token,
        "tags": ["data-gateway", "knowledge-base", "sql", "mindsdb"],
        "visibility": "private",
    }

    # Check for existing gateway
    gateway_id = None
    try:
        gateways = api("GET", "/gateways", token=cf_token)
        for gw in gateways:
            if gw.get("name") == "mindsdb":
                gateway_id = gw["id"]
                break
    except Exception as exc:
        print(f"  Note: {exc}")

    # Update existing (preserves tools, avoids race conditions with replicas)
    if gateway_id:
        try:
            api("PUT", f"/gateways/{gateway_id}", {
                "auth_token": mdb_token,
                "url": f"{MINDSDB_URL}/mcp/sse",
            }, token=cf_token)
            print(f"  Updated existing gateway: {gateway_id}")
            return gateway_id
        except Exception as exc:
            print(f"  Update failed ({exc}), re-creating...")
            gateway_id = None

    # Create new
    if not gateway_id:
        try:
            result = api("POST", "/gateways", gw_payload, token=cf_token)
            gateway_id = result.get("id")
            print(f"  Created gateway: {gateway_id}")
            return gateway_id
        except Exception as exc:
            print(f"  Gateway registration failed: {exc}")
            sys.exit(1)


# ---------------------------------------------------------------------------
# Step 2 — Wait for tool auto-discovery
# ---------------------------------------------------------------------------

def discover_tools(cf_token: str, gateway_id: str) -> tuple[str, str | None]:
    """Poll until the query tool appears; return (query_id, list_databases_id)."""
    print("Step 2: Waiting for tool auto-discovery...")

    query_tool_id = None
    list_db_tool_id = None
    poll_interval = 2  # seconds

    for i in range(TOOL_DISCOVERY_TIMEOUT // poll_interval):
        try:
            tools = api("GET", "/tools", token=cf_token)
            gw_tools = [t for t in tools if t.get("gatewayId") == gateway_id]

            if i % 5 == 0:
                elapsed = i * poll_interval
                print(
                    f"  Polling: {len(tools)} total tools, "
                    f"{len(gw_tools)} for gateway {gateway_id[:8]}... ({elapsed}s)"
                )

            for t in gw_tools:
                name = t["name"]
                if name.endswith("-query") or name == "query":
                    query_tool_id = t["id"]
                elif (
                    name.endswith("-list-databases")
                    or name.endswith("-list_databases")
                    or name == "list_databases"
                ):
                    list_db_tool_id = t["id"]

            if query_tool_id:
                print(f"  Found query tool: {query_tool_id}")
                if list_db_tool_id:
                    print(f"  Found list_databases tool: {list_db_tool_id}")
                return query_tool_id, list_db_tool_id

        except Exception as exc:
            if i % 5 == 0:
                print(f"  Polling error at {i * poll_interval}s: {exc}")

        time.sleep(poll_interval)

    print(f"  query tool not discovered after {TOOL_DISCOVERY_TIMEOUT}s")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Step 3 — Create teams (idempotent)
# ---------------------------------------------------------------------------

def get_or_create_team(
    cf_token: str, name: str, slug: str, description: str
) -> str | None:
    """Return the UUID for *slug*, creating the team if necessary."""
    try:
        resp = api("GET", "/teams/", token=cf_token)
        teams_list = (
            resp if isinstance(resp, list)
            else resp.get("items", resp.get("teams", []))
        )
        for t in teams_list:
            if t.get("slug") == slug or t.get("name") == name:
                print(f"  Team exists: {name} ({t['id']})")
                return t["id"]
    except Exception as exc:
        print(f"  Note checking teams: {exc}")

    try:
        result = api("POST", "/teams/", {
            "name": name,
            "slug": slug,
            "description": description,
            "visibility": "private",
        }, token=cf_token)
        team_id = result.get("id")
        print(f"  Created team: {name} ({team_id})")
        return team_id
    except Exception as exc:
        print(f"  Failed to create team {name}: {exc}")
        return None


def provision_teams(cf_token: str) -> tuple[str | None, str | None]:
    """Ensure Legal and HR teams exist; return (legal_id, hr_id)."""
    print("Step 3: Provisioning teams...")
    legal = get_or_create_team(cf_token, "Legal", "legal", "Legal department team")
    hr = get_or_create_team(cf_token, "HR", "hr", "Human Resources department team")
    return legal, hr


# ---------------------------------------------------------------------------
# Step 4 — Create team-scoped virtual servers (idempotent)
# ---------------------------------------------------------------------------

def create_virtual_servers(
    cf_token: str,
    query_tool_id: str,
    list_db_tool_id: str | None,
    legal_team_id: str | None,
    hr_team_id: str | None,
) -> None:
    """Create the three demo virtual servers if they don't already exist."""
    print("Step 4: Creating virtual servers...")

    servers = [
        {
            "server": {
                "id": "00000000-0000-0000-0000-00006c656731",
                "name": "legal-team-data",
                "description": (
                    "Legal department Knowledge Base access. "
                    "Query tool available for semantic search over legal documents."
                ),
                "tags": ["legal", "knowledge-base"],
                "associated_tools": [query_tool_id],
                "team_id": legal_team_id,
                "visibility": "team" if legal_team_id else "private",
            }
        },
        {
            "server": {
                "id": "00000000-0000-0000-0000-006872303031",
                "name": "hr-team-data",
                "description": (
                    "HR department Knowledge Base access. "
                    "Query tool available for semantic search over HR documents."
                ),
                "tags": ["hr", "knowledge-base"],
                "associated_tools": [query_tool_id],
                "team_id": hr_team_id,
                "visibility": "team" if hr_team_id else "private",
            }
        },
        {
            "server": {
                "id": "00000000-0000-0000-0000-00006d696e64",
                "name": "admin-data-gateway",
                "description": (
                    "Full access to all MindsDB databases and knowledge bases. "
                    "Use list_databases to see available sources, and query to execute any SQL."
                ),
                "tags": ["admin", "data-gateway"],
                "associated_tools": (
                    [query_tool_id] + ([list_db_tool_id] if list_db_tool_id else [])
                ),
                "visibility": "private",
            }
        },
    ]

    for srv in servers:
        name = srv["server"]["name"]
        srv_id = srv["server"]["id"]

        # Drop None team_id to avoid 422 validation errors
        if srv["server"].get("team_id") is None:
            srv["server"].pop("team_id", None)

        try:
            api("POST", "/servers", srv, token=cf_token)
            print(f"  Created virtual server: {name} ({srv_id})")
        except urllib.error.HTTPError as exc:
            if exc.code == 409:
                print(f"  Virtual server exists: {name} ({srv_id})")
            else:
                print(f"  Failed to create {name}: {exc}")
        except Exception as exc:
            print(f"  Failed to create {name}: {exc}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=== MindsDB Registration ===")
    print()

    # Health checks
    wait_for_service(f"{GATEWAY_URL}/health", "Gateway")
    wait_for_service(f"{MINDSDB_URL}/api/status", "MindsDB")

    # Authentication
    print()
    print("Generating admin token...")
    cf_token = generate_admin_token()

    print("Logging into MindsDB...")
    mdb_token = login_mindsdb()
    if not mdb_token:
        print("  Failed to get MindsDB token")
        sys.exit(1)
    print("  MindsDB token obtained")
    print()

    # Registration pipeline
    gateway_id = register_gateway(cf_token, mdb_token)
    print()
    query_tool_id, list_db_tool_id = discover_tools(cf_token, gateway_id)
    print()
    legal_team_id, hr_team_id = provision_teams(cf_token)
    print()
    create_virtual_servers(cf_token, query_tool_id, list_db_tool_id, legal_team_id, hr_team_id)

    # Summary
    print()
    print("=== MindsDB registration complete ===")
    print(f"  Gateway: mindsdb ({gateway_id})")
    print(f"  Tools: query={query_tool_id}, list_databases={list_db_tool_id or 'not found'}")
    if legal_team_id:
        print(f"  Team: Legal ({legal_team_id})")
    if hr_team_id:
        print(f"  Team: HR ({hr_team_id})")


if __name__ == "__main__":
    main()
