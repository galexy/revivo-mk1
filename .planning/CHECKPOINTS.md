# Project Checkpoints

Validation rules that GSD agents (planner and executor) must follow during phase execution. These are project-specific — they reflect lessons learned from this codebase.

## Triggers

### After writing or modifying any code

**Type check immediately:**
- Run `npx nx typecheck <project>` after writing code, before running tests
- Pyright strict mode is configured -- it catches async/sync mismatches, missing attributes, protocol violations, and unhandled return types
- Design with types upfront: define protocols, return types, and function signatures first, then implement
- Do NOT defer type errors to "fix later" -- they compound and mask deeper issues

### After writing or modifying any Alembic migration

**Autogenerate-first workflow (required):**
- Schema changes MUST start in `apps/api/src/adapters/persistence/orm/tables.py`
- Then use `cd apps/api && uv run --package personal-finance-api alembic revision --autogenerate -m "description"` to generate the migration
- Never hand-write DDL operations in migration files (if autogenerate doesn't produce the right DDL, fix tables.py)
- Hand-edit migrations ONLY for data backfill logic (not DDL)

**Verification:**
- Run `cd apps/api && uv run --package personal-finance-api alembic check` after generating migrations to confirm no remaining drift
- Run `cd apps/api && uv run --package personal-finance-api alembic upgrade head` against the actual dev database and verify it applies cleanly
- If the migration involves FK constraints, verify the referenced tables/columns exist
- Run `alembic downgrade -1` then `alembic upgrade head` to verify reversibility
- NEVER rely solely on integration tests for migration correctness — integration tests use `metadata.create_all()` which bypasses Alembic entirely

### After implementing or modifying API endpoints

- Start the actual service (`npx nx serve api`)
- Smoke test key endpoints with curl against the running service
- Verify at minimum: a successful response (not 500), correct response shape, auth works if required
- Do NOT skip this even if integration tests pass — TestClient may behave differently from a real HTTP server

### After modifying dependencies in pyproject.toml

- Run `uv sync --all-packages` and verify no packages were silently removed
- Dependency conflicts can cause uv to drop unrelated packages (Phase 5: procrastinate removed email-validator)
- Run `npx nx run-many -t test` to verify nothing broke across projects

## Planning Rules

When creating plans for phases that involve backend changes (migrations, API endpoints, service logic):

- Migration tasks: `<verify>` must include running `alembic upgrade head` against the real database
- Endpoint tasks: `<verify>` must include starting the service and curling the new endpoint(s)
- Async code tasks: `<verify>` must include type checking to confirm async chain integrity
- Final task in any phase with backend changes: add explicit service smoke test verification
- Plans should specify type annotations in task descriptions -- types are part of the design, not a post-hoc addition

## Execution Rules

- After writing any code: run `npx nx typecheck <project>` and fix errors before proceeding
- After completing a task: run `npx nx test <project>` and fix failures before committing
- After completing a migration task: run `alembic upgrade head` and verify success before committing
- After completing an endpoint task: start the service, send at least one request, verify no 500
- Before the final task in any plan that modifies backend code: ensure migrations apply and service responds
- Do NOT claim task/plan completion if type checks fail, tests fail, migrations fail, or the service returns 500 errors

## Known Gaps

### Integration tests vs. real database

This project's integration tests use `metadata.create_all()` (NOT Alembic migrations) to create tables. This means:

- A column added to the SQLAlchemy model but missing from migrations will work in tests but fail in production
- An FK constraint in migrations but missing from SQLAlchemy models will exist in production but not in tests
- Index definitions may differ between the two schemas
- Tests use transactional rollback per test — FK constraints, triggers, and sequences may behave differently with committed data

**RESOLVED:** The drift detection test (`apps/api/tests/integration/test_schema_parity.py`) now guards against schema drift between `metadata.create_all()` (used by integration tests) and `alembic upgrade head` (used by production). This test runs alembic migrations against a clean database and compares the result to SQLAlchemy metadata.

A passing test suite does NOT guarantee the real service works. Always cross-check against the running service for migration-related changes.

### Integration tests vs. async runtime

Integration tests often mock async infrastructure (job queues, event handlers, email services). This can mask:

- Sync/async color mismatches (sync function calling async function deadlocks under event loop)
- Missing `await` on coroutine objects (returns unawaited coroutine instead of result)
- Event handler failures swallowed by fire-and-forget patterns

**Mitigation:** Pyright strict mode catches most of these statically. Run `npx nx typecheck api` after any change to async code paths.

## Phase/Wave Completion Gates

- After completing a wave that includes migrations: run migrations against real DB, start service, smoke test
- After completing a wave that includes API endpoints: start service, verify those endpoints work
- Before claiming any phase complete: start the actual service, run key user flows with curl
- If ANY smoke test fails, the phase is NOT complete — fix the issue before proceeding
- "All tests pass" is necessary but NOT sufficient for phase completion
- "Type checks pass" is necessary but NOT sufficient -- still need runtime verification

## Commands Reference

```bash
# Type check (run FIRST, before tests)
npx nx typecheck api
npx nx typecheck domain
npx nx run-many -t typecheck   # all projects

# Run tests
npx nx test api
npx nx test domain
npx nx run-many -t test        # all projects

# Lint
npx nx lint api
npx nx lint domain
npx nx run-many -t lint        # all projects

# Run migrations against real DB (from apps/api/)
cd apps/api && uv run --package personal-finance-api alembic upgrade head

# Start service
npx nx serve api

# Smoke test
curl -s http://localhost:8000/docs | head -5
curl -s -X POST http://localhost:8000/auth/token \
  -d "username=test@example.com&password=testpass" \
  -H "Content-Type: application/x-www-form-urlencoded"

# Sync dependencies after pyproject.toml changes
uv sync --all-packages
```
