# Source Tree Analysis - MCP Context Forge

## Overview

Monorepo with 8 distinct parts, 120+ top-level entries (files + directories), spanning Python, Rust, Go, TypeScript, and infrastructure-as-code.

---

## Root Directory

```
mcp-context-forge/
├── mcpgateway/                 # [Part 1] Core FastAPI gateway application
├── plugins/                    # [Part 2] 45+ Python plugin implementations
├── plugins_rust/               # [Part 3] High-performance Rust plugins (PyO3)
├── mcp-servers/                # [Part 4] 28 MCP server implementations
├── a2a-agents/                 # [Part 5] Agent-to-Agent protocol implementations
├── charts/                     # [Part 6a] Helm charts for Kubernetes
├── deployment/                 # [Part 6b] Terraform, Ansible, K8s manifests
├── docs/                       # [Part 7] Mintlify documentation site
├── agent_runtimes/             # [Part 8] LangChain agent runtime
├── tests/                      # Test suite (22 subdirectories)
├── scripts/                    # Build, CI, and utility scripts
├── examples/                   # Deployment configuration examples
├── llms/                       # End-user LLM guidance (runtime docs)
├── build/                      # Build artifacts
├── infra/                      # Additional infrastructure configs
├── plugin_templates/           # Plugin scaffolding templates
├── tools_rust/                 # Rust tool implementations
├── .github/                    # CI/CD workflows (25+ workflow files)
│
├── pyproject.toml              # Python project config (uv/pip)
├── package.json                # JS tooling (Biome, Vitest)
├── Makefile                    # Build automation (60+ targets)
├── docker-compose.yml          # Primary compose stack
├── docker-compose.*.yml        # 7 compose variants (MariaDB, SSO, Phoenix, debug, etc.)
├── Containerfile               # Multi-stage production image
├── Containerfile.lite          # Minimal image variant
├── Containerfile.scratch       # Scratch-based image
├── gunicorn.config.py          # Gunicorn configuration
├── conftest.py                 # Root pytest configuration
├── tox.ini                     # Tox test runner config
├── vitest.config.js            # JS test configuration
├── biome.json                  # Biome linter/formatter config
├── fly.toml                    # Fly.io deployment
├── semgrep.yml                 # Semgrep security rules
├── .pylintrc                   # Pylint configuration
├── .pre-commit-config.yaml     # Pre-commit hooks (22K+ config)
│
├── README.md                   # Project documentation
├── CHANGELOG.md                # Release history
├── CONTRIBUTING.md             # Contribution guidelines
├── DEVELOPING.md               # Developer setup guide
├── TESTING.md                  # Testing guide
├── SECURITY.md                 # Security policy
├── CODE_OF_CONDUCT.md          # Code of conduct
├── AGENTS.md                   # AI assistant guidelines (→ CLAUDE.md)
├── LICENSE                     # Apache-2.0
└── DCO.txt                     # Developer Certificate of Origin
```

---

## Part 1: Gateway Core (`mcpgateway/`)

The main FastAPI application. 19 Python modules at root level, 17 subdirectories.

```
mcpgateway/
├── main.py                     # Application entry point, lifespan management
├── config.py                   # Pydantic Settings (200+ environment variables)
├── db.py                       # SQLAlchemy ORM models (50+ models)
├── schemas.py                  # Pydantic request/response schemas
├── auth.py                     # Authentication logic, normalize_token_teams()
├── admin.py                    # Admin UI routes (HTMX)
├── cli.py                      # CLI entry point (mcpgateway command)
├── version.py                  # Version constant
├── bootstrap_db.py             # Database initialization and migrations
├── observability.py            # OpenTelemetry integration
├── reverse_proxy.py            # WebSocket reverse proxy
├── translate.py                # stdio-to-HTTP MCP translation
├── translate_grpc.py           # gRPC-to-MCP translation
├── translate_header_utils.py   # Header handling utilities
├── wrapper.py                  # ASGI wrapper utilities
├── llm_provider_configs.py     # LLM provider configuration
├── llm_schemas.py              # LLM-specific schemas
├── cli_export_import.py        # Export/import CLI commands
│
├── routers/                    # 19 HTTP endpoint routers
│   ├── auth.py                 # /auth - Basic authentication
│   ├── email_auth.py           # /auth/email - Email-based auth
│   ├── sso.py                  # /auth/sso - SSO/OIDC providers
│   ├── teams.py                # /teams - Team management
│   ├── tokens.py               # /tokens - API token management
│   ├── rbac.py                 # /rbac - Role-based access control
│   ├── oauth_router.py         # /oauth - OAuth flows
│   ├── observability.py        # /observability - Trace/span queries
│   ├── log_search.py           # /api/logs - Structured log search
│   ├── metrics_maintenance.py  # /api/metrics - Metrics operations
│   ├── llm_proxy_router.py     # /chat/completions - OpenAI-compatible proxy
│   ├── llmchat_router.py       # /llmchat - LLM chat sessions
│   ├── llm_config_router.py    # LLM provider/model CRUD
│   ├── llm_admin_router.py     # LLM admin operations
│   ├── well_known.py           # /.well-known - RFC 9728 metadata
│   ├── server_well_known.py    # Per-server well-known (deprecated)
│   ├── reverse_proxy.py        # WebSocket proxy endpoint
│   ├── cancellation_router.py  # Run cancellation
│   └── toolops_router.py       # Tool operations
│
├── services/                   # 53 business logic services
│   ├── gateway_service.py      # Gateway CRUD and upstream management
│   ├── tool_service.py         # Tool discovery and execution
│   ├── resource_service.py     # Resource management
│   ├── prompt_service.py       # Prompt template management
│   ├── server_service.py       # Virtual server composition
│   ├── a2a_service.py          # A2A agent management
│   ├── oauth_manager.py        # Per-user OAuth token delegation
│   ├── email_auth_service.py   # Email auth with Argon2 hashing
│   ├── sso_service.py          # SSO provider management
│   ├── permission_service.py   # RBAC permission checks
│   ├── role_service.py         # Role management
│   ├── metrics.py              # Metrics recording
│   ├── metrics_buffer_service.py # Buffered metrics writes
│   ├── metrics_rollup_service.py # Hourly aggregation
│   ├── metrics_cleanup_service.py # Old metrics cleanup
│   ├── metrics_query_service.py # Metrics querying
│   ├── observability_service.py # Trace/span storage
│   ├── log_aggregator.py       # Log collection
│   ├── structured_logger.py    # Structured logging
│   ├── mcp_session_pool.py     # MCP connection pooling
│   ├── llm_proxy_service.py    # LLM provider proxy
│   ├── llm_provider_service.py # LLM provider CRUD
│   ├── encryption_service.py   # Secret encryption (Fernet)
│   ├── plugin_service.py       # Plugin lifecycle management
│   ├── catalog_service.py      # Tool/resource catalog
│   ├── export_service.py       # Data export
│   ├── import_service.py       # Data import
│   └── ... (25 more services)
│
├── middleware/                  # 15 middleware components
│   ├── auth_middleware.py       # JWT extraction and auth context
│   ├── token_scoping.py        # Team-based resource filtering
│   ├── rbac.py                 # Permission enforcement
│   ├── compression.py          # SSE-aware response compression
│   ├── correlation_id.py       # Request ID injection
│   ├── security_headers.py     # HSTS, CSP, X-Frame-Options
│   ├── request_logging_middleware.py # Request/response logging
│   ├── observability_middleware.py # OpenTelemetry instrumentation
│   ├── token_usage_middleware.py # Rate limiting tracking
│   ├── http_auth_middleware.py  # Plugin-based auth hooks
│   ├── protocol_version.py     # MCP protocol version validation
│   ├── validation_middleware.py # Input validation
│   ├── path_filter.py          # MCP path rewriting
│   ├── request_context.py      # Proxy header extraction
│   └── db_query_logging.py     # SQL query logging
│
├── transports/                 # 5 protocol implementations
│   ├── base.py                 # Abstract transport base class
│   ├── sse_transport.py        # Server-Sent Events
│   ├── websocket_transport.py  # WebSocket (RFC 6455)
│   ├── stdio_transport.py      # Standard I/O (CLI tools)
│   ├── streamablehttp_transport.py # Streamable HTTP (MCP spec)
│   └── redis_event_store.py    # Redis-backed event persistence
│
├── cache/                      # Cache layer implementations
├── common/                     # Shared utilities
├── handlers/                   # Request handlers
├── instrumentation/            # Observability instrumentation
├── plugins/                    # Plugin framework infrastructure
├── tools/                      # CLI tool implementations (cforge)
├── toolops/                    # Tool operations logic
├── utils/                      # Utility functions
├── validation/                 # Input validation logic
├── scripts/                    # Internal scripts
├── static/                     # Static assets (CSS, JS, images)
├── templates/                  # Jinja2 templates (Admin UI)
└── alembic/                    # Database migrations (69 migrations)
    └── versions/               # Migration files
```

---

## Part 2: Python Plugins (`plugins/`)

45+ plugins organized by category. Each plugin follows a standard structure with `__init__.py`, `README.md`, and optional `config.yaml`.

```
plugins/
├── AGENTS.md                   # Plugin development guidelines
├── config.yaml                 # Global plugin configuration
├── __init__.py                 # Plugin package init
│
├── # Security Plugins (11)
├── secrets_detection/          # Detect API keys, passwords in content
├── pii_filter/                 # PII detection and redaction
├── encoded_exfil_detector/     # Detect base64/hex exfiltration
├── sql_sanitizer/              # SQL injection prevention
├── content_moderation/         # Harmful content detection
├── harmful_content_detector/   # Additional content safety
├── code_safety_linter/         # Code security analysis
├── safe_html_sanitizer/        # HTML sanitization
├── virus_total_checker/        # VirusTotal integration
├── url_reputation/             # URL reputation checking
├── vault/                      # HashiCorp Vault integration
│
├── # Transformation Plugins (9)
├── json_repair/                # Fix malformed JSON
├── html_to_markdown/           # HTML-to-Markdown conversion
├── code_formatter/             # Code formatting
├── markdown_cleaner/           # Markdown normalization
├── argument_normalizer/        # Input normalization
├── ai_artifacts_normalizer/    # AI artifact processing
├── altk_json_processor/        # ALTK JSON handling
├── toon_encoder/               # Encoding utilities
├── timezone_translator/        # Timezone conversion
│
├── # Policy Plugins (8)
├── rate_limiter/               # Request rate limiting
├── output_length_guard/        # Response size limits
├── circuit_breaker/            # Circuit breaker pattern
├── schema_guard/               # Schema validation
├── robots_license_guard/       # Robots.txt compliance
├── deny_filter/                # Content deny-listing
├── regex_filter/               # Regex-based filtering
├── file_type_allowlist/        # File type restrictions
│
├── # Infrastructure Plugins (7)
├── cached_tool_result/         # Result caching
├── retry_with_backoff/         # Retry with exponential backoff
├── webhook_notification/       # Webhook delivery
├── tools_telemetry_exporter/   # Telemetry export
├── response_cache_by_prompt/   # Prompt-based caching
├── header_injector/            # HTTP header injection
├── resource_filter/            # Resource filtering
│
├── # Other Plugins (5)
├── citation_validator/         # Citation verification
├── jwt_claims_extraction/      # JWT claim parsing
├── license_header_injector/    # License header management
├── privacy_notice_injector/    # Privacy notice injection
├── summarizer/                 # Content summarization
│
├── # Plugin Infrastructure
├── unified_pdp/                # Unified Policy Decision Point
├── watchdog/                   # Plugin health monitoring
├── sparc_static_validator/     # SPARC validation
├── external/                   # External process plugins (Cedar, OPA, LLMGuard)
├── examples/                   # Plugin development examples
└── resources/                  # Shared plugin resources
```

---

## Part 3: Rust Plugins (`plugins_rust/`)

High-performance security plugins compiled via PyO3 for Python integration.

```
plugins_rust/
├── Cargo.toml                  # Workspace root (edition 2024, PyO3 0.28)
├── Cargo.lock                  # Dependency lockfile
├── pyproject.toml              # Python package config (maturin build)
├── Makefile                    # Build targets (develop, test, bench)
├── README.md                   # Rust plugins overview
├── QUICKSTART.md               # Getting started guide
│
├── src/                        # Shared library root
│   └── lib.rs                  # PyO3 module registration
│
├── pii_filter/                 # PII detection (regex-based)
│   └── src/lib.rs
├── secrets_detection/          # Secret detection (entropy + patterns)
│   └── src/lib.rs
└── encoded_exfil_detection/    # Exfiltration detection
    └── src/lib.rs
```

---

## Part 4: MCP Servers (`mcp-servers/`)

28 MCP server implementations across 3 languages + scaffolding tools.

```
mcp-servers/
├── AGENTS.md                   # MCP server development guidelines
├── scaffold-python-server.sh   # Python server generator
├── scaffold-go-server.sh       # Go server generator
│
├── python/                     # 20 Python MCP servers
│   ├── chunker_server/         # Document chunking
│   ├── code_splitter_server/   # Code splitting
│   ├── csv_pandas_chat_server/ # CSV analysis with pandas
│   ├── data_analysis_server/   # Data analysis tools
│   ├── docx_server/            # Word document processing
│   ├── graphviz_server/        # Graph visualization
│   ├── latex_server/           # LaTeX rendering
│   ├── libreoffice_server/     # LibreOffice integration
│   ├── mcp_eval_server/        # Evaluation server
│   ├── mcp-rss-search/         # RSS feed search
│   ├── mermaid_server/         # Mermaid diagram rendering
│   ├── output_schema_test_server/ # Schema testing
│   ├── plotly_server/          # Plotly chart generation
│   ├── pm_mcp_server/          # Project management
│   ├── pptx_server/            # PowerPoint generation
│   ├── python_sandbox_server/  # Sandboxed Python execution
│   ├── qr_code_server/         # QR code generation
│   ├── synthetic_data_server/  # Synthetic data generation
│   ├── url_to_markdown_server/ # URL-to-Markdown conversion
│   └── xlsx_server/            # Excel processing
│
├── go/                         # 6 Go MCP servers
│   ├── benchmark-server/       # Performance benchmarking
│   ├── calculator-server/      # Calculator tools
│   ├── fast-time-server/       # Low-latency time service
│   ├── pandoc-server/          # Pandoc document conversion
│   ├── slow-time-server/       # Simulated slow service
│   └── system-monitor-server/  # System metrics
│
├── rust/                       # 2 Rust MCP servers
│   ├── fast-test-server/       # Fast test harness
│   └── filesystem-server/      # File system operations
│
└── templates/                  # Cookiecutter templates
    ├── python/                 # Python server template
    └── go/                     # Go server template
```

---

## Part 5: A2A Agents (`a2a-agents/`)

Agent-to-Agent protocol implementations in Go.

```
a2a-agents/
└── go/
    └── a2a-echo-agent/         # Echo agent (Go 1.24, a2a-go SDK v0.3.7)
        ├── go.mod
        ├── go.sum
        ├── main.go
        └── README.md
```

---

## Part 6: Infrastructure

### Helm Charts (`charts/`)

```
charts/
├── AGENTS.md                   # Helm chart guidelines
├── README.md                   # Charts overview
└── mcp-stack/                  # Main Helm chart (v1.0.0-rc.1)
    ├── Chart.yaml              # Chart metadata (apiVersion v2)
    ├── Chart.lock              # Dependency lock
    ├── values.yaml             # Default values
    ├── templates/              # Kubernetes templates
    └── charts/                 # Bundled subcharts (PostgreSQL, Redis)
```

### Deployment (`deployment/`)

```
deployment/
├── AGENTS.md                   # Deployment guidelines
├── README.md                   # Deployment overview
├── CHARTS.md                   # Chart documentation
├── WORK_IN_PROGRESS            # WIP indicator
│
├── k8s/                        # Raw Kubernetes manifests
│   ├── mcp-context-forge-deployment.yaml
│   ├── mcp-context-forge-service.yaml
│   ├── mcp-context-forge-ingress.yaml
│   ├── postgres-*.yaml         # PostgreSQL resources (4 files)
│   └── redis-*.yaml            # Redis resources (2 files)
│
├── terraform/                  # Infrastructure as Code
│   └── ibm-cloud/              # IBM Cloud modules
│
├── ansible/                    # Ansible playbooks
└── knative/                    # Knative serverless configs
```

---

## Part 7: Documentation (`docs/`)

Mintlify-powered documentation site with 100+ pages.

```
docs/
├── docs/                       # Mintlify source
│   ├── architecture/           # Architecture decisions (40+ ADRs)
│   ├── deploy/                 # Deployment guides (AWS, Azure, OpenShift)
│   ├── develop/                # Development guides
│   ├── manage/                 # Management guides (RBAC, teams)
│   ├── using/                  # Usage guides (servers, tools)
│   └── tutorials/              # SSO tutorials (6 providers)
├── mint.json                   # Mintlify configuration
│
├── # Generated brownfield docs (this workflow)
├── project-overview.md
├── architecture.md
├── api-contracts-gateway-core.md
├── data-models-gateway-core.md
├── source-tree-analysis.md
├── development-guide.md
└── project-scan-report.json    # Workflow state file
```

---

## Part 8: Agent Runtimes (`agent_runtimes/`)

```
agent_runtimes/
└── langchain_agent/            # LangChain-based agent runtime
    ├── pyproject.toml          # Dependencies (multi-provider)
    ├── agent.py                # Agent implementation
    └── README.md
```

---

## Test Suite (`tests/`)

22 subdirectories covering comprehensive testing strategy.

```
tests/
├── unit/                       # Unit tests (pytest)
├── integration/                # Integration tests (pytest)
├── e2e/                        # End-to-end tests (pytest)
├── security/                   # Security tests (bandit)
├── fuzz/                       # Fuzz tests (hypothesis, atheris)
├── playwright/                 # UI tests (Playwright)
├── performance/                # Performance benchmarks
├── load/                       # Load tests (Locust)
├── loadtest/                   # Additional load tests
├── jmeter/                     # JMeter test plans
├── js/                         # JavaScript tests (Vitest)
├── async/                      # Async-specific tests
├── client/                     # Client SDK tests
├── compliance/                 # Protocol compliance tests
├── differential/               # Differential tests
├── migration/                  # Migration tests
├── manual/                     # Manual test scripts
├── hey/                        # HTTP load testing (hey tool)
├── helpers/                    # Test helpers/fixtures
├── utils/                      # Test utilities
└── populate/                   # Data population scripts
```

---

## CI/CD Workflows (`.github/workflows/`)

25+ GitHub Actions workflow files (some inactive).

| Workflow | Purpose |
|----------|---------|
| `pytest.yml` | Python test suite |
| `lint.yml` | Pylint + static analysis |
| `lint-web.yml` | Biome (JS/CSS) linting |
| `lint-plugins.yml` | Plugin linting |
| `vitest.yml` | JavaScript tests |
| `bandit.yml` | Security scanning |
| `codeql.yml` | CodeQL analysis |
| `docker-multiplatform.yml` | Multi-arch Docker builds |
| `docker-release.yml` | Release Docker images |
| `docker-scan.yml` | Container scanning |
| `full-build-pipeline.yml` | Complete CI pipeline |
| `playwright.yml` | UI test suite |
| `rust-plugins.yml` | Rust plugin CI |
| `rust-tools.yml` | Rust tool CI |
| `alembic-upgrade-validation.yml` | Migration validation |
| `dependency-review.yml` | Dependency auditing |
| `license-check.yml` | License compliance |

---

## Key Configuration Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Python project metadata, dependencies, tool configs |
| `package.json` | JS dependencies (Biome, Vitest, htmlhint) |
| `biome.json` | Biome linter/formatter configuration |
| `Makefile` | 60+ build/test/deploy targets |
| `.pylintrc` | Pylint configuration |
| `.pre-commit-config.yaml` | 22KB pre-commit hook config |
| `.env.example` | 121KB environment variable template |
| `tox.ini` | Tox test environments |
| `conftest.py` | Root pytest fixtures |
| `gunicorn.config.py` | Production server config |
| `.bumpversion.cfg` | Version bumping config |
