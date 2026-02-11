---
phase: 14-frontend-api-routing
plan: 01
subsystem: frontend
tags: [tanstack-query, openapi-typescript, typescript, type-generation]

# Dependency graph
requires:
  - phase: 13-login-ui
    provides: React app with auth, routing, and shadcn/ui components
provides:
  - TanStack Query packages installed for API state management
  - openapi-typescript for auto-generating types from OpenAPI spec
  - OpenAPI extraction script (apps/api/scripts/generate_openapi.py)
  - Generated TypeScript types (apps/web/src/lib/api-types.generated.ts)
  - Nx target (generate-api-types) for regenerating types
affects: [14-02-api-client, 15-api-integration, frontend-data-layer]

# Tech tracking
tech-stack:
  added:
    - "@tanstack/react-query: ^5.90.20"
    - "@tanstack/react-query-devtools: ^5.91.3"
    - "openapi-typescript: ^7.12.0"
  patterns:
    - "OpenAPI-first type generation: backend spec drives frontend types"
    - "Python script extracts OpenAPI JSON from FastAPI app without starting server"
    - "Nx target for regenerating types after API changes"

key-files:
  created:
    - apps/api/scripts/generate_openapi.py
    - apps/web/src/lib/api-types.generated.ts
  modified:
    - apps/web/package.json
    - apps/web/project.json

key-decisions:
  - "OpenAPI-first type generation: backend spec is source of truth for API types"
  - "Extraction script imports create_app directly (no server startup needed)"
  - "Nx target with workspace root cwd for cross-project coordination"
  - "Generated types include paths (endpoints) and components.schemas (DTOs)"

patterns-established:
  - "Type regeneration workflow: modify API -> run nx generate-api-types web -> commit types"
  - "No manual type definitions - all API types auto-generated from OpenAPI spec"

# Metrics
duration: 2min
completed: 2026-02-11
---

# Phase 14 Plan 01: OpenAPI Type Generation & TanStack Query Install Summary

**TanStack Query and openapi-typescript installed with auto-generated TypeScript types from FastAPI OpenAPI spec**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-11T05:37:53Z
- **Completed:** 2026-02-11T05:39:58Z
- **Tasks:** 2
- **Files modified:** 4 (2 created, 2 modified)

## Accomplishments
- TanStack Query packages installed for API state management in future plans
- openapi-typescript generates TypeScript types from OpenAPI JSON
- Python script extracts OpenAPI spec from FastAPI app without server
- Nx target enables one-command type regeneration

## Task Commits

Each task was committed atomically:

1. **Task 1: Install packages and create OpenAPI generation script** - `ae4b5ac` (feat)
2. **Task 2: Generate TypeScript types and add Nx target** - `9f376d5` (feat)

## Files Created/Modified
- `apps/api/scripts/generate_openapi.py` - Extracts OpenAPI JSON from FastAPI app via create_app().openapi()
- `apps/web/src/lib/api-types.generated.ts` - Auto-generated TypeScript types (2784 lines)
- `apps/web/package.json` - Added TanStack Query and openapi-typescript dependencies
- `apps/web/project.json` - Added generate-api-types Nx target

## Decisions Made

1. **OpenAPI-first type generation**: Backend FastAPI spec is the single source of truth. Frontend types are derived, never manually written.

2. **Extraction script without server**: Script imports `create_app` and calls `.openapi()` directly. No uvicorn startup, no database connection needed. Fast regeneration.

3. **Nx target with workspace root cwd**: Target runs two commands sequentially (extract JSON, generate TS). Uses `{workspaceRoot}` cwd so paths work from monorepo root.

4. **Generated file includes paths and schemas**: Types include both API endpoint signatures (`paths`) and DTO schemas (`components.schemas`). Phase 14-02 will use these for type-safe API client.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

**pnpm not in PATH**: The environment didn't have pnpm installed globally. Resolved by using `npx pnpm` which auto-installs and runs pnpm. All subsequent pnpm commands in this phase used `npx pnpm` pattern.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

**Ready for Phase 14-02 (API Client Setup):**
- TanStack Query packages installed
- Generated types available at `apps/web/src/lib/api-types.generated.ts`
- Types include endpoint signatures and response/request schemas
- Nx target (`generate-api-types`) ready for use after API changes

**Type regeneration workflow:**
1. Modify backend API (add/change endpoints or schemas)
2. Run `npx nx generate-api-types web`
3. Commit updated `api-types.generated.ts`
4. TypeScript compiler catches breaking changes in frontend

---
*Phase: 14-frontend-api-routing*
*Completed: 2026-02-11*
