# Integration Architecture - MCP Context Forge

## Overview

MCP Context Forge is a monorepo with 8 interconnected parts. This document maps how these parts communicate, share data, and depend on each other.

---

## Part Dependency Map

```
                          ┌──────────────────┐
                          │  AI Clients       │
                          │  (Claude, GPT)    │
                          └────────┬─────────┘
                                   │
                    SSE / WebSocket / Streamable HTTP
                                   │
                          ┌────────▼─────────┐
                     ┌────┤  Gateway Core     ├────┐
                     │    │  (mcpgateway/)    │    │
                     │    │  FastAPI/ASGI     │    │
                     │    └──┬───┬───┬───┬───┘    │
                     │       │   │   │   │        │
              ┌──────┘  ┌────┘   │   └────┐  └──────┐
              │         │        │        │         │
              ▼         ▼        ▼        ▼         ▼
         ┌────────┐ ┌────────┐ ┌────┐ ┌────────┐ ┌────────┐
         │Python  │ │ Rust   │ │MCP │ │  A2A   │ │ Agent  │
         │Plugins │ │Plugins │ │Srvs│ │ Agents │ │Runtime │
         └────────┘ └────────┘ └────┘ └────────┘ └────────┘
              │         │                            │
              └────┬────┘                            │
                   ▼                                 ▼
            stevedore +                         LangChain
            PyO3 FFI                           multi-provider

         ┌─────────────────────────────────────────────┐
         │              Infrastructure                   │
         │  Helm Charts  │  Terraform  │  K8s Manifests │
         └─────────────────────────────────────────────┘
```

---

## Inter-Part Communication Patterns

### 1. Gateway Core <-> Python Plugins

**Mechanism**: Stevedore entry points (in-process Python loading)

| Aspect | Detail |
|--------|--------|
| Direction | Gateway calls plugins synchronously |
| Protocol | Python function calls via stevedore `ExtensionManager` |
| Configuration | `plugins/config.yaml` defines active plugins and their settings |
| Lifecycle | Loaded at startup via `plugin_service.py`, hot-reload not supported |
| Data Flow | `plugin_chain_pre` runs before tool execution, `plugin_chain_post` runs after |
| Error Handling | Plugin exceptions caught by gateway, logged, and optionally bypass |

**Key files**:
- `mcpgateway/services/plugin_service.py` - Plugin lifecycle management
- `mcpgateway/plugins/` - Plugin framework infrastructure
- `plugins/config.yaml` - Plugin configuration
- `pyproject.toml` `[project.entry-points."mcpgateway.plugins"]` - Entry point registration

### 2. Gateway Core <-> Rust Plugins

**Mechanism**: PyO3 FFI bridge (compiled Rust loaded as Python modules)

| Aspect | Detail |
|--------|--------|
| Direction | Gateway calls Rust functions as if they were Python |
| Protocol | PyO3 `#[pyfunction]` exported to Python |
| Build | Maturin builds `.so`/`.dylib` from Cargo workspace |
| Performance | 10-100x faster than equivalent Python for CPU-bound operations |
| Registration | Same stevedore entry points as Python plugins |

**Key files**:
- `plugins_rust/Cargo.toml` - Workspace root
- `plugins_rust/src/lib.rs` - PyO3 module registration
- `plugins_rust/pii_filter/` - PII detection (Rust)
- `plugins_rust/secrets_detection/` - Secret detection (Rust)
- `plugins_rust/encoded_exfil_detection/` - Exfiltration detection (Rust)

### 3. Gateway Core <-> MCP Servers

**Mechanism**: HTTP/SSE, WebSocket, or stdio over network or subprocess

| Aspect | Detail |
|--------|--------|
| Direction | Gateway proxies client requests to upstream MCP servers |
| Protocol | JSON-RPC 2.0 over SSE, WebSocket, or stdio |
| Registration | `POST /gateways` registers an upstream MCP server |
| Discovery | Gateway auto-discovers tools, resources, prompts from registered servers |
| Modes | `cache` (store locally) or `direct_proxy` (pass-through) |
| Auth | Per-gateway auth: `basic`, `bearer`, `headers`, `oauth`, `query_param` |
| Translation | `mcpgateway/translate.py` converts stdio servers to HTTP/SSE |

**Key files**:
- `mcpgateway/services/gateway_service.py` - Upstream server management
- `mcpgateway/transports/` - Transport protocol implementations
- `mcpgateway/translate.py` - stdio-to-HTTP translation proxy
- `mcp-servers/python/` - 20 Python MCP server implementations
- `mcp-servers/go/` - 6 Go MCP server implementations
- `mcp-servers/rust/` - 2 Rust MCP server implementations

### 4. Gateway Core <-> A2A Agents

**Mechanism**: HTTP REST (Agent-to-Agent protocol)

| Aspect | Detail |
|--------|--------|
| Direction | Gateway invokes A2A agents as tool calls |
| Protocol | A2A protocol over HTTP REST |
| Registration | A2A agents registered via `/a2a_agents` endpoints |
| Integration | Each A2A agent gets a corresponding MCP tool for client access |
| Feature Flag | `MCPGATEWAY_A2A_ENABLED=true` |

**Key files**:
- `mcpgateway/services/a2a_service.py` - A2A agent management
- `mcpgateway/db.py` `A2AAgent` model - Database model
- `a2a-agents/go/a2a-echo-agent/` - Reference implementation

### 5. Gateway Core <-> Agent Runtimes

**Mechanism**: Python library integration

| Aspect | Detail |
|--------|--------|
| Direction | Agent runtime uses gateway as MCP tool provider |
| Protocol | Python SDK calls + MCP protocol |
| Providers | OpenAI, Azure OpenAI, Anthropic, Bedrock, Ollama |
| Framework | LangChain with multi-provider support |

**Key files**:
- `agent_runtimes/langchain_agent/pyproject.toml` - Dependencies
- `agent_runtimes/langchain_agent/agent.py` - Agent implementation

### 6. Gateway Core <-> Infrastructure

**Mechanism**: Configuration files and container orchestration

| Aspect | Detail |
|--------|--------|
| Helm Chart | `mcp-stack` bundles gateway + PostgreSQL + Redis |
| K8s Manifests | Raw manifests for manual deployment |
| Terraform | IBM Cloud modules (VPC, K8s, databases) |
| Container | Multi-stage builds (Containerfile, Containerfile.lite) |
| Docker Compose | 7 compose variants for different environments |

**Key files**:
- `charts/mcp-stack/` - Helm chart with values.yaml
- `deployment/k8s/` - Kubernetes manifests
- `deployment/terraform/ibm-cloud/` - Terraform modules
- `docker-compose.yml` - Primary compose stack
- `Containerfile` - Production container image

### 7. Gateway Core <-> Documentation

**Mechanism**: Documentation references code; ADRs guide development

| Aspect | Detail |
|--------|--------|
| Platform | Mintlify documentation site |
| ADRs | 40+ Architecture Decision Records |
| Guides | Deployment, SSO, development, management |
| Generated | Brownfield docs (this workflow), API docs, coverage reports |

**Key files**:
- `docs/docs/architecture/` - ADRs and architecture docs
- `docs/mint.json` - Mintlify site configuration

---

## Shared Data Flows

### Tool Execution Flow

```
Client Request
    │
    ▼
Gateway (auth + scoping middleware)
    │
    ▼
Plugin Chain Pre (Python/Rust plugins)
    │
    ▼
Tool Resolution (tool_service.py)
    │
    ├── MCP Server Tool → Transport (SSE/WS/stdio) → Upstream Server
    ├── REST Tool → HTTP Client → External API
    ├── A2A Tool → HTTP → A2A Agent
    └── gRPC Tool → gRPC Client → gRPC Service
    │
    ▼
Plugin Chain Post (Python/Rust plugins)
    │
    ▼
Metrics Recording + Response
```

### Authentication Flow

```
Client (JWT/API Token)
    │
    ▼
Plugin Auth Hook (optional, mcpgateway/middleware/http_auth_middleware.py)
    │
    ▼
JWT Validation (mcpgateway/auth.py)
    │
    ▼
API Token Fallback (SHA256 hash lookup)
    │
    ▼
User Resolution (email_users table)
    │
    ▼
Team Scoping (normalize_token_teams → resource visibility)
    │
    ▼
RBAC Check (permission_service.py → action permissions)
```

### Federation Flow

```
Gateway Instance A                Gateway Instance B
    │                                    │
    ▼                                    ▼
Export Service ──── JSON/NDJSON ────► Import Service
    │                                    │
    ▼                                    ▼
Redis Pub/Sub ◄────────────────────► Redis Pub/Sub
(cache invalidation)              (cache invalidation)
```

---

## Build Dependencies

### Build Order (from leaves to root)

1. **Rust Plugins** (`make rust-dev`) - No dependencies on other parts
2. **Python Plugins** - Depend on gateway schemas for type definitions
3. **MCP Servers** - Independent, each has own build/run cycle
4. **A2A Agents** - Independent Go modules
5. **Agent Runtimes** - Depend on gateway being running for MCP access
6. **Gateway Core** (`make install-dev`) - Depends on Python plugins and optionally Rust plugins
7. **Infrastructure** - Depends on container image built from gateway

### Test Dependencies

| Test Type | Requirements |
|-----------|-------------|
| Unit tests | Gateway + plugins installed |
| Integration tests | Running gateway instance |
| E2E tests | Full stack (gateway + database + optional Redis) |
| Playwright tests | Running gateway with UI enabled |
| Load tests | Locust + running gateway |
| Migration tests | Docker (PostgreSQL container) |
| Rust tests | Rust toolchain + maturin |
| JS tests | Node.js + npm packages |

---

## Configuration Propagation

Environment variables flow from deployment configuration to the gateway:

```
.env / env vars / ConfigMaps / Secrets
    │
    ▼
mcpgateway/config.py (Pydantic Settings)
    │
    ├── Database: DATABASE_URL → db.py → SQLAlchemy engine
    ├── Redis: REDIS_URL → cache layers, session registry
    ├── Auth: JWT_SECRET_KEY → auth.py → JWT validation
    ├── Plugins: PLUGIN_CONFIG_FILE → plugin_service.py → stevedore
    ├── Transport: TRANSPORT_TYPE → transports/ → protocol selection
    └── Features: Feature flags → conditional initialization in main.py
```

---

## Cross-Part Version Alignment

| Component | Version Format | Location |
|-----------|---------------|----------|
| Gateway (Python) | `1.0.0rc1` (PEP 440) | `pyproject.toml`, `mcpgateway/__init__.py` |
| Rust Plugins | `1.0.0-rc.1` (SemVer) | `plugins_rust/Cargo.toml` |
| Helm Chart | `1.0.0-rc.1` (SemVer) | `charts/mcp-stack/Chart.yaml` |
| Chart appVersion | `1.0.0rc1` | `charts/mcp-stack/Chart.yaml` |

Version bumps are managed by `.bumpversion.cfg` for Python, manual for Rust and Helm.
