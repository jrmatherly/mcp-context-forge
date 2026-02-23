# Code Style and Conventions

## Formatting
- **Black**: line-length 200, target Python 3.10-3.12
- **isort**: profile=black, from_first=true, known_first_party=["mcpgateway"]
- **Ruff**: line-length 200, rules E3/E4/E7/E9/F/D1

## Naming
- `snake_case` for functions, methods, variables, modules
- `PascalCase` for classes
- `UPPER_CASE` for constants
- Prefix unused variables with underscore `_`

## Type Hints
- Python >= 3.11 with type hints everywhere
- Strict mypy enabled (all strict flags on)
- Pydantic mypy plugin active
- `from __future__ import annotations` where needed

## Imports
- Grouped per isort sections: stdlib → third-party → first-party (`mcpgateway`) → local
- `from_first = true` (from imports before plain imports)
- One blank line between sections
- Skip `__init__.py` files from sorting

## Docstrings
- Required on all public functions/classes/modules (interrogate fail-under = 100)
- D1 rules from ruff enforce docstring presence
- Tests, scripts, and non-production code exempt from D1

## Key Patterns
- FastAPI dependency injection via `Depends()`
- Pydantic models for all request/response schemas
- SQLAlchemy ORM models in `db.py`
- Service layer pattern: business logic in `services/`, endpoints in `routers/`
- Alembic for database migrations (always idempotent)

## Security
- Never commit secrets; use `.env`
- Bandit for security scanning (no global skips)
- OWASP top 10 awareness required
- `# nosec` inline comments only for verified false positives

## Git/PR
- Sign commits: `git commit -s` (DCO)
- Conventional Commits: `feat:`, `fix:`, `docs:`, `refactor:`, `chore:`
- Link issues: `Closes #123`
- Never mention AI assistants in PRs/diffs
- Don't push until asked
