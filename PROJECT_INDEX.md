# Project Index: mcp-context-forge

Generated: 2026-02-22 | v1.0.0rc1 | Apache-2.0 | Python >=3.11

## Project Structure

```
mcpgateway/              # Core FastAPI app (231 .py files)
├── main.py              # App factory, MCP protocol endpoints, lifecycle
├── config.py            # Pydantic Settings (env/.env)
├── db.py                # SQLAlchemy ORM (60+ models)
├── schemas.py           # Pydantic CRUD schemas
├── auth.py              # JWT/Basic auth, token scoping
├── admin.py             # Admin UI router (HTMX)
├── routers/ (19)        # HTTP endpoints
├── services/ (56)       # Business logic layer
├── middleware/ (15)      # Auth, RBAC, compression, security, logging
├── transports/ (6)      # SSE, WebSocket, stdio, Streamable HTTP, Redis store
├── cache/ (9)           # Auth, registry, resource, tool, metrics, session caches
├── plugins/             # Plugin framework (hooks, manager)
├── alembic/ (69 migr)   # Database migrations
├── utils/ (33)          # Auth, DB, Redis, HTTP, SSL, data utilities
├── templates/           # Jinja2 HTMX templates
└── static/              # CSS, JS, images
plugins/ (46)            # Security, transform, policy, infra, integration plugins
tests/ (610 .py files)   # unit, integration, e2e, compliance, security, fuzz, perf, load
charts/                  # Helm chart (mcp-stack)
deployment/              # Ansible, K8s, Knative, Terraform
scripts/ (27)            # Benchmarks, CI, setup, migration, testing utilities
```

## Entry Points

- **API Server**: `mcpgateway/main.py` → FastAPI app, `make dev` (port 8000) / `make serve` (port 4444)
- **CLI**: `mcpgateway/cli.py` → Typer CLI
- **Translate**: `python -m mcpgateway.translate --stdio "cmd" --port 9000` → Expose stdio MCP via HTTP
- **Export/Import**: `mcpgateway/cli_export_import.py` → Config export/import CLI
- **Tests**: `make test` / `pytest tests/unit/ -v`

## Core Modules

### Services (56) by Domain
- **Core MCP** (5): ToolService, ResourceService, PromptService, ServerService, GatewayService
- **Auth/Security** (12): EmailAuth, Argon2, Encryption, SSO, OAuth, DCR, Role, Permission, Audit, SecurityLogger, TokenCatalog, TokenStorage
- **Observability** (10): Logging, StructuredLogger, LogStorage, LogAggregator, Metrics, MetricsBuffer, MetricsRollup, MetricsQuery, MetricsCleanup, Observability
- **Teams** (4): TeamManagement, TeamInvitation, PersonalTeam, EmailNotification
- **LLM** (2): LLMProvider, LLMProxy
- **Infrastructure** (7): Catalog, Completion, Cancellation, Plugin, A2A, Root, MCPSessionPool
- **Data** (4): Export (AES-256-GCM), Import (conflict resolution), Tag, gRPC

### Routers (19)
`/auth` `/cancellation` `/llmchat` `/api/logs` `/api/metrics` `/oauth` `/observability` `/rbac` `/reverse-proxy` `/auth/sso` `/tokens` `/toolops` `/.well-known` + component routers (email_auth, llm_*, teams, server_well_known)

### Middleware (15)
AuthContext → Compression → CorrelationID → DBQueryLogging → HttpAuth(plugins) → Observability → ProtocolVersion → RBAC → RequestLogging → SecurityHeaders → TokenScoping → TokenUsage → Validation + PathFilter + RequestContext utilities

### Transports (6)
SSE | WebSocket | stdio | Streamable HTTP (in-memory) | Redis EventStore | Base ABC

## Configuration

- `pyproject.toml` — Project deps, build config
- `.env` / `.env.example` — Runtime config (50+ vars)
- `plugins/config.yaml` — Active plugin configuration
- `Makefile` — 100+ build/test/lint targets
- `docker-compose.yml` — Container orchestration

## Key Dependencies

- `fastapi` + `starlette` + `uvicorn` — ASGI web framework
- `sqlalchemy` + `alembic` — ORM + migrations
- `pydantic` + `pydantic-settings` — Validation + config
- `httpx` — Async HTTP client
- `mcp>=1.26.0` — MCP SDK
- `orjson` — Fast JSON serialization
- `pyjwt` + `argon2-cffi` + `cryptography` — Auth/crypto
- `prometheus-client` — Metrics
- `gunicorn` — Production WSGI/ASGI server
- `sse-starlette` — SSE transport

## Quick Start

```bash
cp .env.example .env && make venv install-dev check-env  # Setup
make dev                                                  # Dev server :8000
make autoflake isort black pre-commit                     # Format
make flake8 bandit interrogate pylint verify              # Lint
make test                                                 # Test
```

## Key Patterns

- **Two-layer security**: Token scoping (visibility) + RBAC (permissions)
- **Service layer**: All business logic in services/, routers are thin HTTP adapters
- **Plugin hooks**: HTTP_PRE/POST_REQUEST, TOOL_PRE/POST_EXECUTE, RESOURCE_PRE/POST_READ
- **Cursor pagination**: All list endpoints
- **Idempotent migrations**: Inspector checks before schema changes
- **4 built-in roles**: platform_admin (global *), team_admin, developer, viewer