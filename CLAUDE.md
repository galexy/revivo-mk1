# Project: Personal Finance App

## Overview

- Python FastAPI app with PostgreSQL (SQLAlchemy + Alembic)
- Nx monorepo: backend at apps/api/, frontend at apps/web/
- Docker Compose setup: app service + postgres service
- Tests: pytest with unit (apps/api/tests/unit) and integration (apps/api/tests/integration) directories
- Integration tests use transactional rollback (session-scoped setup) which can mask issues that only appear with committed data

## Checkpoint Validation

See `.planning/CHECKPOINTS.md` for project-specific validation rules that must be followed during development.

Key points:

- After any migration change, run `alembic upgrade head` against the real database — not just tests
- After any endpoint change, start the actual service and smoke test with curl — not just TestClient
- Integration tests use `metadata.create_all()` which bypasses Alembic — test schema can drift from production
- Never claim completion unless the running service actually works (tests passing is necessary but not sufficient)

## Database Schema Changes

**tables.py is the source of truth for database schema.**

Rules:
- Never hand-write DDL in migration files
- Always use `alembic revision --autogenerate` to generate migrations from tables.py changes
- After generating, review the migration -- hand-edit ONLY for data backfill logic
- Run `alembic check` to verify no remaining drift
- Run `alembic upgrade head` against the real database (not just tests)

For the full step-by-step procedure, see `.claude/skills/safe-schema-change.md`
