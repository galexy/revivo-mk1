# Project: Personal Finance App

## Overview

- Python FastAPI app with PostgreSQL (SQLAlchemy + Alembic)
- Docker Compose setup: app service + postgres service
- Tests: pytest with unit (tests/unit) and integration (tests/integration) directories
- Integration tests use transactional rollback (session-scoped setup) which can mask issues that only appear with committed data

## Chokepoint Testing Rules

### 1. After writing or modifying any Alembic migration

- Run `alembic upgrade head` against the actual dev database (DATABASE_URL_SYNC) and verify it applies cleanly
- If the migration involves FK constraints, verify the referenced tables/columns exist
- Run `alembic downgrade -1` then `alembic upgrade head` to verify reversibility
- NEVER rely solely on integration tests for migration correctness -- integration tests use `metadata.create_all()` which bypasses Alembic entirely

### 2. After implementing or modifying API endpoints

- Start the actual service (`uvicorn src.main:app --host 0.0.0.0 --port 8000`) or use Docker Compose
- Smoke test key endpoints with curl/httpie against the running service
- Verify at minimum: a successful response (not 500), correct response shape, auth works if required
- Do NOT skip this step even if integration tests pass -- TestClient may behave differently from a real HTTP server

### 3. Integration test awareness

- The test suite uses `metadata.create_all()` (not Alembic migrations) to create tables -- this means the test schema can drift from production schema
- Tests use transactional rollback per test -- FK constraints, triggers, and sequences may behave differently with committed data
- When writing tests, consider: "Would this also work against a real database with real migrations?"
- If a test passes but you suspect it might not work in production, add a comment noting the concern

### 4. Phase/wave completion chokepoints

- After completing a wave of tasks that includes migrations: run migrations against real DB, then start the service and smoke test
- After completing a wave of tasks that includes API endpoints: start the service and verify those endpoints work
- Before claiming any phase is complete: start the actual service, run through the key user flows for that phase with curl
- If ANY smoke test fails, the phase is NOT complete -- fix the issue before proceeding

### 5. Never claim completion prematurely

- "All tests pass" is necessary but NOT sufficient for phase completion
- The actual service must start and handle basic requests without 500 errors
- If there is a gap between what tests verify and what the running service does, close that gap before moving on

## Service Testing Commands

```bash
# Start service directly
uvicorn src.main:app --host 0.0.0.0 --port 8000 &

# Or via Docker Compose
docker compose up -d app

# Run migrations against real DB
DATABASE_URL_SYNC=postgresql+psycopg2://postgres:postgres@postgres:5432/personal_finance alembic upgrade head

# Smoke test examples
curl -s http://localhost:8000/docs | head -5  # OpenAPI docs load
curl -s -X POST http://localhost:8000/auth/token -d "username=test@example.com&password=testpass" -H "Content-Type: application/x-www-form-urlencoded"

# Run all tests
pytest tests/ -x -q
```

## SQLAlchemy/Alembic Parity Warning

```
CRITICAL: tests/integration/conftest.py uses metadata.create_all() which creates tables
from SQLAlchemy table definitions, NOT from Alembic migrations. This means:
- A column added to the SQLAlchemy model but missing from migrations will work in tests but fail in production
- An FK constraint in migrations but missing from SQLAlchemy models will exist in production but not in tests
- Index definitions may differ between the two schemas

Always verify migrations apply cleanly to a real database, not just that tests pass.
```
