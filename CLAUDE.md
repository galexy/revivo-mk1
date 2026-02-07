# Project: Personal Finance App

## Overview

- Python FastAPI + PostgreSQL monorepo managed by Nx
- Docker Compose setup: app service + postgres service
- Python dependency management: hatch packages in root pyproject.toml (editable install)
- Tests: pytest with unit and integration directories across apps and libs
- Integration tests use transactional rollback (session-scoped setup) which can mask issues that only appear with committed data

## Monorepo Structure

Managed by Nx with hatch packages for Python editable installs.

```
/
├── apps/
│   ├── api/          # FastAPI backend (Python)
│   │   ├── src/      # Source code (adapters, application, main.py)
│   │   ├── tests/    # API integration and unit tests
│   │   ├── alembic/  # Database migrations
│   │   ├── scripts/  # Operational scripts
│   │   └── docs/     # Runbooks
│   └── web/          # React frontend (Phase 8+)
├── libs/
│   ├── domain/       # Shared domain layer (Python)
│   │   ├── domain/   # Domain models, events, ports
│   │   └── tests/    # Domain unit tests
│   └── ui/           # shadcn/ui components (Phase 8+)
├── nx.json           # Nx workspace config
├── pyproject.toml    # Root project config (deps, tool config, hatch packages)
└── alembic.ini       # Alembic config (points to apps/api/alembic/)
```

## Import Conventions

- Domain layer: `from domain.model.account import Account` (shared library)
- API internals: `from src.adapters.api.app import create_app` (app-local)
- Application layer: `from src.application.services.account_service import AccountService`
- Never use `src.domain.*` -- domain is a separate package at `libs/domain/domain/`

## Nx Commands

- `npx nx test api` -- Run API tests (apps/api/tests/)
- `npx nx test domain` -- Run domain tests (libs/domain/tests/)
- `npx nx lint api` -- Lint API code
- `npx nx lint domain` -- Lint domain code
- `npx nx serve api` -- Start API dev server
- `npx nx show projects` -- List all projects (api, domain, web, ui)
- `npx nx graph` -- Visualize project dependency graph

## Checkpoint Validation

See `.planning/CHECKPOINTS.md` for project-specific validation rules that must be followed during development.

Key points:

- After any migration change, run `alembic upgrade head` against the real database -- not just tests
- After any endpoint change, start the actual service and smoke test with curl -- not just TestClient
- Integration tests use `metadata.create_all()` which bypasses Alembic -- test schema can drift from production
- Never claim completion unless the running service actually works (tests passing is necessary but not sufficient)

## Database Schema Changes

**tables.py is the source of truth for database schema.**

Location: `apps/api/src/adapters/persistence/orm/tables.py`

Rules:
- Never hand-write DDL in migration files
- Always use `alembic revision --autogenerate` to generate migrations from tables.py changes
- After generating, review the migration -- hand-edit ONLY for data backfill logic
- Run `alembic check` to verify no remaining drift
- Run `alembic upgrade head` against the real database (not just tests)

For the full step-by-step procedure, see `.claude/skills/safe-schema-change.md`

## Future Phase Notes

- Phase 8 will add React + Tailwind v4 to apps/web/
- libs/ui/ is prepared for shadcn/ui monorepo setup (https://ui.shadcn.com/docs/monorepo)
- New shared Python libraries go in libs/ with their own pyproject.toml
- New apps go in apps/ with project.json
