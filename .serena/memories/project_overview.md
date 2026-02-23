# MCP Context Forge - Project Overview

## Purpose
MCP Gateway (ContextForge) is a production-grade gateway, proxy, and registry for Model Context Protocol (MCP) servers and A2A (Agent-to-Agent) Agents. It federates MCP and REST services, providing unified discovery, authentication, rate-limiting, observability, virtual servers, multi-transport protocols, and an optional Admin UI.

## Tech Stack
- **Backend**: FastAPI (Python 3.11+), Pydantic validation, SQLAlchemy ORM, Starlette ASGI
- **Frontend/Admin UI**: HTMX + Alpine.js, Jinja2 templates
- **Database**: SQLite (default), PostgreSQL (optional), Redis for caching/federation
- **Migrations**: Alembic
- **Transports**: SSE, WebSocket, stdio, streamable HTTP
- **Auth**: JWT (PyJWT), Basic Auth, OAuth, Argon2 password hashing
- **Observability**: OpenTelemetry (optional), Prometheus metrics
- **Server**: Uvicorn (dev), Gunicorn (production), Granian (optional Rust-based)
- **Package Manager**: uv (replaces pip)

## Project Structure
```
mcpgateway/              # Core FastAPI application (~20 top-level files)
  ├── main.py            # Application entry point
  ├── config.py          # Environment configuration (pydantic-settings)
  ├── db.py              # SQLAlchemy ORM models and session management
  ├── schemas.py         # Pydantic validation schemas
  ├── auth.py            # Authentication and token handling
  ├── cli.py             # CLI entry point (typer)
  ├── services/          # Business logic layer (55+ services)
  ├── routers/           # HTTP endpoint definitions (19 routers)
  ├── middleware/         # Cross-cutting concerns (15 middleware)
  ├── transports/        # Protocol implementations
  ├── plugins/           # Plugin framework infrastructure
  ├── alembic/           # Database migrations
  ├── handlers/          # Request handlers
  ├── validation/        # Input validation
  ├── cache/             # Caching layer
  ├── common/            # Shared utilities
  ├── utils/             # Utility functions
  ├── static/            # CSS/JS for admin UI
  └── templates/         # Jinja2 templates

tests/                   # Test suite (unit, integration, e2e, security, fuzz, playwright)
plugins/                 # Plugin implementations
charts/                  # Helm charts for Kubernetes
deployment/              # Infrastructure configs
docs/                    # Mintlify documentation site
a2a-agents/              # A2A agent implementations
mcp-servers/             # MCP server templates
llms/                    # End-user LLM guidance (runtime, not for development)
```

## Key Entry Points
- `mcpgateway.main:app` - FastAPI application
- `mcpgateway.cli:main` - CLI (`mcpgateway` command)
- `mcpgateway.plugins.tools.cli:main` - Plugin CLI (`mcpplugins` command)
- `mcpgateway.tools.cli:main` - Tools CLI (`cforge` command)

## Environment
- Configure via `.env` file (copy `.env.example`)
- Key vars: `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET_KEY`, `AUTH_REQUIRED`, `PORT`
- Default port: 4444 (production), 8000 (dev)
