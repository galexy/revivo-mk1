# Safe Schema Change Procedure

## When to Use

Any time a plan or task requires database schema changes:
- New tables or columns
- Modified columns (type, nullable, default)
- New indexes or constraints
- Foreign key changes

## Procedure

### Step 1: Modify tables.py

Make your schema change in `src/adapters/persistence/orm/tables.py`.

This is the single source of truth for the database schema.

### Step 2: Generate Migration

```bash
alembic revision --autogenerate -m "description of change"
```

This compares tables.py metadata against the current database and generates a migration.

### Step 3: Review the Migration

Check the generated file in `alembic/versions/`.

- Verify the DDL operations match your intent
- Look for unexpected changes (Alembic may detect other drift)

### Step 4: Hand-edit ONLY for Data Backfill

If your change requires data migration (e.g., populating a new NOT NULL column):
- Add data backfill logic to the `upgrade()` function
- Never hand-write DDL operations

If autogenerate didn't produce the right DDL, fix tables.py and regenerate.

### Step 5: Verify No Remaining Drift

```bash
alembic check
```

This confirms there's no remaining difference between tables.py and the migration chain.

### Step 6: Apply to Real Database

```bash
alembic upgrade head
```

This applies the migration to the actual dev database (not just tests).

### Step 7: Verify Reversibility

```bash
alembic downgrade -1
alembic upgrade head
```

This confirms the migration can be rolled back and reapplied cleanly.

### Step 8: Run Tests

```bash
pytest tests/ -x -q
```

Confirm all tests pass, including the schema parity test.

## Common Mistakes to Avoid

1. **Adding a column to tables.py but forgetting to generate a migration**
   - The drift detection test (`tests/integration/test_schema_parity.py`) will catch this
   - Fix: Run `alembic revision --autogenerate`

2. **Writing DDL directly in a migration file instead of changing tables.py first**
   - This causes drift between tables.py and the migration chain
   - Fix: Delete the hand-written migration, update tables.py, then autogenerate

3. **Using `metadata.create_all()` as proof that a schema change works**
   - `metadata.create_all()` bypasses Alembic entirely
   - Integration tests use this approach, so they may pass while production fails
   - Fix: Always run `alembic upgrade head` against the real database

4. **Forgetting to import tables.py in env.py**
   - Already fixed in this project (tables.py is imported via `import src.adapters.persistence.orm.tables`)
   - Without this import, autogenerate sees empty metadata

## Key Files

| File | Purpose |
|------|---------|
| `src/adapters/persistence/orm/tables.py` | Source of truth for schema |
| `alembic/env.py` | Alembic configuration (imports tables.py for autogenerate) |
| `alembic/script.py.mako` | Migration template (imports custom types) |
| `alembic/versions/` | Generated migration files |
| `tests/integration/test_schema_parity.py` | Drift detection test |

## Reference

- Alembic autogenerate docs: https://alembic.sqlalchemy.org/en/latest/autogenerate.html
- compare_type=True: Enabled in env.py for thorough drift detection
- user_module_prefix: Set to "types." for clean TypeDecorator rendering
