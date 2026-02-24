# Development Guide - MCP Context Forge

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | >=3.11, <3.14 | Core language |
| uv | Latest | Virtual environment and package management |
| Node.js | >=18 | JS tooling (Biome, Vitest) |
| Rust | Edition 2024 | Rust plugins (optional, `ENABLE_RUST_BUILD=1`) |
| Go | >=1.24 | Go MCP servers (optional) |
| Docker/Podman | Latest | Container builds |
| Make | GNU Make | Build automation |

## Quick Start

```bash
# 1. Clone and setup
git clone <repo-url> mcp-context-forge
cd mcp-context-forge
cp .env.example .env

# 2. Create virtual environment and install
make venv install-dev

# 3. Verify environment
make check-env

# 4. Start development server
make dev              # Dev server on :8000 with autoreload
```

### Production Server

```bash
make serve            # Gunicorn on :4444
make certs && make serve-ssl   # HTTPS on :4444
make serve-granian    # Granian (Rust-based alternative)
```

## Environment Configuration

The `.env.example` file (121KB) documents all 200+ environment variables. Key categories:

| Category | Key Variables | Notes |
|----------|--------------|-------|
| Core | `HOST`, `PORT`, `DATABASE_URL`, `REDIS_URL` | Default SQLite, optional PostgreSQL/Redis |
| Auth | `JWT_SECRET_KEY`, `AUTH_REQUIRED`, `BASIC_AUTH_USER` | Set `AUTH_REQUIRED=false` for dev |
| Features | `MCPGATEWAY_UI_ENABLED`, `PLUGINS_ENABLED`, `MCPGATEWAY_A2A_ENABLED` | Feature flags |
| Logging | `LOG_LEVEL`, `STRUCTURED_LOGGING_DATABASE_ENABLED` | `INFO` default |
| Observability | `OBSERVABILITY_ENABLED`, `OTEL_EXPORTER_OTLP_ENDPOINT` | Optional OpenTelemetry |

## Code Quality Workflow

### After Writing Code

```bash
make autoflake        # Remove unused imports
make isort            # Sort imports (profile=black)
make black            # Format code (line-length=200)
make pre-commit       # Run all pre-commit hooks
```

### Before Committing

```bash
# Type checking on new/changed files
ty check mcpgateway/your_file.py
mypy mcpgateway/your_file.py

# Full linting suite
make flake8           # Flake8 checks
make bandit           # Security scanning
make interrogate      # Docstring coverage
make pylint           # Pylint (config in .pylintrc)
make verify           # Combined verification
```

### JavaScript/CSS

```bash
npx biome check .     # Lint and format check
npx biome check --write .  # Auto-fix
npx vitest            # Run JS tests
```

## Testing

### Primary Test Commands

```bash
make test             # Run unit tests
make test-verbose     # Verbose output
make coverage         # Run with coverage report
make htmlcov          # Generate HTML coverage report
```

### Specialized Testing

| Command | Purpose |
|---------|---------|
| `make test-db-perf` | Database performance + N+1 detection |
| `make fuzz-quick` | Quick fuzzing for CI |
| `make fuzz-all` | Complete fuzzing suite |
| `make migration-test-all` | Migration tests (SQLite + PostgreSQL) |
| `npx vitest` | JavaScript tests |

### Load Testing

```bash
make generate-small     # Generate small dataset (100 users)
make populate-small     # Populate via REST API
make testing-up         # Start testing stack (Locust + services)
make testing-down       # Stop testing stack
```

### Playwright UI Tests

```bash
make monitoring-up      # Start monitoring stack
python -m playwright install  # Install browsers
pytest tests/playwright/
```

## Database Operations

### Alembic Migrations

```bash
cd mcpgateway

# Check current state
alembic heads           # ALWAYS check first
alembic current         # Show current revision

# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
alembic downgrade -1    # Rollback one step
```

### Migration Requirements

1. `down_revision` must point to the current head (verify with `alembic heads`)
2. Write idempotent migrations that check before modifying
3. Verify single head after creation
4. See CLAUDE.md for the full idempotent migration pattern

### Database Backends

| Backend | Connection | Use Case |
|---------|-----------|----------|
| SQLite | `sqlite:///./mcp.db` | Development (default) |
| PostgreSQL | `postgresql+psycopg://...` | Production |
| MariaDB | `mysql+pymysql://...` | Alternative production |

## Docker Operations

### Building Images

```bash
docker build -f Containerfile -t mcpgateway .        # Full image
docker build -f Containerfile.lite -t mcpgateway:lite .  # Minimal image
```

### Docker Compose Stacks

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Primary stack (gateway + PostgreSQL + Redis) |
| `docker-compose.with-phoenix.yml` | + Phoenix observability |
| `docker-compose.sso.yml` | + SSO test providers |
| `docker-compose.mariadb.yml` | MariaDB instead of PostgreSQL |
| `docker-compose-debug.yml` | Debug configuration |
| `docker-compose-performance.yml` | Performance testing stack |

## Rust Plugin Development

```bash
# Enable Rust builds
export ENABLE_RUST_BUILD=1

# Development workflow
make rust-dev           # Build and install (dev mode)
make rust-test          # Run Rust tests
make rust-bench         # Run benchmarks
make rust-check         # Format + lint + test

# Cross-compilation
make rust-cross         # Build for all Linux architectures
```

## MCP Server Development

### Python Servers

```bash
# Scaffold new server
./mcp-servers/scaffold-python-server.sh my-server

# Run via translation proxy
python -m mcpgateway.translate --stdio "python -m my_server" --port 9000
```

### Go Servers

```bash
# Scaffold new server
./mcp-servers/scaffold-go-server.sh my-server

# Build and run
cd mcp-servers/go/my-server && go build && ./my-server
```

## Security Scanning

```bash
make bandit             # Python security scanning
make gitleaks           # Secret detection in git history
make devskim            # DevSkim security patterns
make snyk-all           # All Snyk scans (requires auth)
make security-report    # Comprehensive security report
```

## Certificate Management

```bash
make certs              # TLS cert + key (self-signed)
make certs-jwt          # JWT RSA keys
make certs-jwt-ecdsa    # JWT ECDSA keys
make certs-all          # All certificates
make certs-mcp-all      # mTLS infrastructure for plugins
```

## CLI Tools

### Gateway CLI (`mcpgateway`)

```bash
mcpgateway              # Start the gateway
```

### Context Forge CLI (`cforge`)

```bash
cforge                  # Context Forge operations
```

### Plugin CLI (`mcpplugins`)

```bash
mcpplugins              # Plugin management
```

### JWT Token Generation

```bash
python -m mcpgateway.utils.create_jwt_token \
  --username admin@example.com \
  --exp 10080 \
  --secret YOUR_SECRET

# Export for API calls
export MCPGATEWAY_BEARER_TOKEN=$(python -m mcpgateway.utils.create_jwt_token \
  --username admin@example.com --exp 0 --secret KEY)
```

## Monitoring and Observability

```bash
make monitoring-up      # Prometheus + Grafana + exporters
make monitoring-status  # Check monitoring services
make monitoring-logs    # View monitoring logs
make monitoring-down    # Stop monitoring

make inspector-up       # MCP Inspector (interactive client)
make inspector-down     # Stop inspector
```

## Commit Standards

- **Sign commits**: `git commit -s` (DCO requirement)
- **Conventional Commits**: `feat:`, `fix:`, `docs:`, `refactor:`, `chore:`
- **Link issues**: `Closes #123`
- Include tests for behavior changes
- Require green lint and tests before PR

## Project Entry Points

| Entry Point | Command | Description |
|-------------|---------|-------------|
| `mcpgateway.main:app` | - | FastAPI application |
| `mcpgateway.cli:main` | `mcpgateway` | CLI tool |
| `mcpgateway.plugins.tools.cli:main` | `mcpplugins` | Plugin CLI |
| `mcpgateway.tools.cli:main` | `cforge` | Context Forge CLI |
