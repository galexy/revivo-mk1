# Project Checkpoints

Validation rules that GSD agents (planner and executor) must follow during phase execution. These are project-specific — they reflect lessons learned from this codebase.

## Triggers

### After writing or modifying any Alembic migration

- Run `alembic upgrade head` against the actual dev database and verify it applies cleanly
- If the migration involves FK constraints, verify the referenced tables/columns exist
- Run `alembic downgrade -1` then `alembic upgrade head` to verify reversibility
- NEVER rely solely on integration tests for migration correctness — integration tests use `metadata.create_all()` which bypasses Alembic entirely

### After implementing or modifying API endpoints

- Start the actual service (`uvicorn src.main:app --host 0.0.0.0 --port 8000`)
- Smoke test key endpoints with curl against the running service
- Verify at minimum: a successful response (not 500), correct response shape, auth works if required
- Do NOT skip this even if integration tests pass — TestClient may behave differently from a real HTTP server

## Planning Rules

When creating plans for phases that involve backend changes (migrations, API endpoints, service logic):

- Migration tasks: `<verify>` must include running `alembic upgrade head` against the real database
- Endpoint tasks: `<verify>` must include starting the service and curling the new endpoint(s)
- Final task in any phase with backend changes: add explicit service smoke test verification

## Execution Rules

- After completing a migration task: run `alembic upgrade head` and verify success before committing
- After completing an endpoint task: start the service, send at least one request, verify no 500
- Before the final task in any plan that modifies backend code: ensure migrations apply and service responds
- Do NOT claim task/plan completion if migrations fail or the service returns 500 errors

## Known Gaps

### Integration tests vs. real database

This project's integration tests use `metadata.create_all()` (NOT Alembic migrations) to create tables. This means:

- A column added to the SQLAlchemy model but missing from migrations will work in tests but fail in production
- An FK constraint in migrations but missing from SQLAlchemy models will exist in production but not in tests
- Index definitions may differ between the two schemas
- Tests use transactional rollback per test — FK constraints, triggers, and sequences may behave differently with committed data

A passing test suite does NOT guarantee the real service works. Always cross-check against the running service for migration-related changes.

## Phase/Wave Completion Gates

- After completing a wave that includes migrations: run migrations against real DB, start service, smoke test
- After completing a wave that includes API endpoints: start service, verify those endpoints work
- Before claiming any phase complete: start the actual service, run key user flows with curl
- If ANY smoke test fails, the phase is NOT complete — fix the issue before proceeding
- "All tests pass" is necessary but NOT sufficient for phase completion

## Commands Reference

```bash
# Run migrations against real DB
alembic upgrade head

# Start service
uvicorn src.main:app --host 0.0.0.0 --port 8000 &

# Smoke test
curl -s http://localhost:8000/docs | head -5
curl -s -X POST http://localhost:8000/auth/token \
  -d "username=test@example.com&password=testpass" \
  -H "Content-Type: application/x-www-form-urlencoded"

# Run all tests
pytest tests/ -x -q
```
