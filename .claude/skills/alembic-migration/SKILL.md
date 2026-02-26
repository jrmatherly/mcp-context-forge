---
name: alembic-migration
description: Create an Alembic database migration following project conventions (idempotent, single-head). Use when adding columns, tables, or modifying the database schema.
disable-model-invocation: true
---

Create an Alembic migration for: $ARGUMENTS

## Critical Rules (from CLAUDE.md)

- `down_revision` MUST point to the **actual current head** (verified below)
- Never guess or copy `down_revision` from older migrations
- Multiple heads = broken tests. Always verify single head after creating.
- Write **idempotent** migrations that check before modifying.

## Steps

1. **Verify current head** (this is the value for `down_revision`):
   ```bash
   cd mcpgateway && alembic heads
   ```

2. **Generate the migration**:
   ```bash
   cd mcpgateway && alembic revision --autogenerate -m "$ARGUMENTS"
   ```

3. **Edit the generated file** to make it idempotent:
   ```python
   def upgrade() -> None:
       inspector = sa.inspect(op.get_bind())
       if "my_table" not in inspector.get_table_names():
           return
       columns = [col["name"] for col in inspector.get_columns("my_table")]
       if "new_column" in columns:
           return
       op.add_column("my_table", sa.Column("new_column", sa.String(), nullable=True))
   ```

4. **Verify single head** after creation:
   ```bash
   cd mcpgateway && alembic heads
   ```
   Must show exactly ONE head. If multiple, fix `down_revision`.

5. **Run tests** to confirm:
   ```bash
   make test
   ```
