---
name: mcf-api
description: Interact with the MCP Context Forge Gateway REST API — register gateways, create servers, invoke tools, manage teams, configure OAuth, and perform admin operations. Use when asked to register an MCP server, call a gateway endpoint, create a team, invoke a tool, set up a virtual server, test API connectivity, check gateway health, manage tokens, configure header passthrough, or perform any gateway API operation. Also trigger when the user mentions curl examples, API payloads, or gateway configuration.
---

Perform gateway API operation: $ARGUMENTS

## Authentication Setup

All authenticated endpoints require a JWT bearer token.

### Generate a token

```bash
# Admin token (full access — teams: null + is_admin: true)
export MCPGATEWAY_BEARER_TOKEN=$(python -m mcpgateway.utils.create_jwt_token \
  --username admin@apollosai.dev --exp 10080 --secret $JWT_SECRET_KEY | tr -d '\n')

# Team-scoped token
export MCPGATEWAY_BEARER_TOKEN=$(python -m mcpgateway.utils.create_jwt_token \
  --username user@example.com --exp 60 --secret $JWT_SECRET_KEY --teams '["team-uuid"]' | tr -d '\n')

# Public-only token (automation)
export MCPGATEWAY_BEARER_TOKEN=$(python -m mcpgateway.utils.create_jwt_token \
  --username ci@example.com --exp 60 --secret $JWT_SECRET_KEY --teams '[]' | tr -d '\n')
```

### Token scoping rules

| JWT `teams` | `is_admin: true` | `is_admin: false` |
|-------------|------------------|-------------------|
| Key MISSING | PUBLIC-ONLY | PUBLIC-ONLY |
| `null` | ADMIN BYPASS | PUBLIC-ONLY |
| `[]` | PUBLIC-ONLY | PUBLIC-ONLY |
| `["t1"]` | Team + Public | Team + Public |

### Base URLs
- Dev: `http://127.0.0.1:8000` (`make dev`)
- Prod: `http://localhost:4444` (`make serve`)
- Docker: `http://localhost:8080` (nginx proxy)

## Common Operations

### Health Check (no auth)

```bash
curl -s http://localhost:4444/health | jq
curl -s http://localhost:4444/ready | jq
```

### Register a Gateway (external MCP server)

```bash
curl -s -X POST -H "Authorization: Bearer $MCPGATEWAY_BEARER_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
           "url": "http://localhost:9000",
           "name": "my-mcp-server",
           "description": "Example MCP server",
           "transport": "STREAMABLEHTTP"
         }' \
     http://localhost:4444/gateways | jq
```

Transport options: `SSE`, `STREAMABLEHTTP`, `WEBSOCKET`, `STDIO`

#### With bearer auth
```bash
curl -s -X POST -H "Authorization: Bearer $MCPGATEWAY_BEARER_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
           "url": "http://localhost:9000",
           "name": "auth-server",
           "auth_type": "bearer",
           "auth_token": "server-secret-token"
         }' \
     http://localhost:4444/gateways | jq
```

#### With multi-auth headers
```bash
curl -s -X POST -H "Authorization: Bearer $MCPGATEWAY_BEARER_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
           "url": "http://localhost:9000",
           "name": "multi-auth-server",
           "auth_type": "authheaders",
           "auth_headers": [
             {"key": "X-API-Key", "value": "secret-key"},
             {"key": "X-Client-ID", "value": "client-456"}
           ]
         }' \
     http://localhost:4444/gateways | jq
```

#### With OAuth (per-user delegation)
```bash
curl -s -X POST -H "Authorization: Bearer $MCPGATEWAY_BEARER_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
           "url": "https://mcp.example.com/v1/mcp",
           "name": "oauth-server",
           "transport": "STREAMABLEHTTP",
           "auth_type": "oauth",
           "oauth_config": {
             "grant_type": "authorization_code",
             "authorization_url": "https://auth.example.com/authorize",
             "token_url": "https://auth.example.com/oauth/token",
             "redirect_uri": "https://mcp.yourdomain.com/oauth/callback",
             "scopes": ["read", "write"],
             "client_id": "YOUR_CLIENT_ID",
             "client_secret": "YOUR_CLIENT_SECRET"
           }
         }' \
     http://localhost:4444/gateways | jq
```

### Refresh Gateway (re-discover tools)

```bash
curl -s -X POST -H "Authorization: Bearer $MCPGATEWAY_BEARER_TOKEN" \
     http://localhost:4444/gateways/<gateway_id>/refresh | jq
```

### Create a Virtual Server

```bash
curl -s -X POST -H "Authorization: Bearer $MCPGATEWAY_BEARER_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
           "server": {
             "name": "my-server",
             "description": "Virtual server description",
             "tags": ["demo"],
             "associated_tools": ["tool-id-1", "tool-id-2"],
             "visibility": "private"
           }
         }' \
     http://localhost:4444/servers | jq
```

Returns 409 if server with same name already exists (use as idempotent existence check).

### Create a Team

```bash
curl -s -X POST -H "Authorization: Bearer $MCPGATEWAY_BEARER_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
           "name": "Engineering",
           "slug": "engineering",
           "description": "Engineering team",
           "visibility": "private"
         }' \
     http://localhost:4444/teams/ | jq
```

### Invoke a Tool (JSON-RPC)

```bash
curl -s -X POST -H "Authorization: Bearer $MCPGATEWAY_BEARER_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
           "jsonrpc": "2.0",
           "id": 1,
           "method": "tool-name",
           "params": {"arg1": "value1"}
         }' \
     http://localhost:4444/rpc | jq
```

### List Operations

```bash
# Gateways
curl -s -H "Authorization: Bearer $MCPGATEWAY_BEARER_TOKEN" "http://localhost:4444/gateways" | jq

# Servers
curl -s -H "Authorization: Bearer $MCPGATEWAY_BEARER_TOKEN" "http://localhost:4444/servers" | jq

# Tools
curl -s -H "Authorization: Bearer $MCPGATEWAY_BEARER_TOKEN" "http://localhost:4444/tools" | jq

# Prompts
curl -s -H "Authorization: Bearer $MCPGATEWAY_BEARER_TOKEN" "http://localhost:4444/prompts" | jq

# Resources
curl -s -H "Authorization: Bearer $MCPGATEWAY_BEARER_TOKEN" "http://localhost:4444/resources" | jq

# Teams
curl -s -H "Authorization: Bearer $MCPGATEWAY_BEARER_TOKEN" "http://localhost:4444/teams/" | jq

# A2A Agents
curl -s -H "Authorization: Bearer $MCPGATEWAY_BEARER_TOKEN" "http://localhost:4444/a2a" | jq
```

### Query Parameters

- `include_inactive` (bool) — include disabled entities
- `tags=tag1,tag2` — filter by tags
- `team_id=<uuid>` — filter by team
- `visibility=private|team|public` — filter by visibility
- `cursor` / `limit` — cursor-based pagination

### Streaming Endpoints

```bash
# Global SSE
curl -N -H "Authorization: Bearer $MCPGATEWAY_BEARER_TOKEN" http://localhost:4444/sse

# Per-server SSE
curl -N -H "Authorization: Bearer $MCPGATEWAY_BEARER_TOKEN" http://localhost:4444/servers/<id>/sse

# WebSocket
websocat "ws://localhost:4444/ws" -H "Authorization: Bearer $MCPGATEWAY_BEARER_TOKEN"
```

### Import/Export

```bash
# Export all configuration
curl -s -H "Authorization: Bearer $MCPGATEWAY_BEARER_TOKEN" http://localhost:4444/export > backup.json

# Import (skip conflicts)
curl -s -X POST -H "Authorization: Bearer $MCPGATEWAY_BEARER_TOKEN" \
     -H "Content-Type: application/json" \
     -d @backup.json \
     "http://localhost:4444/import?conflict_strategy=skip" | jq
```

### Admin Operations

```bash
# System stats
curl -s -H "Authorization: Bearer $MCPGATEWAY_BEARER_TOKEN" http://localhost:4444/admin/api/stats | jq

# MCP discovery
curl -s http://localhost:4444/.well-known/mcp.json | jq

# Passthrough header config
curl -s -H "Authorization: Bearer $MCPGATEWAY_BEARER_TOKEN" \
     http://localhost:4444/admin/config/passthrough-headers | jq
```

## Common Errors

| Code | Meaning |
|------|---------|
| 401 | Bearer token missing/invalid/expired |
| 409 | Resource already exists (idempotent — safe to ignore) |
| 422 | Validation error (malformed payload) |

## Gotchas

- PUT without `auth_type` wipes gateway auth credentials to `{}` — always include `auth_type` in updates
- OAuth gateways can't auto-discover tools until a user completes the consent flow in a browser
- `POST /servers` returns 409 if name exists — use as existence check, not an error
- `POST /teams/` is also idempotent-safe
- Prefer `Authorization` header over `jwt_token` cookie
- URL-encode resource URIs when used as path parameters
