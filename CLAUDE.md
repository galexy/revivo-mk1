# Project: Personal Finance App

## Overview

- Python FastAPI + PostgreSQL monorepo managed by Nx
- Runs in two environments: Docker Compose (local dev) and Claude Code Web (cloud)
- Python dependency management: hatch packages in root pyproject.toml (editable install)
- Tests: pytest with unit and integration directories across apps and libs
- Integration tests use transactional rollback (session-scoped setup) which can mask issues that only appear with committed data

## Environment Setup

This project supports two development environments. PostgreSQL configuration auto-detects which environment you're in.

### Claude Code Web (cloud)

PostgreSQL 16 is pre-installed in the environment. A SessionStart hook runs `scripts/setup-postgres.sh` automatically to:
- Start PostgreSQL if it isn't running
- Configure password authentication for TCP connections
- Create required databases (`personal_finance`, `finance_test`, `jobs`)
- Set the `postgres` user password to `postgres`

If the hook hasn't run or you need to set up manually:

```bash
sudo bash scripts/setup-postgres.sh
```

No Docker Compose is needed. All code defaults to `localhost:5432` when no environment variables are set.

### Local Development (Docker Compose / Devcontainer)

Docker Compose provides PostgreSQL via the `postgres` service. Environment variables are set explicitly in `docker-compose.yml` and `.devcontainer/devcontainer.json` to point at the Docker hostname (`postgres:5432`).

```bash
# Start services
docker compose up -d

# Or use VS Code Devcontainer (recommended)
# "Reopen in Container" — handles everything automatically
```

### How environment detection works

All database code defaults to `localhost:5432` when no environment variables are set — this works out-of-the-box for Claude Code Web. Docker Compose and the devcontainer set `DATABASE_URL`, `DATABASE_URL_SYNC`, and `JOB_QUEUE_DATABASE_URL` explicitly to point at Docker service hostnames. No conditional logic or feature flags are needed.

| Variable | Claude Code Web (default) | Docker Compose (explicit) |
|---|---|---|
| `DATABASE_URL` | `postgresql://...@localhost:5432/personal_finance` | `postgresql+asyncpg://...@postgres:5432/personal_finance` |
| `DATABASE_URL_SYNC` | _(derived from DATABASE_URL)_ | `postgresql+psycopg2://...@postgres:5432/personal_finance` |
| `TEST_DATABASE_URL` | `postgresql://...@localhost:5432/finance_test` | `postgresql://...@postgres:5432/finance_test` |
| `JOB_QUEUE_DATABASE_URL` | `postgresql://...@localhost:5432/jobs` | `postgresql://...@postgres-jobs:5432/jobs` |

## Monorepo Structure

Managed by Nx with hatch packages for Python editable installs.

```
/
├── apps/
│   ├── api/          # FastAPI backend (Python)
│   │   ├── src/      # Source code (adapters, application, main.py)
│   │   ├── tests/    # API integration and unit tests
│   │   ├── alembic/  # Database migrations
│   │   ├── alembic.ini # Alembic config
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
```

## Import Conventions

- Domain layer: `from domain.model.account import Account` (shared library)
- API internals: `from src.adapters.api.app import create_app` (app-local)
- Application layer: `from src.application.services.account_service import AccountService`
- Never use `src.domain.*` -- domain is a separate package at `libs/domain/domain/`

## Nx Commands

All tasks should be run through Nx, not the underlying tools directly.

- `npx nx test api` -- Run API tests (apps/api/tests/)
- `npx nx test domain` -- Run domain tests (libs/domain/tests/)
- `npx nx lint api` -- Lint API code
- `npx nx lint domain` -- Lint domain code
- `npx nx typecheck api` -- Type check API code (pyright strict)
- `npx nx typecheck domain` -- Type check domain code (pyright strict)
- `npx nx serve api` -- Start API dev server
- `npx nx run-many -t test` -- Run tests across all projects
- `npx nx run-many -t lint typecheck` -- Run lint and typecheck across all projects
- `npx nx show projects` -- List all projects (api, domain, web, ui)
- `npx nx graph` -- Visualize project dependency graph

## uv Workspace

This project uses a uv workspace. The root `pyproject.toml` defines the workspace; each app/lib has its own `pyproject.toml` with dependencies.

- `uv sync --all-packages` -- Install all workspace members and their dependencies
- Nx targets use `uv run --package <name>` to run under the correct package context
- Plain `uv sync` only installs root dependencies (dev tools) -- not app/lib dependencies

## Development Workflow: Think End-to-End

**Integration tests passing is NOT completion.** This project has a documented history of tests passing while the actual service fails. Treat every change as unverified until you confirm it works end-to-end.

### Verification ladder (follow this order)

1. **Type check first** -- Run `npx nx typecheck <project>` after writing code. Pyright strict mode catches async/sync mismatches, missing attributes, and protocol violations that tests may not exercise. Design with types upfront; let the type checker find errors before you run anything.

2. **Run tests** -- Run `npx nx test <project>`. Tests are necessary but not sufficient. Be aware that integration tests use `metadata.create_all()` (not Alembic) and transactional rollback, which mask migration drift and commit-dependent behavior.

3. **Run the actual service** -- After any migration, endpoint, or service change: start the service with `npx nx serve api`, then smoke test with curl. TestClient does not behave identically to a real HTTP server.

4. **Check migrations against real DB** -- After any schema change, run `cd apps/api && uv run --package personal-finance-api alembic upgrade head` against the real database. The drift detection test guards against metadata vs migration mismatch, but it doesn't catch runtime issues.

### Async/sync discipline

This codebase has a full async chain from routes through to event handlers. Mixing sync and async code caused a Phase 6 incident that required converting 28 service methods across 17 files. Prevent this:

- **All write paths are async:** route (async def) -> await service.method() -> await uow.commit() -> await publish_all() -> await handler() -> await defer_async()
- **Read-only paths may be sync** for thread pool execution
- When adding new service methods, event handlers, or routes, check the call chain end-to-end. A sync function calling an async function (or vice versa) will pass type checks but deadlock at runtime under FastAPI's event loop.
- **Type check catches this** -- pyright strict flags `Coroutine` return types that aren't awaited. Run typecheck before testing.

### What to run and when

| Change type | Required checks |
|---|---|
| Domain model changes | `npx nx typecheck domain && npx nx test domain` |
| Service/repository changes | `npx nx typecheck api && npx nx test api` |
| API endpoint changes | Above + `npx nx serve api` + curl smoke test |
| Migration/schema changes | Above + `cd apps/api && uv run --package personal-finance-api alembic upgrade head` |
| Dependency changes | `uv sync --all-packages && npx nx run-many -t test` |
| Cross-cutting changes | `npx nx run-many -t typecheck test` |

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

## GSD Plan Execution Quality

When executing GSD plans, these rules prevent the pattern of "tests pass, service breaks":

### During planning (`/gsd:plan-phase`)

- Every plan that modifies API endpoints or services MUST include a `<verify>` step that starts the real service and smoke tests with curl
- Every plan that adds async code MUST note the async chain in the task context so the executor maintains it
- Plans should specify type annotations upfront in task descriptions -- not as an afterthought

### During execution (`/gsd:execute-phase`)

- Run `npx nx typecheck <project>` after each task, before committing. Type errors compound; catching them early is cheaper than debugging runtime failures during UAT.
- Run `npx nx test <project>` after each task. Fix failures immediately -- don't defer to the next task.
- For the final task in any plan: run the full verification ladder (typecheck -> test -> serve -> smoke test)
- When adding dependencies to `pyproject.toml`, run `uv sync --all-packages` and verify no packages were silently removed (dependency conflicts can drop unrelated packages)

### Lessons from past phases

- **Phase 4.1:** Integration tests used `metadata.create_all()` while production used Alembic migrations. 7 hand-written migrations had schema drift that tests couldn't detect. Fixed by adding drift detection test.
- **Phase 5:** Adding `procrastinate` silently removed `email-validator` due to dependency conflict. Tests broke immediately but it could have been worse.
- **Phase 6:** Sync event handlers calling async Procrastinate `defer()` deadlocked under FastAPI's event loop. Integration tests didn't catch it because they mocked the job queue. Required converting 28 methods across 17 files. Pyright strict mode would have flagged the Coroutine/None type mismatch.
- **Phase 7:** Nx targets with wrong paths, missing venv prefixes, and incorrect cwd all passed individual checks but failed when run through Nx. Always test through Nx, not directly.

## Background Servers

Dev servers (`npx nx serve api`, `npx nx serve web`) and headless Chromium are long-running processes. Use the correct pattern to launch and stop them so they don't become orphaned processes.

### How to launch

Use the Bash tool with `run_in_background: true`. Do **NOT** use `&` in the command itself -- the background task IS the server process.

```
# Correct -- task stays "running", stoppable via TaskStop
Bash(command="npx nx serve web", run_in_background=true)  # returns task ID, e.g. "abc123"

# Correct -- Chromium for browser testing
Bash(command="chromium --headless=new --no-sandbox --remote-debugging-port=9222 --disable-gpu --disable-dev-shm-usage about:blank", run_in_background=true)
```

```
# WRONG -- orphans the process, task "completes" immediately, no way to stop
Bash(command="npx nx serve web &\nsleep 5\necho done", run_in_background=true)
```

### How to stop

Use `TaskStop` with the task ID returned from the launch call:

```
TaskStop(task_id="abc123")
```

For Chromium cleanup (if launched outside the pattern): `pkill -f 'chromium.*remote-debugging'`

### When to use which server

| Task | Server(s) needed |
|---|---|
| API smoke test (curl) | `npx nx serve api` |
| Frontend visual check | `npx nx serve web` + Chromium |
| Full E2E (frontend + backend) | Both `serve api` and `serve web` + Chromium |

### Cleanup

Always stop background servers when done with visual/smoke testing. Stop in reverse order: Chromium first, then dev servers.

## Chrome DevTools MCP

The Chrome DevTools MCP server requires a headless Chromium instance with the remote debugging port open. Start it as a background task (see "Background Servers" above) before using any `mcp__chrome-devtools__*` tools.

Note: This environment has no external internet access, so Swagger UI at `/docs` won't render (CDN resources are unreachable). Use `/openapi.json` for the raw OpenAPI spec instead.

## Future Phase Notes

- Phase 8 will add React + Tailwind v4 to apps/web/
- libs/ui/ is prepared for shadcn/ui monorepo setup (https://ui.shadcn.com/docs/monorepo)
- New shared Python libraries go in libs/ with their own pyproject.toml
- New apps go in apps/ with project.json


<!-- nx configuration start-->
<!-- Leave the start & end comments to automatically receive updates. -->

# General Guidelines for working with Nx

- When running tasks (for example build, lint, test, e2e, etc.), always prefer running the task through `nx` (i.e. `nx run`, `nx run-many`, `nx affected`) instead of using the underlying tooling directly
- You have access to the Nx MCP server and its tools, use them to help the user
- When answering questions about the repository, use the `nx_workspace` tool first to gain an understanding of the workspace architecture where applicable.
- When working in individual projects, use the `nx_project_details` mcp tool to analyze and understand the specific project structure and dependencies
- For questions around nx configuration, best practices or if you're unsure, use the `nx_docs` tool to get relevant, up-to-date docs. Always use this instead of assuming things about nx configuration
- If the user needs help with an Nx configuration or project graph error, use the `nx_workspace` tool to get any errors
- For Nx plugin best practices, check `node_modules/@nx/<plugin>/PLUGIN.md`. Not all plugins have this file - proceed without it if unavailable.

<!-- nx configuration end-->
