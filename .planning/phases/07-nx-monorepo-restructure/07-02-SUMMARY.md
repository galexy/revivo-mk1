---
phase: 07-nx-monorepo-restructure
plan: 02
subsystem: infra
tags: [monorepo, nx, git-mv, pyproject, alembic, project-restructure]

# Dependency graph
requires:
  - phase: 07-01
    provides: Nx workspace init with nx.json and project scaffolds
provides:
  - Backend API at apps/api/ as registered Nx project
  - apps/api/project.json with serve/test/lint targets
  - Updated alembic.ini, Makefile, CHECKPOINTS.md, skill docs for new paths
  - Editable install from apps/api/src via hatch packages config
affects: [07-03, 07-04, all-future-phases-referencing-backend-paths]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Monorepo layout: apps/api/ for backend, apps/web/ for frontend"
    - "Nx project.json with .venv/bin/ paths for Python tool execution"
    - "Editable install via hatch packages=['apps/api/src'] preserves import src.* pattern"

key-files:
  created:
    - apps/api/project.json
    - apps/api/pyproject.toml
  modified:
    - pyproject.toml
    - alembic.ini
    - Makefile
    - CLAUDE.md
    - .planning/CHECKPOINTS.md
    - .claude/skills/safe-schema-change.md

key-decisions:
  - "Keep root pyproject.toml as regular project (not uv workspace) to avoid typeid-python Rust build issue in offline environment"
  - "Use hatch packages=['apps/api/src'] for editable install -- preserves import src.* pattern across entire codebase"
  - "Nx targets use .venv/bin/ absolute paths since Nx runs outside Python virtual environment"
  - "Nx targets use {workspaceRoot} cwd to run from repo root where venv lives"
  - "alembic.ini prepend_sys_path includes both . and apps/api for import resolution"
  - "path_separator=os in alembic.ini to suppress deprecation warning"

patterns-established:
  - "Backend at apps/api/: all source, tests, alembic, scripts, docs in one directory"
  - "Nx targets reference Python tools via .venv/bin/ prefix"
  - "All documentation updated when files move (CLAUDE.md, CHECKPOINTS.md, skills)"

# Metrics
duration: 34min
completed: 2026-02-07
---

# Phase 7 Plan 2: Backend as Nx Project Summary

**Backend moved to apps/api/ via git mv with all 444 tests passing, Nx project registered with serve/test/lint targets, and all configs updated**

## Performance

- **Duration:** 34 min
- **Started:** 2026-02-07T05:49:54Z
- **Completed:** 2026-02-07T06:23:53Z
- **Tasks:** 3
- **Files modified:** 148 (142 renames + 6 config updates)

## Accomplishments
- Moved entire backend (src, tests, alembic, scripts, docs) to apps/api/ via git mv preserving history
- Created apps/api/project.json registering API as Nx project with serve/test/lint targets
- Updated all configuration files (alembic.ini, Makefile, CLAUDE.md, CHECKPOINTS.md, skill docs) for new paths
- Verified: 444 tests pass, alembic migrations apply, service starts and responds, Nx targets execute

## Task Commits

Each task was committed atomically:

1. **Task 1: Move backend files to apps/api/ using git mv** - `126c261` (feat)
2. **Task 2: Update configuration files for new backend location** - `21d98f7` (chore)
3. **Task 3: Verify backend works at new location** - `3ca2934` (fix)

## Files Created/Modified
- `apps/api/src/**` - All backend source code (moved from src/)
- `apps/api/tests/**` - All tests (moved from tests/)
- `apps/api/alembic/**` - Migration scripts (moved from alembic/)
- `apps/api/scripts/**` - Operational scripts (moved from scripts/)
- `apps/api/docs/**` - Documentation (moved from docs/)
- `apps/api/pyproject.toml` - API-specific Python project config
- `apps/api/project.json` - Nx project definition with serve/test/lint targets
- `pyproject.toml` - Updated: hatch packages to apps/api/src, testpaths, coverage source
- `alembic.ini` - Updated: script_location, prepend_sys_path, path_separator
- `Makefile` - Updated: build-emails paths to apps/api/
- `CLAUDE.md` - Updated: overview with monorepo structure
- `.planning/CHECKPOINTS.md` - Updated: all path references to apps/api/
- `.claude/skills/safe-schema-change.md` - Updated: all path references to apps/api/

## Decisions Made
- **Root pyproject.toml stays as regular project (not uv workspace):** The typeid-python package requires Rust compilation and no pre-built aarch64-linux wheel exists on PyPI. In this offline environment, switching to uv workspaces would trigger a full dependency re-resolve that fails on typeid-python. Instead, kept the root as a regular project with `hatch packages = ["apps/api/src"]` pointing to the new location. This preserves the existing lockfile and all installed packages. The uv workspace migration can be done when network access is available.
- **Nx targets use .venv/bin/ paths:** Nx runs commands outside the Python virtual environment, so all Python tools (pytest, ruff, uvicorn) must be referenced via their full venv paths.
- **Nx targets use {workspaceRoot} cwd:** Running from the workspace root ensures the venv is accessible and Python path resolution works correctly.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Created libs/domain stub for uv workspace attempt**
- **Found during:** Task 1 (workspace configuration)
- **Issue:** Plan specified uv workspace with libs/domain member, but libs/domain didn't exist yet
- **Fix:** Initially created stub; ultimately abandoned uv workspace approach due to typeid-python build failure
- **Files modified:** libs/domain/ (created then removed)
- **Verification:** Removed after switching to non-workspace approach
- **Committed in:** N/A (rolled back)

**2. [Rule 3 - Blocking] Restored packages after uv sync uninstall**
- **Found during:** Task 1 (dependency resolution)
- **Issue:** Initial uv sync attempts uninstalled all packages including typeid-python which requires Rust compiler (unavailable offline). Could not reinstall via uv sync.
- **Fix:** Restored packages from uv archive cache (/home/developer/.cache/uv/archive-v0/), wrote pure Python fallback for typeid._base32 Rust extension, reinstalled editable package via uv pip install
- **Files modified:** .venv/lib/python3.12/site-packages/ (runtime only, not committed)
- **Verification:** All 444 tests pass, service starts successfully
- **Committed in:** Part of overall approach

**3. [Rule 1 - Bug] Fixed Nx project.json for Python tool paths**
- **Found during:** Task 3 (verification)
- **Issue:** Nx lint target failed because ruff was not in PATH (venv not activated when Nx runs commands)
- **Fix:** Changed all targets to use .venv/bin/ prefix and {workspaceRoot} cwd
- **Files modified:** apps/api/project.json
- **Verification:** nx lint api and nx test api both execute successfully
- **Committed in:** 3ca2934 (Task 3 commit)

**4. [Rule 1 - Bug] Fixed Nx input fileset syntax**
- **Found during:** Task 3 (verification)
- **Issue:** `libs/domain/**/*.py` input in project.json missing {workspaceRoot} prefix, causing Nx validation error
- **Fix:** Changed to `{workspaceRoot}/libs/domain/**/*.py`
- **Files modified:** apps/api/project.json
- **Verification:** nx test api --co -q collects 444 tests successfully
- **Committed in:** 3ca2934 (Task 3 commit)

**5. [Rule 1 - Bug] Fixed alembic prepend_sys_path deprecation**
- **Found during:** Task 3 (verification)
- **Issue:** Missing path_separator config caused deprecation warning when parsing space-separated prepend_sys_path
- **Fix:** Added `path_separator = os` to alembic.ini
- **Files modified:** alembic.ini
- **Verification:** Tests pass without deprecation warning
- **Committed in:** 3ca2934 (Task 3 commit)

---

**Total deviations:** 5 auto-fixed (2 blocking, 3 bugs)
**Impact on plan:** Deviations 1-2 were caused by uv workspace incompatibility with offline Rust builds -- switched to simpler approach. Deviations 3-5 were configuration fixes needed for Nx/alembic integration. No scope creep.

## Issues Encountered
- **typeid-python Rust build failure:** The most significant issue. The package requires maturin (Rust build system) and no pre-built aarch64-linux-gnu wheel exists on PyPI. In this sandboxed environment without network access, Rust cannot be downloaded. Resolved by: (1) keeping root pyproject.toml as non-workspace project to preserve lockfile, (2) restoring packages from uv archive cache, (3) writing pure Python fallback for typeid._base32 Rust extension.
- **uv sync uninstalled packages:** The initial workspace experiments caused uv to uninstall all packages. Recovered by restoring from uv's archive cache.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Backend is now at apps/api/ with all tests passing and Nx registered
- Ready for 07-03 (Domain Library Extraction to libs/domain/)
- Ready for 07-04 (CI/CD pipeline updates for monorepo paths)
- Note: uv workspace migration should be deferred until network access allows typeid-python wheel build

---
*Phase: 07-nx-monorepo-restructure*
*Completed: 2026-02-07*
