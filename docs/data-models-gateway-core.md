# Data Models - Gateway Core

## Overview

MCP Context Forge uses SQLAlchemy ORM with 50+ models across 10 functional areas. The database supports SQLite (development), PostgreSQL (production), and MySQL/MariaDB, with 69 Alembic migrations tracking schema evolution.

---

## 1. Core MCP Entity Models

### Tool (`tools`)
The central entity representing an MCP tool registered in the gateway.

| Column | Type | Notes |
|--------|------|-------|
| `id` | String(36) PK | UUID |
| `original_name` | String(255) | Name from upstream MCP server |
| `name` | String(255) | Computed: `custom_name_slug` or `gateway_slug/original_name` |
| `url` | String(767) | Tool endpoint URL |
| `description` | Text | Tool description |
| `integration_type` | String(20) | `MCP`, `REST`, `A2A` |
| `request_type` | String(20) | `SSE`, `GET`, `POST`, `PUT`, `DELETE`, `PATCH`, `STDIO` |
| `input_schema` | JSON | JSON Schema for tool input |
| `output_schema` | JSON | JSON Schema for tool output |
| `annotations` | JSON | MCP tool annotations |
| `tags` | JSON | Tag list |
| `enabled` / `reachable` | Boolean | Status flags |
| `gateway_id` | FK(gateways.id) | Parent gateway |
| `team_id` | FK(email_teams.id) | Multi-tenant scoping |
| `owner_email` | String(255) | Owner |
| `visibility` | String(20) | `public`, `private`, `team` |
| `plugin_chain_pre/post` | JSON | Pre/post plugin chains |
| Audit columns | Various | `created_by`, `modified_by`, `created_from_ip`, etc. |

**Relationships**: `gateway`, `servers` (M2M), `metrics`
**Computed Metrics**: `execution_count`, `failure_rate`, `avg_response_time`, `metrics_summary`

### Resource (`resources`)
MCP resources (files, data, URIs) available through the gateway.

| Column | Type | Notes |
|--------|------|-------|
| `id` | String(36) PK | UUID |
| `uri` | String(767) | Resource URI |
| `name` | String(255) | Display name |
| `mime_type` | String(255) | Content type |
| `text_content` | Text | Text content |
| `binary_content` | LargeBinary | Binary content |
| `uri_template` | Text | URI template for dynamic resources |
| Multi-tenant fields | Various | Same as Tool |

**Relationships**: `gateway`, `servers` (M2M), `subscriptions`, `metrics`

### Prompt (`prompts`)
MCP prompts with template and argument validation.

| Column | Type | Notes |
|--------|------|-------|
| `id` | String(36) PK | UUID |
| `template` | Text | Prompt template |
| `argument_schema` | JSON | Argument validation schema |
| Multi-tenant + audit fields | Various | Same as Tool |

**Methods**: `validate_arguments()` for input validation

### Server (`servers`)
Virtual MCP servers that compose tools, resources, and prompts.

| Column | Type | Notes |
|--------|------|-------|
| `id` | String(36) PK | UUID |
| `name` | String(255) | Server name |
| `oauth_enabled` | Boolean | Enable per-server OAuth |
| `oauth_config` | JSON | OAuth configuration |
| Multi-tenant fields | Various | Same as Tool |

**Relationships**: `tools` (M2M), `resources` (M2M), `prompts` (M2M), `a2a_agents` (M2M), `scoped_tokens`

### Gateway (`gateways`)
Upstream MCP server connections (the servers the gateway proxies to).

| Column | Type | Notes |
|--------|------|-------|
| `id` | String(36) PK | UUID |
| `slug` | String(255) | URL-safe identifier |
| `url` | String(767) | Upstream URL |
| `transport` | String(20) | `SSE`, `WebSocket`, etc. |
| `capabilities` | JSON | MCP capabilities |
| `auth_type` | String(20) | `basic`, `bearer`, `headers`, `oauth`, `query_param` |
| `auth_value` | JSON | Auth credentials (encrypted) |
| `gateway_mode` | String(20) | `cache` or `direct_proxy` |
| `refresh_interval_seconds` | Integer | Auto-refresh interval |
| Multi-tenant fields | Various | Same as Tool |

**Relationships**: `tools`, `prompts`, `resources`, `oauth_tokens`, `registered_oauth_clients`

### A2AAgent (`a2a_agents`)
Agent-to-Agent protocol agents.

| Column | Type | Notes |
|--------|------|-------|
| `id` | String(36) PK | UUID |
| `agent_type` | String(50) | `openai`, `anthropic`, `custom` |
| `endpoint_url` | String(767) | Agent endpoint |
| `protocol_version` | String(10) | A2A protocol version |
| `capabilities` | JSON | Agent capabilities |
| `tool_id` | FK(tools.id) | Associated MCP tool |

### GrpcService (`grpc_services`)
gRPC services with reflection-based discovery.

| Column | Type | Notes |
|--------|------|-------|
| `id` | String(36) PK | UUID |
| `target` | String(767) | `host:port` |
| `reflection_enabled` | Boolean | Use gRPC reflection |
| `discovered_services` | JSON | Reflection results |
| `service_count` / `method_count` | Integer | Discovery counts |

---

## 2. Authentication & User Management (11 models)

### EmailUser (`email_users`)
| Column | Type | Notes |
|--------|------|-------|
| `email` | String(255) PK | Primary identifier |
| `password_hash` | String(255) | Argon2 hash |
| `is_admin` | Boolean | Platform admin flag |
| `admin_origin` | String(20) | `sso`, `manual`, `api` |
| `auth_provider` | String(50) | Auth method |
| `failed_login_attempts` | Integer | Brute-force protection |
| `locked_until` | DateTime | Account lockout |
| `password_change_required` | Boolean | Force password change |

**Methods**: `is_account_locked()`, `get_teams()`, `get_personal_team()`, `is_team_member()`

### EmailTeam (`email_teams`)
| Column | Type | Notes |
|--------|------|-------|
| `id` | String PK | UUID |
| `name` / `slug` | String(255) | Team identifiers |
| `visibility` | String(20) | `private`, `public` |
| `is_personal` | Boolean | Auto-created personal team |
| `max_members` | Integer | Member limit |

### Supporting Models
- **EmailTeamMember**: Team membership with roles (`owner`, `member`)
- **EmailTeamMemberHistory**: Audit trail for membership changes
- **EmailTeamInvitation**: Token-based team invitations with expiry
- **EmailTeamJoinRequest**: Public team join requests with approval workflow
- **PendingUserApproval**: SSO user registration approval queue
- **EmailAuthEvent**: Login/registration audit log
- **PasswordResetToken**: Time-limited password reset tokens

---

## 3. RBAC Models (3 models)

### Role (`roles`)
| Column | Type | Notes |
|--------|------|-------|
| `id` | String PK | UUID |
| `name` | String(255) | Role name |
| `scope` | String(20) | `global`, `team`, `personal` |
| `permissions` | JSON | Permission list |
| `inherits_from` | FK(roles.id) | Role hierarchy |
| `is_system_role` | Boolean | Built-in vs custom |

### UserRole (`user_roles`)
Role assignments with optional team scoping and expiration.

### PermissionAuditLog (`permission_audit_log`)
Records every permission check: user, permission, resource, granted/denied, IP.

---

## 4. OAuth Models (3 models)

### OAuthToken (`oauth_tokens`)
Per-user OAuth tokens keyed by `(gateway_id, app_user_email)`.

### OAuthState (`oauth_states`)
CSRF protection and PKCE code verifier for OAuth flows.

### RegisteredOAuthClient (`registered_oauth_clients`)
Dynamic Client Registration (DCR) results, keyed by `(gateway_id, issuer)`.

---

## 5. API Token Model

### EmailApiToken (`email_api_tokens`)
| Column | Type | Notes |
|--------|------|-------|
| `id` | String(36) PK | UUID |
| `jti` | String(36) UNIQUE | JWT ID for revocation |
| `token_hash` | String(255) | SHA256 hash |
| `resource_scopes` | JSON | e.g., `['tools.read', 'resources.read']` |
| `ip_restrictions` | JSON | IP allowlist |
| `time_restrictions` | JSON | Time-based access |
| `usage_limits` | JSON | Rate limiting |
| `server_id` | FK(servers.id) | Scoped to server |

---

## 6. Metrics Models (10 models)

### Raw Metrics (5 tables)
`tool_metrics`, `resource_metrics`, `server_metrics`, `prompt_metrics`, `a2a_agent_metrics`

Each records: `entity_id`, `timestamp`, `response_time`, `is_success`, `error_message`

### Hourly Rollups (5 tables)
`tool_metrics_hourly`, `resource_metrics_hourly`, `server_metrics_hourly`, `prompt_metrics_hourly`, `a2a_agent_metrics_hourly`

Pre-aggregated: `total_count`, `success_count`, `failure_count`, `min/max/avg/p50/p95/p99_response_time`

---

## 7. Observability Models (5 models)

- **ObservabilityTrace**: Top-level trace with HTTP metadata, user info, duration
- **ObservabilitySpan**: Nested spans within traces (parent-child hierarchy)
- **ObservabilityEvent**: Events within spans (errors, exceptions, annotations)
- **ObservabilityMetric**: Counter/gauge/histogram metrics linked to traces
- **ObservabilitySavedQuery**: User-saved trace query configurations

---

## 8. Performance Models (2 models)

- **PerformanceSnapshot**: Per-worker metrics snapshots (CPU, memory, requests)
- **PerformanceAggregate**: Hourly/daily aggregates with p95 latency, error rates

---

## 9. Session Models (2 models)

- **SessionRecord** (`mcp_sessions`): MCP session data with TTL
- **SessionMessageRecord** (`mcp_messages`): Messages within sessions

---

## 10. Association Tables (M2M)

| Table | Connects |
|-------|----------|
| `server_tool_association` | Server <-> Tool |
| `server_resource_association` | Server <-> Resource |
| `server_prompt_association` | Server <-> Prompt |
| `server_a2a_association` | Server <-> A2AAgent |

---

## Key Design Patterns

### Multi-Tenancy
All core entities include `team_id`, `owner_email`, `visibility` for data isolation.

### Audit Trail
All entities track `created_by/modified_by`, `created_from_ip/modified_from_ip`, `created_via/modified_via`, `created_user_agent/modified_user_agent`.

### Federation
Entities support `gateway_id`, `federation_source`, `import_batch_id`, `version` for cross-instance federation.

### Two-Tier Metrics
Raw per-request metrics + pre-aggregated hourly rollups with percentiles for efficient historical queries.

### Hybrid Properties
Tool, Prompt, Gateway use SQLAlchemy `hybrid_property` for computed fields that work both in Python and SQL.

---

## Database Configuration

| Database | Connection | Notes |
|----------|-----------|-------|
| SQLite | `sqlite:///./mcp.db` | WAL mode, FK constraints, 64MB cache |
| PostgreSQL | `postgresql+psycopg://...` | Keep-alive, prepared statements, pool management |
| MariaDB | `mysql+pymysql://...` | READ_COMMITTED isolation |

**Resilience**: `ResilientSession` with auto-rollback, pool pre-ping, PgBouncer compatibility (NullPool option).

---

## Migration Summary

**Total Migrations**: 69 (Alembic)
**Key Categories**: Core tables, auth/users, OAuth, metrics/observability, team scoping, A2A agents, gRPC, indexes, data migrations
