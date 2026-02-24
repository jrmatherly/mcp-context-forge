# MCP Context Forge - Documentation Index

## Project Documentation

Generated brownfield documentation for AI-assisted development.

### Core Documents

| Document | Description |
|----------|-------------|
| [Project Overview](project-overview.md) | Purpose, version info, technology stack, and project parts |
| [Architecture](architecture.md) | Gateway pattern, middleware pipeline, auth model, transports, caching |
| [Source Tree Analysis](source-tree-analysis.md) | Annotated directory tree for all 8 project parts |
| [Integration Architecture](integration-architecture.md) | Inter-part communication, data flows, build dependencies |

### Technical Reference

| Document | Description |
|----------|-------------|
| [API Contracts](api-contracts-gateway-core.md) | 150+ REST API endpoints across 19 routers |
| [Data Models](data-models-gateway-core.md) | 50+ SQLAlchemy ORM models across 10 functional areas |
| [Development Guide](development-guide.md) | Setup, commands, testing, deployment workflows |

### Metadata

| Document | Description |
|----------|-------------|
| [Project Parts](project-parts.json) | Machine-readable project structure metadata |
| [Scan Report](project-scan-report.json) | Documentation workflow state and findings |

---

## Existing Documentation

### Mintlify Documentation Site (`docs/docs/`)

The primary documentation site with 100+ pages:

- **Architecture** (`docs/docs/architecture/`) - 40+ Architecture Decision Records (ADRs)
- **Deployment** (`docs/docs/deploy/`) - AWS, Azure, OpenShift, ArgoCD, Helm guides
- **Development** (`docs/docs/develop/`) - Profiling, database optimization, plugins
- **Management** (`docs/docs/manage/`) - RBAC, teams, multi-tenancy
- **Usage** (`docs/docs/using/`) - MCP servers, tools, external integrations
- **Tutorials** (`docs/docs/tutorials/`) - 6 SSO provider tutorials

### Root-Level Documentation

| Document | Description |
|----------|-------------|
| [README.md](../README.md) | Project introduction and quick start |
| [CONTRIBUTING.md](../CONTRIBUTING.md) | Contribution guidelines |
| [DEVELOPING.md](../DEVELOPING.md) | Developer setup guide |
| [TESTING.md](../TESTING.md) | Testing strategy and commands |
| [CHANGELOG.md](../CHANGELOG.md) | Release history |
| [SECURITY.md](../SECURITY.md) | Security policy |
| [MIGRATION-0.7.0.md](../MIGRATION-0.7.0.md) | Breaking changes migration guide |
| [MULTIPLATFORM.md](../MULTIPLATFORM.md) | Multi-platform deployment |

### Agent Guidelines (AGENTS.md files)

| Location | Scope |
|----------|-------|
| Root `AGENTS.md` / `CLAUDE.md` | Project-wide coding guidelines |
| `tests/AGENTS.md` | Testing conventions |
| `plugins/AGENTS.md` | Plugin development |
| `charts/AGENTS.md` | Helm chart operations |
| `deployment/AGENTS.md` | Infrastructure and deployment |
| `docs/AGENTS.md` | Documentation authoring |
| `mcp-servers/AGENTS.md` | MCP server implementation |

### LLM Runtime Guidance (`llms/`)

End-user documentation for LLMs using the gateway at runtime (not for code agents):

| Document | Scope |
|----------|-------|
| `llms/mcpgateway.md` | Gateway usage |
| `llms/api.md` | API reference |
| `llms/plugins-llms.md` | Plugin usage |
| `llms/testing.md` | Testing guidance |
| `llms/helm.md` | Helm deployment |
| `llms/mcp-server-python.md` | Python MCP servers |
| `llms/mcp-server-go.md` | Go MCP servers |
