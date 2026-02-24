# API Contracts - Gateway Core

## Overview

MCP Context Forge exposes a comprehensive REST API through 19 FastAPI routers with 150+ endpoints covering MCP operations, authentication, team management, RBAC, observability, and administration.

**Base URL**: Configurable via `APP_DOMAIN` (default: `http://localhost:4444`)
**Authentication**: JWT Bearer tokens (session or API), OAuth 2.0, SSO/OIDC, email/password
**Protocol**: JSON-RPC 2.0 for MCP operations, REST for management APIs

---

## Authentication Router (`/auth`)

| Method | Path | Summary | Auth |
|--------|------|---------|------|
| POST | `/auth/login` | Authenticate user and return session JWT | None |

---

## Email Authentication (`/auth/email`)

| Method | Path | Summary | Auth |
|--------|------|---------|------|
| POST | `/register` | Register new user | None |
| POST | `/login` | Login with email/password | None |
| POST | `/forgot-password` | Request password reset | None |
| POST | `/reset-password` | Reset password with token | None |
| POST | `/change-password` | Change password (authenticated) | Required |
| POST | `/validate-password-reset-token` | Validate reset token | None |
| POST | `/admin/users` | Create user (admin) | `admin.user_management` |
| GET | `/admin/users` | List all users (paginated) | `admin.user_management` |
| GET | `/admin/users/{user_id}` | Get user details | `admin.user_management` |
| PUT | `/admin/users/{user_id}` | Update user | `admin.user_management` |
| DELETE | `/admin/users/{user_id}` | Delete user | `admin.user_management` |
| GET | `/admin/auth-events/{user_id}` | Get auth events | `admin.user_management` |

---

## SSO Authentication (`/auth/sso`)

| Method | Path | Summary | Auth |
|--------|------|---------|------|
| GET | `/providers` | List available SSO providers | None |
| GET | `/login/{provider_id}` | Initiate SSO login | None |
| GET | `/callback/{provider_id}` | Handle SSO callback | None |
| POST | `/admin/providers` | Create SSO provider | `admin.sso_providers:create` |
| GET | `/admin/providers` | List all SSO providers | `admin.sso_providers:read` |
| GET | `/admin/providers/{provider_id}` | Get SSO provider | `admin.sso_providers:read` |
| PUT | `/admin/providers/{provider_id}` | Update SSO provider | `admin.sso_providers:update` |
| DELETE | `/admin/providers/{provider_id}` | Delete SSO provider | `admin.sso_providers:delete` |
| GET | `/pending-approvals` | List pending user approvals | `admin.user_management` |
| POST | `/pending-approvals/{id}/action` | Approve/reject registration | `admin.user_management` |

---

## Teams (`/teams`)

| Method | Path | Summary | Auth |
|--------|------|---------|------|
| POST | `/` | Create new team | `teams.create` |
| GET | `/` | List teams visible to caller | `teams.read` |
| GET | `/discover` | Discover public teams | `teams.read` |
| GET | `/{team_id}` | Get specific team | `teams.read` |
| PUT | `/{team_id}` | Update team | `teams.update` |
| DELETE | `/{team_id}` | Delete team | `teams.delete` |
| GET | `/{team_id}/members` | List team members | `teams.read` |
| POST | `/{team_id}/members` | Add team member | `teams.manage_members` |
| PUT | `/{team_id}/members/{email}` | Update member role | `teams.manage_members` |
| DELETE | `/{team_id}/members/{email}` | Remove team member | `teams.manage_members` |
| POST | `/{team_id}/invitations` | Invite user to team | `teams.manage_members` |
| GET | `/{team_id}/invitations` | List team invitations | `teams.read` |
| POST | `/invitations/{token}/accept` | Accept team invitation | `teams.read` |
| DELETE | `/invitations/{id}` | Cancel team invitation | `teams.manage_members` |
| POST | `/{team_id}/join` | Request to join public team | None |
| DELETE | `/{team_id}/leave` | Leave team | None |
| GET | `/{team_id}/join-requests` | List pending join requests | `teams.manage_members` |
| POST | `/{team_id}/join-requests/{id}/approve` | Approve join request | `teams.manage_members` |
| DELETE | `/{team_id}/join-requests/{id}` | Reject join request | `teams.manage_members` |

---

## API Tokens (`/tokens`)

| Method | Path | Summary | Auth |
|--------|------|---------|------|
| POST | `/tokens` | Create new API token | `tokens.create` |
| GET | `/tokens` | List API tokens | `tokens.read` |
| GET | `/tokens/{token_id}` | Get token details | `tokens.read` |
| PUT | `/tokens/{token_id}` | Update token | `tokens.update` |
| DELETE | `/tokens/{token_id}` | Revoke token | `tokens.revoke` |
| GET | `/tokens/{token_id}/usage` | Get token usage stats | `tokens.read` |
| GET | `/tokens/admin/all` | List all tokens (admin) | Admin |
| DELETE | `/tokens/admin/{token_id}` | Admin revoke token | Admin |
| POST | `/tokens/teams/{team_id}` | Create team token | `tokens.create` |
| GET | `/tokens/teams/{team_id}` | List team tokens | `tokens.read` |

---

## RBAC (`/rbac`)

| Method | Path | Summary | Auth |
|--------|------|---------|------|
| POST | `/rbac/roles` | Create new role | Admin |
| GET | `/rbac/roles` | List all roles | `admin.user_management` |
| GET | `/rbac/roles/{role_id}` | Get role details | `admin.user_management` |
| PUT | `/rbac/roles/{role_id}` | Update role | Admin |
| DELETE | `/rbac/roles/{role_id}` | Delete role | Admin |
| POST | `/rbac/users/{email}/roles` | Assign role to user | `admin.user_management` |
| GET | `/rbac/users/{email}/roles` | Get user roles | `admin.user_management` |
| DELETE | `/rbac/users/{email}/roles/{id}` | Revoke user role | `admin.user_management` |
| POST | `/rbac/permissions/check` | Check user permission | `admin.security_audit` |
| GET | `/rbac/permissions/user/{email}` | Get user permissions | `admin.security_audit` |
| GET | `/rbac/permissions/available` | Get available permissions | None |
| GET | `/rbac/my/roles` | Get my roles | None |
| GET | `/rbac/my/permissions` | Get my permissions | None |

---

## OAuth (`/oauth`)

| Method | Path | Summary | Auth |
|--------|------|---------|------|
| GET | `/oauth/authorize/{gateway_id}` | Initiate OAuth flow | Required |
| GET | `/oauth/callback` | OAuth callback handler | None |
| GET | `/oauth/status/{gateway_id}` | Get OAuth status | Required |
| POST | `/oauth/fetch-tools/{gateway_id}` | Fetch tools after OAuth | Required |
| GET | `/oauth/registered-clients` | List registered OAuth clients | Admin |
| GET | `/oauth/registered-clients/{gw_id}` | Get client for gateway | Required |
| DELETE | `/oauth/registered-clients/{id}` | Delete registered client | Admin |

---

## Observability (`/observability`)

| Method | Path | Summary | Auth |
|--------|------|---------|------|
| GET | `/observability/traces` | List traces (filtered) | `admin.system_config` |
| POST | `/observability/traces/query` | Advanced trace query | `admin.system_config` |
| GET | `/observability/traces/{trace_id}` | Get trace with spans | `admin.system_config` |
| GET | `/observability/spans` | List spans (filtered) | `admin.system_config` |
| DELETE | `/observability/traces/cleanup` | Delete old traces | `admin.system_config` |
| GET | `/observability/stats` | Get observability stats | `admin.system_config` |
| POST | `/observability/traces/export` | Export traces (JSON/CSV/NDJSON) | `admin.system_config` |
| GET | `/observability/analytics/query-performance` | Query perf analytics | `admin.system_config` |

---

## Log Search (`/api/logs`)

| Method | Path | Summary | Auth |
|--------|------|---------|------|
| POST | `/api/logs/search` | Search structured logs | `logs:read` |
| GET | `/api/logs/trace/{correlation_id}` | Get correlation trace | `logs:read` |
| GET | `/api/logs/security-events` | Get security events | `security:read` |
| GET | `/api/logs/audit-trails` | Get audit trails | `audit:read` |
| GET | `/api/logs/performance-metrics` | Get performance metrics | `metrics:read` |

---

## Metrics Maintenance (`/api/metrics`)

| Method | Path | Summary | Auth |
|--------|------|---------|------|
| POST | `/api/metrics/cleanup` | Manual metrics cleanup | Admin |
| POST | `/api/metrics/rollup` | Manual metrics rollup | Admin |
| GET | `/api/metrics/stats` | Get metrics stats | Admin |

---

## LLM Proxy & Configuration

### LLM Proxy
| Method | Path | Summary | Auth |
|--------|------|---------|------|
| POST | `/chat/completions` | OpenAI-compatible chat completions | Required |

### LLM Chat (`/llmchat`)
| Method | Path | Summary | Auth |
|--------|------|---------|------|
| POST | `/llmchat/chat/init` | Initialize LLM chat session | Required |
| POST | `/llmchat/chat/message` | Send message in chat | Required |

### LLM Configuration
| Method | Path | Summary | Auth |
|--------|------|---------|------|
| POST | `/providers` | Create LLM provider | `admin.system_config` |
| GET | `/providers` | List LLM providers | Required |
| GET | `/providers/{id}` | Get provider details | Required |
| PUT | `/providers/{id}` | Update LLM provider | `admin.system_config` |
| DELETE | `/providers/{id}` | Delete LLM provider | `admin.system_config` |
| POST | `/models` | Create LLM model | `admin.system_config` |
| GET | `/models` | List LLM models | Required |
| PUT | `/models/{id}` | Update LLM model | `admin.system_config` |
| DELETE | `/models/{id}` | Delete LLM model | `admin.system_config` |
| POST | `/providers/{id}/health-check` | Provider health check | Required |
| GET | `/models/gateway/available` | List gateway models | Required |

---

## Well-Known URIs

| Method | Path | Summary | Auth |
|--------|------|---------|------|
| GET | `/.well-known/oauth-protected-resource/{path}` | RFC 9728 OAuth metadata | None |
| GET | `/.well-known/{filename}` | Serve well-known files (robots.txt, security.txt, ai.txt) | None |
| GET | `/admin/well-known` | Get well-known status | Required |
| GET | `/{server_id}/.well-known/oauth-protected-resource` | DEPRECATED server OAuth metadata | None |

---

## Other Endpoints

| Method | Path | Summary | Auth |
|--------|------|---------|------|
| WebSocket | `/reverse-proxy/connect` | WebSocket reverse proxy | Required |
| POST | `/toolops/validation/generate_testcases` | Generate test cases | `admin.system_config` |
| POST | `/cancellation/cancel` | Cancel a run | `admin.system_config` |

---

## API Design Patterns

- **Pagination**: Cursor-based (teams, users) and offset/limit (logs, traces)
- **Filtering**: Time ranges, status codes, components, resource types
- **Export**: JSON, CSV, NDJSON streaming
- **Streaming**: SSE for long-running operations, WebSocket for bidirectional
- **Error Format**: Standard JSON with `detail` field and HTTP status codes
- **Versioning**: MCP protocol version negotiation via `mcp_version` field
