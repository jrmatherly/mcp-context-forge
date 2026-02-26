---
name: check-env
description: Run the full pre-commit quality gate — format, lint, static analysis. Use before committing changes.
disable-model-invocation: true
---

Run the project's full quality pipeline before committing.

## Current State
- Branch: !`git branch --show-current`
- Unstaged changes: !`git diff --stat`

## Steps

1. Format and run pre-commit hooks:
   ```bash
   make autoflake isort black pre-commit
   ```

2. Type-check new/modified Python files only (use `ty` or `mypy`):
   ```bash
   # Check just the files that changed
   git diff --name-only --diff-filter=ACMR HEAD -- '*.py' | xargs -I{} .venv/bin/mypy {} --ignore-missing-imports 2>/dev/null || true
   ```

3. Run static analysis:
   ```bash
   make flake8 bandit interrogate pylint verify
   ```

4. Report any failures. For each failure:
   - Show the exact error
   - Fix it if straightforward
   - Ask the user if the fix is unclear
