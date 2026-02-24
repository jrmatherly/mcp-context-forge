# Project Overview - MCP Context Forge

## Purpose

MCP Context Forge (Apollos AI Gateway) is a production-grade gateway, proxy, and registry for Model Context Protocol (MCP) servers and Agent-to-Agent (A2A) Agents. It federates MCP and REST services into a unified endpoint for AI clients, providing discovery, authentication, rate-limiting, observability, virtual servers, multi-transport protocols, and an optional Admin UI.

## Repository Type

**Monorepo** with 8 distinct parts spanning Python, Rust, Go, TypeScript, and infrastructure-as-code.

## Version

- **Application**: `1.0.0rc1` (PEP 440)
- **Helm Chart**: `1.0.0-rc.1` (SemVer)
- **Rust Plugins**: `1.0.0-rc.1` (SemVer)

## Parts Summary

| Part | Path | Type | Language | Description |
|------|------|------|----------|-------------|
| Gateway Core | `mcpgateway/` | backend | Python 3.11+ | FastAPI application - the main gateway service |
| Python Plugins | `plugins/` | library | Python | 45+ security, transformation, and policy plugins |
| Rust Plugins | `plugins_rust/` | library | Rust (Edition 2024) | High-performance security plugins via PyO3 |
| MCP Servers | `mcp-servers/` | backend | Python, Go, Rust | 20+ MCP server implementations + templates |
| A2A Agents | `a2a-agents/` | backend | Go | Agent-to-Agent protocol implementations |
| Infrastructure | `charts/`, `deployment/` | infra | Helm, Terraform | Kubernetes deployment and IaC |
| Documentation | `docs/` | web | Mintlify | Comprehensive documentation site |
| Agent Runtimes | `agent_runtimes/` | library | Python | LangChain-based agent runtime |

## Technology Stack

### Core Gateway
| Category | Technology | Version |
|----------|-----------|---------|
| Language | Python | >=3.11, <3.14 |
| Framework | FastAPI + Starlette | >=0.129.0 |
| ORM | SQLAlchemy | >=2.0.46 |
| Validation | Pydantic | >=2.12.5 |
| Migrations | Alembic | >=1.18.4 |
| Auth | PyJWT + Argon2 | >=2.11.0 |
| HTTP Client | httpx (HTTP/2) | >=0.28.1 |
| MCP SDK | mcp | >=1.26.0 |
| Serialization | orjson | >=3.11.7 |
| Server | Uvicorn / Gunicorn | >=0.41.0 |
| Admin UI | HTMX + Alpine.js | - |
| JS Tooling | Biome + Vitest | >=2.4.4 |

### Database Support
| Database | Adapter | Use Case |
|----------|---------|----------|
| SQLite | Built-in | Development default |
| PostgreSQL | psycopg3 | Production recommended |
| MariaDB/MySQL | pymysql/mariadb | Alternative production |
| Redis | redis-py + hiredis | Caching, federation, sessions |

### Observability
| Tool | Purpose |
|------|---------|
| Prometheus | Metrics collection |
| OpenTelemetry | Distributed tracing (optional) |
| Phoenix/Jaeger/Zipkin | Trace visualization |

## Architecture

### Pattern
Service Gateway / API Gateway with middleware pipeline, plugin hooks, and multi-transport support.

### Key Architectural Decisions
- **19 routers** handling REST API endpoints
- **56 services** implementing business logic
- **15 middleware** components for cross-cutting concerns
- **5 transport protocols**: SSE, WebSocket, stdio, Streamable HTTP, base ABC
- **9 cache layers**: auth, registry, resource, tool lookup, metrics, admin stats, A2A stats, config, sessions
- **50+ database models** with multi-tenancy support
- **70 Alembic migrations** tracking schema evolution

### Security Model
Two-layer security:
1. **Token Scoping (Layer 1)**: JWT `teams` claim filters resource visibility
2. **RBAC (Layer 2)**: Role-based permissions control actions

### Multi-Tenancy
All core entities support `team_id`, `owner_email`, and `visibility` for data isolation across teams.

## Entry Points

| Entry Point | Command | Description |
|-------------|---------|-------------|
| `mcpgateway.main:app` | - | FastAPI application |
| `mcpgateway.cli:main` | `mcpgateway` | CLI tool |
| `mcpgateway.plugins.tools.cli:main` | `mcpplugins` | Plugin CLI |
| `mcpgateway.tools.cli:main` | `cforge` | Context Forge CLI |

## License

Apache-2.0
