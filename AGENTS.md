# AGENTS.md

Guidelines for AI coding assistants working with this repository.

For comprehensive implementation rules, patterns, and gotchas optimized for AI agent consumption, see:
- `_bmad-output/project-context.md` - **Critical rules AI agents must follow** (technology stack, coding patterns, anti-patterns, security rules, edge cases)

For domain-specific guidance, see subdirectory AGENTS.md files:
- `tests/AGENTS.md` - Testing conventions and workflows
- `plugins/AGENTS.md` - Plugin framework and development
- `charts/AGENTS.md` - Helm chart operations
- `deployment/AGENTS.md` - Infrastructure and deployment
- `docs/AGENTS.md` - Documentation authoring
- `mcp-servers/AGENTS.md` - MCP server implementation

**Note:** The `llms/` directory contains guidance for LLMs *using* the Context Forge solution (end-user runtime guidance), not for code agents working on this codebase.

## Project Overview

MCP Gateway (ContextForge) is a production-grade gateway, proxy, and registry for Model Context Protocol (MCP) servers and A2A Agents. It federates MCP and REST services, providing unified discovery, auth, rate-limiting, observability, virtual servers, multi-transport protocols, and an optional Admin UI.

## Project Structure

```
mcpgateway/                 # Core FastAPI application
├── main.py                 # Application entry point
├── config.py               # Environment configuration
├── db.py                   # SQLAlchemy ORM models and session management
├── schemas.py              # Pydantic validation schemas
├── services/               # Business logic layer (55+ services)
├── routers/                # HTTP endpoint definitions (20 routers)
├── middleware/             # Cross-cutting concerns (17 middleware)
├── transports/             # Protocol implementations (SSE, WebSocket, stdio, streamable HTTP)
├── plugins/                # Plugin framework infrastructure
└── alembic/                # Database migrations

tests/                      # Test suite (see tests/AGENTS.md)
plugins/                    # Plugin implementations (see plugins/AGENTS.md)
charts/                     # Helm charts (see charts/AGENTS.md)
deployment/                 # Infrastructure configs (see deployment/AGENTS.md)
docs/                       # Architecture and usage documentation (see docs/AGENTS.md)
a2a-agents/                 # A2A agent implementations (used for testing/examples)
mcp-servers/                # MCP server templates (see mcp-servers/AGENTS.md)
llms/                       # End-user LLM guidance (not for code agents)
```

## Essential Commands

### Setup
```bash
cp .env.example .env && make venv install-dev check-env    # Complete setup
make venv                          # Create virtual environment with uv
make install-dev                   # Install with dev dependencies
make check-env                     # Verify .env against .env.example
```

### Development
```bash
make dev                          # Dev server on :8000 with autoreload
make serve                        # Production gunicorn on :4444
make certs && make serve-ssl      # HTTPS on :4444
```

### Code Quality
```bash
# After writing code
make autoflake isort black pre-commit

# Before committing, use ty, mypy and pyrefly to check just the new files, then run:
make flake8 bandit interrogate pylint verify
```

## Authentication & RBAC Overview

MCP Gateway implements a **two-layer security model**:

1. **Token Scoping (Layer 1)**: Controls what resources a user CAN SEE (data filtering)
2. **RBAC (Layer 2)**: Controls what actions a user CAN DO (permission checks)

### Token Scoping Quick Reference

The `teams` claim in JWT tokens determines resource visibility:

| JWT `teams` State | `is_admin: true` | `is_admin: false` |
|-------------------|------------------|-------------------|
| Key MISSING | PUBLIC-ONLY `[]` | PUBLIC-ONLY `[]` |
| `teams: null` | ADMIN BYPASS | PUBLIC-ONLY `[]` |
| `teams: []` | PUBLIC-ONLY `[]` | PUBLIC-ONLY `[]` |
| `teams: ["t1"]` | Team + Public | Team + Public |

**Key behaviors:**

- Missing `teams` key = public-only access (secure default)
- Admin bypass requires BOTH `teams: null` AND `is_admin: true`
- `normalize_token_teams()` in `mcpgateway/auth.py` is the single source of truth

### Built-in Roles

| Role | Scope | Key Permissions |
|------|-------|-----------------|
| `platform_admin` | global | `*` (all) |
| `team_admin` | team | teams.*, tools.read/execute, resources.read |
| `developer` | team | tools.read/execute, resources.read |
| `viewer` | team | tools.read, resources.read (read-only) |

### Documentation

- **Full RBAC guide**: `docs/docs/manage/rbac.md`
- **Multi-tenancy architecture**: `docs/docs/architecture/multitenancy.md`
- **OAuth token delegation**: `docs/docs/architecture/oauth-design.md`

## MindsDB Integration

Optional MindsDB deployment via `docker compose --profile mindsdb`:
- Auto-registration: `scripts/register-mindsdb.py` runs as init container (`register_mindsdb` service)
- The container image does NOT pip-install `mcpgateway` — avoid importing it in scripts; use pyjwt directly for JWT generation
- `MINDSDB_HTTP_AUTH_TYPE=token` — indefinitely-valid bearer tokens, no cron refresh needed
- MindsDB MCP endpoint: `/mcp/sse` (SSE transport, part of HTTP API — no `MINDSDB_APIS=mcp` needed)
- `sql_sanitizer` plugin blocks destructive SQL via `TOOL_PRE_INVOKE` — regex `\b` patterns match inside string literals (known limitation)
- Team-scoped Virtual Servers + agent permissions provide hard security enforcement; agent instructions are soft (~95% effective)
- See `docs/docs/architecture/mindsdb-enhancements.md` for future hardening roadmap
- See `docs/docs/tutorials/mindsdb-team-provisioning.md` for adding new teams
- API idempotency: `POST /servers` returns 409 if server exists (use as existence check); `POST /teams/` also idempotent-safe

## Shared Nginx (Production Deployment)

- In production, LibreChat's nginx owns ports 80/443 and routes to both apps via subdomain
- MCP Context Forge's gateway joins the `shared-proxy` Docker network for cross-stack routing
- MCF's standalone nginx is behind `profiles: ["standalone"]` — only for local dev
- Design doc: `.scratchpad/plans/shared-nginx-consolidation.md`
- LibreChat nginx configs: `~/dev/ai-stack/LibreChat/nginx/` (`nginx.conf`, `librechat.conf.template`, `mcf-gateway.conf.template`)
- Prerequisite: `docker network create shared-proxy` (run once before starting either stack)
- Required LibreChat `.env` vars: `LIBRECHAT_DOMAIN`, `MCF_DOMAIN`

## Atlassian Integration

- Docker Compose: `--profile atlassian` enables `register_atlassian` init container
- Registration script: `scripts/register-atlassian.py` — idempotent, registers Rovo + optional Bitbucket gateways
- Bitbucket OAuth scopes: configured on the OAuth consumer, NOT in the auth URL — `scopes: []` in gateway registration
- OAuth gateways can't auto-discover tools (requires user browser consent) — use single check, not polling
- Bitbucket MCP server: `mcp-servers/python/bitbucket-server/` — FastMCP skeleton (stubs only)
- Helm chart: init job only (cloud-hosted service), uses `secretKeyRef` to `gateway-secret` for JWT vars

## Helm Chart Notes

- `values.schema.json` has `additionalProperties: false` — new top-level values sections require a matching schema entry or `helm lint` fails
- `values.schema.json` nested objects should also have `additionalProperties: false` for strict validation
- Validate with all optional combos: `helm template test charts/mcp-stack/ --set pgbouncer.enabled=true`, `--set mindsdb.enabled=true`
- Also validate: `--set atlassian.enabled=true --set atlassian.credentials.clientId=test --set atlassian.credentials.clientSecret=test`
- Registration job templates: use `secretKeyRef` to `gateway-secret` for JWT vars — values live under `mcpContextForge.secret.JWT_SECRET_KEY` (UPPER_SNAKE_CASE), never `mcpContextForge.config.jwtAlgorithm` (camelCase)
- `docker-compose.yml` uses high-load defaults (8 CPU / 8 GB); Helm `values.yaml` uses conservative defaults (200m CPU / 1Gi) — drift is documented inline
- `deployment/k8s/` raw manifests are **deprecated** — use `charts/mcp-stack/` Helm chart for all Kubernetes deployments
- MindsDB image runs as root (UID 0, no USER in Dockerfile) — `securityContext.runAsNonRoot` must be `false`, `readOnlyRootFilesystem` must be `false`

## Pre-commit Configuration

- `make pre-commit` uses `.pre-commit-lite.yaml` (NOT `.pre-commit-config.yaml`) — keep both files' `exclude` patterns in sync
- When adding new directories, update exclusions in: `.pre-commit-config.yaml`, `.pre-commit-lite.yaml`, `.flake8`, `pyproject.toml` (Ruff), `.dockerignore`, `MANIFEST.in`
- AI/agent directories (`_bmad/`, `.claude/`, `.serena/`, `.scratchpad/`, etc.) are excluded from linting but tracked in git
- All Python files (including `scripts/`) must have `# -*- coding: utf-8 -*-` after the shebang — `fix-encoding-pragma` hook enforces this
- If pre-commit fails with `EOFError: Compressed file ended before the end-of-stream marker`, clear the cache: `rm -rf .cache/pre-commit-home/`

## CI/CD Workflows

- All 21 workflows in `.github/workflows/` have path filters — doc-only or scratchpad changes skip CI
- Each workflow includes its own `.github/workflows/<name>.yml` in `paths` so workflow edits trigger their own CI
- `linting-full.yml` uses `paths-ignore` (broad check, excludes scratchpad/AI dirs); all others use `paths` (allowlist)
- Workflows with `schedule:` triggers (`bandit`, `dependency-review`, `license-check`) still run weekly regardless of path filters
- When adding new source directories, add them to relevant workflow `paths` filters
- Editing workflow files triggers a security reminder hook — this is expected, not an error

## Key Environment Variables

```bash
# Core
HOST=0.0.0.0
PORT=4444
DATABASE_URL=sqlite:///./mcp.db   # or postgresql+psycopg://...
REDIS_URL=redis://localhost:6379
RELOAD=true

# Auth
JWT_SECRET_KEY=your-secret-key
BASIC_AUTH_USER=admin
BASIC_AUTH_PASSWORD=changeme
AUTH_REQUIRED=true                   # Set false ONLY for development
AUTH_ENCRYPTION_SECRET=my-test-salt  # For encrypting stored secrets

# Features
MCPGATEWAY_UI_ENABLED=true
MCPGATEWAY_ADMIN_API_ENABLED=true
MCPGATEWAY_A2A_ENABLED=true
PLUGINS_ENABLED=true
PLUGIN_CONFIG_FILE=plugins/config.yaml

# Logging
LOG_LEVEL=INFO
LOG_TO_FILE=false
STRUCTURED_LOGGING_DATABASE_ENABLED=false

# Observability
OBSERVABILITY_ENABLED=false
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
```

## MCP Helpers

```bash
# Generate JWT token
python -m mcpgateway.utils.create_jwt_token --username admin@apollosai.dev --exp 10080 --secret KEY

# Export for API calls
export MCPGATEWAY_BEARER_TOKEN=$(python -m mcpgateway.utils.create_jwt_token --username admin@apollosai.dev --exp 0 --secret KEY)

# Expose stdio server via HTTP/SSE
python -m mcpgateway.translate --stdio "uvx mcp-server-git" --port 9000
```

### Adding an MCP Server
1. Start: `python -m mcpgateway.translate --stdio "server-command" --port 9000`
2. Register: `POST /gateways`
3. Create virtual server: `POST /servers`
4. Access via SSE/WebSocket endpoints

## Technology Stack

- **FastAPI** with **Pydantic** validation and **SQLAlchemy** ORM (Starlette ASGI)
- **HTMX + Alpine.js** for admin UI
- **SQLite** default, **PostgreSQL** support, **Redis** for caching/federation
- **Alembic** for migrations

## Alembic Database Migrations

When adding new database columns or tables, create an Alembic migration.

### Creating Migrations

```bash
# CRITICAL: Always check the current head FIRST
cd mcpgateway && alembic heads

# Generate a new migration (auto-generates from model changes)
alembic revision --autogenerate -m "add_column_to_table"

# Or create an empty migration for manual edits
alembic revision -m "add_column_to_table"
```

### Migration File Requirements

The `down_revision` MUST point to the current head. **Never guess or copy from older migrations.**

```python
# CORRECT: Points to actual current head (verified via `alembic heads`)
revision: str = "abc123def456"
down_revision: Union[str, Sequence[str], None] = "43c07ed25a24"  # Current head

# WRONG: Creates multiple heads (breaks all tests)
down_revision: Union[str, Sequence[str], None] = "some_old_revision"
```

### Idempotent Migrations Pattern

Always write idempotent migrations that check before modifying:

```python
def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())

    # Skip if table doesn't exist (fresh DB uses db.py models directly)
    if "my_table" not in inspector.get_table_names():
        return

    # Skip if column already exists
    columns = [col["name"] for col in inspector.get_columns("my_table")]
    if "new_column" in columns:
        return

    op.add_column("my_table", sa.Column("new_column", sa.String(), nullable=True))
```

### Verification

```bash
# Verify single head after creating migration
cd mcpgateway && alembic heads
# Should show only ONE head

# Run tests to confirm migrations work
make test
```

### Common Errors

- **"Multiple heads are present"**: Your `down_revision` points to wrong parent. Fix by updating to actual current head.
- **"Target database is not up to date"**: Run `alembic upgrade head` first.

## Coding Standards

- **Python >= 3.11** with type hints; strict mypy
- **Formatting**: Black (line length 200), isort (profile=black)
- **Linting**: Ruff (F,E,W,B,ASYNC), Pylint per `pyproject.toml`
- **Naming**: `snake_case` functions/modules, `PascalCase` classes, `UPPER_CASE` constants
- **Imports**: Group per isort sections (stdlib, third-party, first-party `mcpgateway`, local)

## Commit & PR Standards

- **Sign commits**: `git commit -s` (DCO requirement)
- **Conventional Commits**: `feat:`, `fix:`, `docs:`, `refactor:`, `chore:`
- **Link issues**: `Closes #123`
- Include tests for behavior changes
- Require green lint and tests before PR
- Don't push until asked, and if it's an external contributor, see todo/force-push.md first to push to the contributor's branch.

## Important Constraints

- Never mention AI assistants in PRs/diffs
- Do not include test plans or effort estimates in PRs
- Never create files unless absolutely necessary; prefer editing existing files
- Never proactively create documentation files unless explicitly requested
- Never commit secrets; use `.env` for configuration

## Key Files

- `mcpgateway/main.py` - Application entry point
- `mcpgateway/config.py` - Environment configuration
- `mcpgateway/db.py` - SQLAlchemy ORM models and session management
- `mcpgateway/schemas.py` - Pydantic schemas
- `pyproject.toml` - Project configuration
- `Makefile` - Build automation
- `.env.example` - Environment template
- `.pre-commit-lite.yaml` - Pre-commit config used by CI (`make pre-commit`)
- `.pre-commit-config.yaml` - Full pre-commit config for local dev

## CLI Tools Available

- `gh` for GitHub operations
- `make` for build/test automation
- `uv` for virtual environment management
- Standard tools: pytest, black, isort, ruff, pylint
