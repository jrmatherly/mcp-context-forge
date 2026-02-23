# Suggested Commands

## Setup
```bash
cp .env.example .env             # Create environment config
make venv                        # Create virtual environment with uv
make install-dev                 # Install with dev dependencies
make check-env                   # Verify .env against .env.example
```

## Running
```bash
make dev                         # Dev server on :8000 with autoreload
make serve                       # Production gunicorn on :4444
make certs && make serve-ssl     # HTTPS on :4444
```

## Code Quality (after writing code)
```bash
make autoflake isort black pre-commit   # Format code
```

## Type Checking (check new files only, then run full suite)
```bash
# Use ty, mypy, pyrefly on just the new/changed files, then:
make flake8 bandit interrogate pylint verify
```

## Testing
```bash
make test                        # Run main test suite
make test-unit                   # Run unit tests only
make test-cov                    # Run tests with coverage
make test-security               # Run security tests
pytest tests/unit/test_foo.py    # Run specific test file
pytest -k "test_name"            # Run specific test by name
```

## Database Migrations
```bash
cd mcpgateway && alembic heads                              # Check current head
cd mcpgateway && alembic revision --autogenerate -m "desc"  # Auto-generate migration
cd mcpgateway && alembic upgrade head                       # Apply migrations
```

## JWT Token Generation
```bash
python -m mcpgateway.utils.create_jwt_token --username admin@apollosai.dev --exp 10080 --secret KEY
```

## MCP Translation (expose stdio server via HTTP)
```bash
python -m mcpgateway.translate --stdio "uvx mcp-server-git" --port 9000
```

## System Utilities (macOS/Darwin)
```bash
git status / git diff / git log   # Git operations
gh pr create / gh issue list      # GitHub CLI
ls / find / grep                  # File operations (note: macOS variants)
uv pip install <package>          # Package installation (use uv, not pip)
```

## Docker/Container
```bash
docker compose up -d              # Start with docker compose
make container                    # Build container image
```

## Documentation
```bash
make docs-serve                   # Serve docs locally (Mintlify)
```
