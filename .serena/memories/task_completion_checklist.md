# Task Completion Checklist

When a coding task is completed, run these steps in order:

## 1. Format Code
```bash
make autoflake isort black pre-commit
```

## 2. Type Check (new/changed files only first)
```bash
# Run ty, mypy, and pyrefly on just the changed files
ty check mcpgateway/path/to/file.py
mypy mcpgateway/path/to/file.py
pyrefly check mcpgateway/path/to/file.py
```

## 3. Lint
```bash
make flake8 bandit interrogate pylint
```

## 4. Run Full Verification
```bash
make verify
```

## 5. Run Tests
```bash
make test                    # Full test suite
# Or targeted:
pytest tests/unit/test_specific.py -v
```

## 6. If Database Changes
- Create idempotent Alembic migration
- Verify single head: `cd mcpgateway && alembic heads`
- Migration `down_revision` must point to current head

## 7. Before Committing
- `git commit -s` (DCO sign-off required)
- Use conventional commit format: `feat:`, `fix:`, `docs:`, etc.
- Link issues: `Closes #123`
- Never include AI assistant mentions in commits/PRs
- Don't push until asked
