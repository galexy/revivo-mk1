# Phase 7: Nx Monorepo Restructure - Context

**Gathered:** 2026-02-07
**Status:** Ready for planning

<domain>
## Phase Boundary

Convert the existing single-app Python project into an Nx monorepo with `apps/api` (backend), `apps/web` (frontend scaffold), `libs/domain` (extracted Python domain layer), and `libs/ui` (future shadcn/ui components). All existing backend tests must pass after restructure. Nx commands must work for building and testing apps.

</domain>

<decisions>
## Implementation Decisions

### Directory Layout
- Backend app at `apps/api/` (not "backend")
- Frontend app at `apps/web/` (not "frontend")
- Domain layer extracted to `libs/domain/` as shared library
- Future shadcn/ui components will live at `libs/ui/` (see https://ui.shadcn.com/docs/monorepo)
- Flat libs structure: `libs/domain`, `libs/ui` (no language namespace)
- Tests colocated with projects: `apps/api/tests/`, `libs/domain/tests/`
- Docker files (Dockerfile, docker-compose.yml) stay at repo root
- `.planning/` directory stays at repo root (project-wide, not app-specific)

### Migration Strategy
- Incremental commits (not big-bang) — init Nx, move backend, extract domain, scaffold frontend
- Preserve git history using `git mv` for moved files
- Rename import paths to match new structure (e.g., `from domain.model import ...` not `from app.domain.model import ...`)
- Validation checkpoint: all tests pass + UAT tests rerun + Nx commands work

### Build & Dev Workflow
- Python dependency management: Claude's discretion based on Nx Python plugin conventions
- Devcontainer: fix what breaks only (Docker context paths, volume mounts, working directories). No new features.
- CLAUDE.md updated this phase to document monorepo structure, import conventions, Nx commands, directory layout for future shadcn/ui
- Nx task definitions (build, test, lint) set up for both apps/api and apps/web

### Frontend Scaffold
- `apps/web/` is empty directory + `project.json` only (no React code — Phase 8)
- Minimal `package.json` at `apps/web/` (name + version, no deps)
- `libs/ui/` scaffolded as empty Nx project + `project.json` (ready for Phase 8 shadcn/ui setup)
- `libs/domain/` gets `project.json` with test/lint targets

### Claude's Discretion
- Alembic migrations location (likely `apps/api/alembic/` since API owns the database)
- Python dependency management approach (per-project vs root pyproject.toml)
- Exact Nx plugin choices for Python projects
- Nx workspace configuration details

</decisions>

<specifics>
## Specific Ideas

- shadcn/ui monorepo setup should follow their official guide (https://ui.shadcn.com/docs/monorepo) — document the intended libs/ui path in CLAUDE.md even though no components are added this phase
- Git mv for history preservation is important — the project has 45+ plans of commit history worth keeping traceable

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 07-nx-monorepo-restructure*
*Context gathered: 2026-02-07*
