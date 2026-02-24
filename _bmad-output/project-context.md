---
project_name: 'mcp-context-forge'
user_name: 'Jason'
date: '2026-02-23'
sections_completed: ['technology_stack', 'language_rules', 'framework_rules', 'testing_rules', 'code_quality', 'workflow_rules', 'critical_rules']
status: 'complete'
rule_count: 75
optimized_for_llm: true
---

# Project Context for AI Agents

_This file contains critical rules and patterns that AI agents must follow when implementing code in this project. Focus on unobvious details that agents might otherwise miss._

---

## Technology Stack & Versions

### Core Application
- **Python** >= 3.11, < 3.14 (target: 3.11 for type checking and linting)
- **FastAPI** >= 0.129.0 (Starlette ASGI underneath)
- **Pydantic** >= 2.12.5 (with email extras; mypy plugin enabled)
- **SQLAlchemy** >= 2.0.46 (ORM with both sync and async support)
- **Alembic** >= 1.18.4 (database migrations)
- **PyJWT** >= 2.11.0 (JWT authentication)
- **httpx** >= 0.28.1 (with HTTP/2 support)
- **MCP SDK** >= 1.26.0 (Model Context Protocol)

### Databases & Caching
- **SQLite** (default, file-based or in-memory for tests)
- **PostgreSQL** via psycopg3 (production)
- **Redis** >= 7.2.0 (caching, federation, session store; optional hiredis for performance)

### Admin UI (server-rendered, no SPA)
- **Jinja2** >= 3.1.6 (HTML templates)
- **HTMX** (dynamic partials via `hx-*` attributes)
- **Alpine.js** (lightweight reactive state)
- **Bootstrap** (CSS framework)
- **Chart.js** (data visualization)
- **Ace Editor** (code editing in admin panels)

### Rust Plugins
- 3 security plugins in `plugins_rust/`: `encoded_exfil_detection`, `pii_filter`, `secrets_detection`

### Frontend Tooling (JS/CSS)
- **Biome** >= 2.4.4 (linting + formatting, replaced ESLint/Prettier/Stylelint)
- **Vitest** >= 4.0.18 (JS test runner with Istanbul coverage)
- **HTMLHint** >= 1.9.1

### Python Tooling
- **Black** (formatter, line-length 200)
- **isort** (import sorter, profile=black)
- **Ruff** >= 0.13.3 (fast linter: E3/E4/E7/E9/F/D1 rules)
- **Flake8**, **Pylint** (with pylint-pydantic plugin), **Bandit** (security)
- **mypy** (strict mode, pydantic plugin), **pyrefly**, **pyright**
- **interrogate** (docstring coverage, fail-under=100%)
- **pytest** (asyncio_mode=auto, in-memory SQLite for tests)

### Infrastructure
- **Helm chart**: `mcp-stack` v1.0.0-rc.1 (appVersion: 1.0.0rc1)
- **Kubernetes** >= 1.21
- **Docker/OCI** multi-platform builds with Cosign signing
- **GitHub Actions** CI/CD (19 workflow files)

### Version String Convention
- Python/PEP 440: `1.0.0rc1` (no hyphens, lowercase)
- Helm/SemVer: `1.0.0-rc.1` (hyphen + dot-separated)
- bump2version manages: `pyproject.toml`, `__init__.py`, `Containerfile`, `Containerfile.lite`

## Critical Implementation Rules

### Language-Specific Rules (Python)

- **Type hints required on all functions** -- mypy strict mode is enabled with `disallow_untyped_defs`, `disallow_untyped_calls`, `no_implicit_optional`
- **Explicit `Optional[]`** -- never rely on implicit `None` defaults; write `Optional[str] = None` not `str = None`
- **Pydantic v2 models** -- use `model_validator`, `field_validator` (not deprecated v1 `@validator`); mypy plugin is active via `plugins = ["pydantic.mypy"]`
- **Async-first** -- FastAPI routes and service methods are async; use `httpx.AsyncClient` not `requests`; `pytest.mark.asyncio` with `asyncio_mode = "auto"` (no need to mark every test)
- **Import ordering** -- isort profile=black with `from_first = true` (all `from X import Y` before plain `import X`); known first-party: `mcpgateway`; known third-party: `alembic`; skip `__init__.py` files
- **Line length 200** -- Black, Ruff, Pylint, and isort all enforce 200-char lines
- **Docstrings on everything in `mcpgateway/`** -- interrogate enforces 100% coverage; `no-docstring-rgx=^_` exempts private methods in Pylint
- **Ruff rules** -- `E3, E4, E7, E9, F, D1` are enabled; `D1` (docstring checks) disabled for `tests/`, `scripts/`, `mcp-servers/`
- **Logging uses `%` formatting** -- `.pylintrc` sets `logging-format-style=old`; use `logger.info("msg %s", val)` not f-strings
- **orjson for JSON** -- `orjson` is an allowed C extension in both Pylint and mypy; prefer it over stdlib `json` for performance
- **SQLAlchemy generated members** -- Pylint allows `sqlalchemy.func.*` via `generated-members` to prevent false E1101 errors
- **Exception handling** -- `broad-exception-caught` and `broad-exception-raised` are disabled in Pylint, but Bandit still checks security; use specific exception types where possible
- **Never use `typing.Any` from unimported modules** -- `disallow_any_unimported = true` in mypy

### Framework-Specific Rules (FastAPI)

- **Service layer pattern** -- business logic lives in `mcpgateway/services/` (55+ services); routers in `mcpgateway/routers/` are thin HTTP handlers that delegate to services
- **Middleware pipeline order matters** -- 17 middleware layers execute in reverse registration order; new middleware must be inserted at the correct position (see `mcpgateway/main.py`)
- **Transport abstraction** -- all transports (SSE, WebSocket, stdio, Streamable HTTP) extend the abstract `Transport` base class in `mcpgateway/transports/base.py` with `connect/disconnect/send_message/receive_message`
- **JSON-RPC 2.0 messaging** -- all MCP communication uses JSON-RPC 2.0 envelope with `method/params/id` structure
- **Two-layer security model** -- Layer 1 (Token Scoping) controls what resources users CAN SEE; Layer 2 (RBAC) controls what actions users CAN DO; these are independent and both must be considered
- **`normalize_token_teams()` in `mcpgateway/auth.py`** is the single source of truth for team scoping; missing `teams` key = empty array (public-only); admin bypass requires BOTH `teams: null` AND `is_admin: true`
- **Plugin framework** -- Python plugins in `plugins/` with `config.yaml` manifest; Rust plugins in `plugins_rust/`; plugin hooks can inject custom auth, content filtering, and tool processing
- **Alembic migrations are idempotent** -- always check `inspector.get_table_names()` and `inspector.get_columns()` before modifying; fresh DBs use `db.py` models directly, not migrations
- **Alembic single-head rule** -- always run `cd mcpgateway && alembic heads` before creating a migration; `down_revision` MUST point to the actual current head; multiple heads break all tests
- **Database models in `mcpgateway/db.py`** -- SQLAlchemy ORM models and session management are co-located; `SessionLocal` is a valid name (added to Pylint `good-names`)

### Admin UI Rules (HTMX + Alpine.js)

- **Server-rendered partials** -- admin UI uses Jinja2 templates returning HTML fragments; HTMX swaps partials via `hx-get`, `hx-post`, `hx-target`, `hx-swap`
- **Alpine.js for client state** -- use `x-data`, `x-show`, `x-bind` for reactive UI; no React/Vue/Angular
- **Biome for JS/CSS** -- all `mcpgateway/static/**/*.js` and `mcpgateway/static/**/*.css` are linted/formatted by Biome; globals declared: `Alpine`, `htmx`, `bootstrap`, `Chart`, `ace`, `showToast`, `showConfirmDialog`, `fetchWithAuth`
- **JS style** -- semicolons always, double quotes, trailing commas, 2-space indent, 120-char line width (per `biome.json`)
- **CSS style** -- 4-space indent, 120-char line width (per `biome.json`)
- **No global code evaluation** -- `noGlobalEval: "error"` in Biome (relaxed only in `tests/`)

### Testing Rules

- **Test directory mirrors source** -- `tests/unit/mcpgateway/` mirrors `mcpgateway/` structure; 14 test categories: `unit/`, `integration/`, `e2e/`, `performance/`, `playwright/`, `security/`, `fuzz/`, `load/`, `loadtest/`, `jmeter/`, `client/`, `async/`, `migration/`, `differential/`
- **File naming** -- test files: `test_*.py`; classes: `Test*`; functions: `test_*`; pre-commit enforces `name-tests-test` with `--pytest-test-first`
- **Async tests auto-detected** -- `asyncio_mode = "auto"` in `pyproject.toml`; no need for `@pytest.mark.asyncio` on every test
- **In-memory SQLite for tests** -- `DATABASE_URL=sqlite:///:memory:` and `TEST_DATABASE_URL=sqlite:///:memory:` set via `pytest-env`
- **Test environment variables** -- `MCPGATEWAY_ADMIN_API_ENABLED=true` and `MCPGATEWAY_UI_ENABLED=true` are auto-set for all tests
- **Default test run excludes** -- `--ignore=tests/playwright --ignore=tests/migration --ignore=tests/performance --ignore=tests/compliance` in `addopts`
- **Markers for categorization** -- `slow`, `ui`, `api`, `smoke`, `e2e`, `fuzz`, `benchmark`, `integration`, `postgresql`, plus MCP compliance markers (`mcp_core`, `mcp_required`, etc.)
- **Mocking pattern** -- use `unittest.mock.AsyncMock` and `patch("mcpgateway.services.xxx")` for service-layer mocks; prefer pure unit tests with mocked persistence
- **Coverage config** -- source: `mcpgateway/`; omits `alembic/`, `tools/builder/`, protobuf `*_pb2*.py`; excludes `pragma: no cover`, `TYPE_CHECKING`, `NotImplementedError`
- **JS tests with Vitest** -- `vitest run` for single pass; `vitest --coverage` for Istanbul coverage; `jsdom` environment for DOM testing
- **No network calls in unit tests** -- avoid real credentials and external API calls; use mocks and fixtures
- **PR readiness check** -- `make doctest test htmlcov smoketest lint-web flake8 bandit interrogate pylint verify`

### Code Quality & Style Rules

- **Pylint config gotcha** -- `.pylintrc` file at project root takes precedence over `[tool.pylint]` in `pyproject.toml`; always edit `.pylintrc` for Pylint settings, not `pyproject.toml`
- **Pylint good-names** -- `OTEL_AVAILABLE` and `SessionLocal` are explicitly allowed in `.pylintrc`; underscore-prefixed module-level singletons match `good-names-rgxs=^_[a-z][a-z0-9_]*$`
- **Pylint design limits** -- `max-args=12`, `max-positional-arguments=16`, `max-attributes=30`, `max-locals=15`, `max-statements=50`, `max-nested-blocks=18`
- **Pylint disabled checks** -- `too-many-locals`, `too-many-arguments`, `import-error`, `logging-fstring-interpolation`, `broad-exception-caught`, `broad-exception-raised`, `too-few-public-methods`, `line-too-long`, `too-many-lines`, `too-many-branches`, `too-many-statements`, `too-many-public-methods`, `unsubscriptable-object`
- **Naming conventions** -- `snake_case` for functions/methods/variables/modules; `PascalCase` for classes; `UPPER_CASE` for constants and class constants; `any` style for class attributes and inline vars
- **Similarity detection** -- Pylint `min-similarity-lines=16`; ignores comments, docstrings, imports, and signatures
- **Pre-commit AI artifact blocking** -- commits are rejected if they contain: `:contentReference`, `[oaicite:??digits]`, AI stock phrases ("as an AI language model", etc.), placeholder citations like `(Author, 2023)`, `(Source:...)`, or code fences with 4+ backticks
- **Pre-commit formatting** -- automatic: end-of-file fixer, trailing whitespace trim, UTF-8 BOM removal, LF line endings, smart quote normalization, ligature replacement, Unicode space normalization, BiDi control character blocking
- **Pre-commit Python** -- Black formatter, Ruff linter (with `--fix` on `mcpgateway/` only), Flake8, interrogate (100% docstring coverage on `mcpgateway/`)
- **Secret detection** -- Gitleaks and `detect-private-key` hooks run on every commit; never commit `.env`, credentials, or API keys
- **File organization** -- routers are thin HTTP handlers; services contain business logic; middleware for cross-cutting concerns; schemas for Pydantic models; `db.py` for ORM models
- **Documentation patterns** -- external server docs go in `docs/docs/using/servers/external/{vendor}/{server}.md`; follow heading pattern from `github.md`; no emojis in docs; `.pages` files control nav ordering

### Development Workflow Rules

- **Signed commits required** -- `git commit -s` (DCO requirement); all commits must include `Signed-off-by:` line
- **Conventional Commits** -- prefixes: `feat:`, `fix:`, `docs:`, `refactor:`, `chore:`; link issues with `Closes #123`
- **Never mention AI assistants** -- no references to AI, ChatGPT, Claude, etc. in PRs, diffs, or committed code; pre-commit hooks actively block AI stock phrases
- **No test plans or effort estimates in PRs** -- keep PR descriptions focused on what changed and why
- **Don't push until asked** -- for external contributors, check `todo/force-push.md` before pushing to contributor branches
- **Code quality before commit** -- run `make autoflake isort black pre-commit` after writing code; run `make flake8 bandit interrogate pylint verify` before committing
- **Type checking on new files** -- use `ty`, `mypy`, and `pyrefly` to check just the new/modified files before running full suite
- **CI workflow matrix** -- 19 GitHub Actions workflows covering: pytest, vitest, lint (Python + web + plugins), Playwright, CodeQL, Bandit, dependency review, license check, Docker builds (multi-platform + scan + release), Rust plugins, Rust tools, Alembic upgrade validation, full build pipeline
- **Alembic verification** -- after creating a migration, run `cd mcpgateway && alembic heads` to confirm single head; run `make test` to confirm migrations work
- **Makefile is the build system** -- use `make` targets for all operations: `make dev` (dev server), `make serve` (production), `make test`, `make coverage`, `make smoketest`, etc.
- **Environment setup** -- `cp .env.example .env && make venv install-dev check-env` for complete setup; `uv` manages virtual environments
- **Never create files unless necessary** -- prefer editing existing files; never proactively create documentation files unless explicitly requested

### Critical Don't-Miss Rules

**Anti-Patterns to Avoid:**
- **Never add Pylint config to `pyproject.toml`** -- `.pylintrc` is the authoritative config file; `pyproject.toml` Pylint sections are ignored when `.pylintrc` exists
- **Never create Alembic migrations without checking current head** -- `cd mcpgateway && alembic heads` FIRST; wrong `down_revision` creates multiple heads and breaks the entire test suite
- **Never use f-strings in logging calls** -- Pylint `logging-format-style=old` requires `%` formatting: `logger.info("value: %s", val)`
- **Never use `requests` library** -- the project uses `httpx` with async support; `requests` is not a dependency
- **Never use Pydantic v1 API** -- no `@validator`, no `class Config:`; use `@field_validator`, `@model_validator`, `model_config = ConfigDict(...)`
- **Never skip `--no-verify` on commits** -- pre-commit hooks enforce critical security and quality gates
- **Never commit secrets** -- Gitleaks + detect-private-key hooks will block; use `.env` for all credentials

**Security Rules:**
- **SSRF protection** -- the gateway has built-in SSRF protection with blocked networks and DNS fail-closed; respect these when adding new HTTP endpoints
- **OAuth per-user delegation** -- `oauth_tokens` table is keyed by `(gateway_id, app_user_email)`; never use `get_any_valid_token()` (deliberately removed as security vulnerability)
- **Auth required by default** -- `AUTH_REQUIRED=true` in production; only set `false` for local development
- **Password policies** -- reuse prevention, max age enforcement, account lockout protection are all enforced; don't bypass these
- **Input validation at boundaries** -- validation middleware checks inputs at the HTTP layer; don't duplicate validation deep in services

**Edge Cases:**
- **`OTEL_AVAILABLE` is a feature flag** -- OpenTelemetry is optional; code using it must check `OTEL_AVAILABLE` and handle the case where it's `False`
- **Multi-transport awareness** -- features must work across SSE, WebSocket, stdio, and Streamable HTTP transports; don't assume a single transport
- **Team scoping edge cases** -- `teams: null` with `is_admin: true` = admin bypass; `teams: null` with `is_admin: false` = public-only (NOT admin); missing `teams` key = public-only
- **Redis is optional** -- the gateway works without Redis (falls back to in-memory caching); never assume Redis is available
- **PostgreSQL vs SQLite** -- migrations and queries must work on both; avoid database-specific SQL

---

## Usage Guidelines

**For AI Agents:**
- Read this file before implementing any code
- Follow ALL rules exactly as documented
- When in doubt, prefer the more restrictive option
- Update this file if new patterns emerge

**For Humans:**
- Keep this file lean and focused on agent needs
- Update when technology stack changes
- Review quarterly for outdated rules
- Remove rules that become obvious over time

Last Updated: 2026-02-23
