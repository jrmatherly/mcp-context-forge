# Architecture Index

## Layer Summary
- **Routers (19)**: HTTP endpoints in `mcpgateway/routers/` — auth, RBAC, OAuth, SSO, teams, LLM, observability, cancellation, reverse proxy, metrics, log search, well-known
- **Services (56)**: Business logic in `mcpgateway/services/` — 5 core MCP, 12 auth/security, 11 observability/metrics, 4 team, 2 LLM, 7 infrastructure, 4 data mgmt, rest misc
- **Middleware (15)**: `mcpgateway/middleware/` — auth context, compression, correlation ID, DB query logging, HTTP auth hooks, observability, path filter, protocol version, RBAC, request context, request logging, security headers, token scoping, token usage, validation
- **Transports (5)**: `mcpgateway/transports/` — SSE, WebSocket, stdio, Streamable HTTP, base ABC
- **Cache (9)**: `mcpgateway/cache/` — auth, registry, resource, tool lookup, metrics, admin stats, A2A stats, global config, session registry
- **DB Models (60+)**: `mcpgateway/db.py` — core MCP entities, users, RBAC, teams, OAuth/SSO, metrics (5 rollup tables), observability (5), performance (3), security, LLM, audit
- **Plugins (50+)**: `plugins/` — security, transformation, policy/compliance, infrastructure, integration
- **Migrations (70)**: `mcpgateway/alembic/versions/`

## Key Files
- Entry: `mcpgateway/main.py` (app factory, lifecycle, protocol endpoints)
- Config: `mcpgateway/config.py` (Pydantic Settings)
- DB: `mcpgateway/db.py` (60+ ORM models)
- Schemas: `mcpgateway/schemas.py` (CRUD Pydantic models)
- Auth: `mcpgateway/auth.py` (JWT, normalize_token_teams)
- Admin UI: `mcpgateway/admin.py` (HTMX router)

## Full Index
See `.scratchpad/PROJECT_INDEX.md` for the comprehensive project index.
