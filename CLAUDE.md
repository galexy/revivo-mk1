# Project: Personal Finance App

## Overview

- Python FastAPI app with PostgreSQL (SQLAlchemy + Alembic)
- Docker Compose setup: app service + postgres service
- Tests: pytest with unit (tests/unit) and integration (tests/integration) directories
- Integration tests use transactional rollback (session-scoped setup) which can mask issues that only appear with committed data

## Checkpoint Validation

See `.planning/CHECKPOINTS.md` for project-specific validation rules that must be followed during development.

Key points:

- After any migration change, run `alembic upgrade head` against the real database — not just tests
- After any endpoint change, start the actual service and smoke test with curl — not just TestClient
- Integration tests use `metadata.create_all()` which bypasses Alembic — test schema can drift from production
- Never claim completion unless the running service actually works (tests passing is necessary but not sufficient)
