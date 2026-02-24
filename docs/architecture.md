# Architecture - MCP Context Forge

## Executive Summary

MCP Context Forge implements a **Service Gateway** pattern for the Model Context Protocol ecosystem. Built on FastAPI/Starlette ASGI, it sits in front of MCP servers, REST APIs, gRPC services, and A2A agents, exposing a unified federated endpoint. The architecture emphasizes multi-tenancy, pluggable security, protocol translation, and horizontal scalability via Redis-backed federation.

## Architecture Pattern

**Primary**: API Gateway / Service Gateway
**Secondary**: Middleware Pipeline, Plugin Architecture, Event-Driven (for metrics/observability)

```
AI Clients (Claude, GPT, etc.)
        |
        v
  +------------------+
  |  MCP Gateway      |
  |  (FastAPI/ASGI)   |
  |                   |
  | Middleware Pipeline|
  | Auth -> Scoping -> |
  | RBAC -> Logging    |
  |                   |
  | Plugin Hooks      |
  | Pre/Post chains   |
  +------------------+
        |
   +----+----+----+----+
   |    |    |    |    |
   v    v    v    v    v
  MCP  REST gRPC  A2A  Virtual
  Svrs APIs Svcs Agents Servers
```

## Technology Stack

See [project-overview.md](./project-overview.md) for the full technology table.

## Services Layer (55+ services)

Services are organized into 12 functional areas:

| Area | Count | Key Services |
|------|-------|-------------|
| Core MCP Protocol | 4 | ToolService, ResourceService, PromptService, GatewayService |
| Server Management | 1 | ServerService |
| Auth & Authorization | 6 | PermissionService, OAuthManager, EmailAuthService, SSOService, RoleService, TokenStorageService |
| Team Management | 3 | TeamManagementService, TeamInvitationService, PersonalTeamService |
| Observability & Logging | 8 | ObservabilityService, LoggingService, AuditTrailService, StructuredLogger, LogAggregator, LogStorageService, SecurityLogger, Metrics |
| Metrics & Performance | 7 | MetricsBufferService, MetricsRollupService, MetricsQueryService, MetricsCleanupService, PerformanceTracker, PerformanceService, EventService |
| Data Management | 6 | ExportService, ImportService, CatalogService, CompletionService, CancellationService, TagService |
| Security & Infrastructure | 6 | EncryptionService, Argon2PasswordService, HTTPClientService, ElicitationService, PluginService, RootService |
| LLM Integration | 3 | LLMProviderService, LLMProxyService, MCPClientChatService |
| MCP Transport | 2 | MCPSessionPool, NotificationService |
| Admin & Support | 2 | SupportBundleService, A2AAgentService |
| Specialized | 3 | LLMChatService, DCRService, A2AService |

### Performance Characteristics

- **MCP Session Pool**: 20-23ms to 1-2ms per tool call (10-20x improvement)
- **Shared HTTP Client**: Connection pooling avoids TCP/TLS overhead per request
- **Metrics Buffer**: Batched writes reduce database load
- **Permission Caching**: 5-minute TTL with in-memory cache

## Application Lifecycle

### Startup Sequence

1. **Database Readiness**: Wait for DB, bootstrap schema, run Alembic migrations
2. **Plugin Initialization**: Load plugin manager if `PLUGINS_ENABLED=true`
3. **Service Instantiation**: Core services (gateway, server, tool, resource, prompt, completion, sampling, tags, export/import, A2A)
4. **Cache Warmup**: Redis readiness check, session registry init, resource cache warmup
5. **Background Services**: Metrics buffer/rollup/cleanup, log aggregator, elicitation, MCP session pool
6. **SSO Bootstrap**: Provider configuration from environment (GitHub, Google, Okta, Keycloak, EntraID)
7. **Cache Invalidation**: Start subscriber for distributed cache coordination

### Shutdown Sequence (reverse order)

Metrics flush -> Service shutdown -> Cache cleanup -> Plugin shutdown -> Session pool close -> HTTP client close -> Redis close

## Middleware Pipeline

Middleware executes in reverse registration order (innermost first in request flow):

| Order | Middleware | Purpose |
|-------|-----------|---------|
| 1 | ProxyHeaders | Extract real IP from proxy headers |
| 2 | CorrelationID | Add request ID for distributed tracing |
| 3 | AuthContext | Extract auth context from verified JWT |
| 4 | TokenUsage | Track token usage and rate-limiting |
| 5 | Observability | OpenTelemetry instrumentation |
| 6 | AdminAuth | Protect admin-only endpoints |
| 7 | DocsAuth | Protect `/docs` and `/openapi.json` |
| 8 | RequestLogging | Detailed request/response logging |
| 9 | SSEAwareCompress | Response compression (skip SSE streams) |
| 10 | HttpAuth | Plugin-based HTTP auth hooks |
| 11 | MCPPathRewrite | Rewrite MCP paths with token scoping |
| 12 | TokenScoping | Filter resources by token teams |
| 13 | Validation | Input validation (experimental) |
| 14 | MCPProtocolVersion | Validate MCP protocol version |
| 15 | SecurityHeaders | HSTS, CSP, X-Frame-Options, etc. |
| 16 | CORS | CORS policy enforcement |

## Authentication Architecture

### Two-Layer Security Model

**Layer 1 - Token Scoping** (what users CAN SEE):
- JWT `teams` claim determines resource visibility
- `normalize_token_teams()` in `auth.py` is the single source of truth
- Missing `teams` key = public-only (secure default)
- `teams: null` + `is_admin: true` = admin bypass (sees all resources)

**Layer 2 - RBAC** (what users CAN DO):
- Role-based permissions via `Role`/`UserRole` models
- Built-in roles: `platform_admin`, `team_admin`, `developer`, `viewer`
- Permission checking middleware on every request

### Auth Methods
1. **JWT Session Tokens**: Standard login flow
2. **API Tokens**: Long-lived, scoped tokens with SHA256 hash storage
3. **OAuth 2.0**: Authorization Code flow with PKCE for upstream servers
4. **SSO/OIDC**: 6+ providers (GitHub, Google, Okta, Keycloak, EntraID, generic)
5. **Plugin Auth**: Extensible via `HTTP_AUTH_RESOLVE_USER` hook

### Token Validation Pipeline
Plugin auth (if configured) -> JWT decode -> JTI revocation check -> User DB lookup -> API token fallback -> Team resolution

## Transport Layer

| Transport | Protocol | Direction | Session | Use Case |
|-----------|----------|-----------|---------|----------|
| SSE | HTTP/1.1 streaming | Server -> Client | Per-connection | Browser clients |
| WebSocket | RFC 6455 | Full-duplex | Per-connection | Low-latency clients |
| stdio | stdin/stdout | Full-duplex | N/A | CLI tools, subprocesses |
| Streamable HTTP | HTTP polling + optional SSE | Full-duplex | Optional (stateful/stateless) | Universal HTTP clients |

Configured via `TRANSPORT_TYPE`: `http`, `websocket`, or `all` (default).

## Data Architecture

### Database Models (50+)

| Area | Models | Key Tables |
|------|--------|------------|
| Core MCP | 7 | `tools`, `resources`, `prompts`, `servers`, `gateways`, `a2a_agents`, `grpc_services` |
| Auth/Users | 11 | `email_users`, `email_teams`, `email_team_members`, `roles`, `user_roles` |
| OAuth | 3 | `oauth_tokens`, `oauth_states`, `registered_oauth_clients` |
| Metrics | 10 | Raw metrics (5) + hourly rollups (5) |
| Observability | 5 | `observability_traces`, `observability_spans`, `observability_events`, `observability_metrics` |
| Performance | 2 | `performance_snapshots`, `performance_aggregates` |
| Sessions | 2 | `mcp_sessions`, `mcp_messages` |

See [data-models-gateway-core.md](./data-models-gateway-core.md) for complete schema documentation.

### Multi-Tenancy Pattern
All core entities include:
- `team_id` (FK to `email_teams`)
- `owner_email` (String)
- `visibility` (`public`, `private`, `team`)

### Metrics Two-Tier Strategy
- **Raw metrics**: Per-request records for recent data
- **Hourly rollups**: Pre-aggregated with percentiles (p50, p95, p99) for historical queries

## Plugin Architecture

### Plugin Types
- **Python Plugins** (`plugins/`): 45+ plugins using stevedore entry points
- **Rust Plugins** (`plugins_rust/`): High-performance via PyO3 FFI bridge
- **External Plugins** (`plugins/external/`): Separate process plugins (Cedar, OPA, LLMGuard)

### Plugin Chain
Tools support `plugin_chain_pre` and `plugin_chain_post` for request/response transformation.

### Plugin Categories
- **Security**: secrets_detection, pii_filter, encoded_exfil_detector, sql_sanitizer, content_moderation
- **Transformation**: json_repair, html_to_markdown, code_formatter, markdown_cleaner, argument_normalizer
- **Policy**: rate_limiter, output_length_guard, circuit_breaker, schema_guard, robots_license_guard
- **Infrastructure**: cached_tool_result, retry_with_backoff, webhook_notification, tools_telemetry_exporter

## API Design

See [api-contracts-gateway-core.md](./api-contracts-gateway-core.md) for the full 150+ endpoint catalog.

### Router Organization (19 routers)
- **Auth**: auth, email_auth, sso
- **Management**: teams, tokens, rbac
- **OAuth**: oauth_router
- **Observability**: observability, log_search, metrics_maintenance
- **LLM**: llm_proxy, llmchat, llm_config, llm_admin
- **Protocol**: well_known, server_well_known, cancellation, toolops
- **Infrastructure**: reverse_proxy

## Caching Strategy

| Cache Layer | Backend | Purpose |
|-------------|---------|---------|
| Auth Cache | Redis/Memory | JWT validation results |
| Registry Cache | Redis/Memory | Gateway/server registry |
| Resource Cache | Redis/Memory | Resource content |
| Tool Lookup Cache | Redis/Memory | Tool resolution |
| Metrics Cache | Redis/Memory | Aggregated metrics |
| Admin Stats Cache | Redis/Memory | Dashboard statistics |
| A2A Stats Cache | Redis/Memory | Agent statistics |
| Global Config Cache | Redis/Memory | System configuration |
| Session Registry | Redis/Memory/DB | MCP session management |

## Deployment Architecture

### Container
- **Containerfile**: Multi-stage build with Python 3.12
- **Containerfile.lite**: Minimal image without optional dependencies
- **Docker Compose**: Full stack with PostgreSQL, Redis, optional Phoenix/PgAdmin

### Kubernetes
- **Helm Chart**: `mcp-stack` bundles gateway + PostgreSQL + Redis
- **Kubernetes**: >=1.21.0 required
- **Terraform**: IBM Cloud modules for VPC, K8s, PostgreSQL, Redis

### Scaling
- **Horizontal**: Multiple gateway instances with Redis-backed federation
- **Session Affinity**: Multi-worker session management
- **Connection Pooling**: PgBouncer support with NullPool option

## Testing Strategy

| Test Type | Framework | Location |
|-----------|-----------|----------|
| Unit | pytest | `tests/unit/` |
| Integration | pytest | `tests/integration/` |
| E2E | pytest | `tests/e2e/` |
| Security | pytest + bandit | `tests/security/` |
| Fuzz | hypothesis + atheris | `tests/fuzz/` |
| UI | Playwright | `tests/playwright/` |
| Performance | Locust + JMeter | `tests/performance/`, `tests/load/` |
| JS Frontend | Vitest | `tests/js/` (via `vitest.config.js`) |
| Mutation | mutmut | Configured in `pyproject.toml` |

## Configuration

200+ environment variables organized by category. See `mcpgateway/config.py` (Pydantic Settings) for the complete list.

Key categories: Core, Authentication/JWT, Email Auth, Password Policy, SSO, CORS, Security Headers, Compression, Transport, Features, Logging, Observability, SSRF Protection, Cache/Redis.
