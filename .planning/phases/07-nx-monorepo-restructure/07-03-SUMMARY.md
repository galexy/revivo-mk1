---
phase: 07-nx-monorepo-restructure
plan: 03
subsystem: domain
tags: [monorepo, domain-extraction, shared-library, import-rewrite, nx]

# Dependency graph
requires:
  - phase: 07-02
    provides: Backend at apps/api/ with editable install via hatch packages
provides:
  - Domain layer as standalone shared library at libs/domain/
  - All imports use domain.* (not src.domain.*)
  - libs/domain/project.json with Nx test/lint targets
  - import-linter contracts updated for extracted domain package
affects: [07-04, all-future-phases-importing-domain-code]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Shared domain library at libs/domain/domain/ importable via hatch packages"
    - "Editable install: packages=['apps/api/src', 'libs/domain/domain'] in root pyproject.toml"
    - "pytest --import-mode=importlib for multi-testpath monorepo test discovery"
    - "import-linter root_packages=['src', 'domain'] for cross-package architecture enforcement"

key-files:
  created:
    - libs/domain/pyproject.toml
    - libs/domain/project.json
    - libs/domain/tests/__init__.py
    - libs/domain/tests/unit/__init__.py
  modified:
    - pyproject.toml
    - "61 Python files (import rewrite from src.domain.* to domain.*)"
  moved:
    - "apps/api/src/domain/ -> libs/domain/domain/ (git mv, history preserved)"
    - "apps/api/tests/unit/domain/ -> libs/domain/tests/unit/domain/ (git mv)"

# Decisions
decisions:
  - id: domain-hatch-packages-path
    decision: "Use 'libs/domain/domain' (not 'libs/domain') in hatch packages list"
    rationale: "Hatch adds parent directory to sys.path; libs/domain/domain means Python finds domain/ package at libs/domain/ level"
  - id: pytest-importlib-mode
    decision: "Add --import-mode=importlib to pytest configuration"
    rationale: "Both apps/api/tests/ and libs/domain/tests/ have tests/__init__.py creating module name collision in default pytest import mode"
  - id: import-linter-dual-root
    decision: "Set root_packages=['src', 'domain'] for import-linter"
    rationale: "Domain is now a separate top-level package, not nested under src; both need to be roots for architecture enforcement"
  - id: editable-install-no-deps
    decision: "Use uv pip install -e . --no-deps to update editable install"
    rationale: "uv pip install -e . (with deps) triggers typeid-python Rust rebuild which fails in offline environment; --no-deps skips this"

# Metrics
metrics:
  duration: "10 min"
  completed: "2026-02-07"
  tests: 444
  files_changed: 108
---

# Phase 7 Plan 3: Domain Layer Extraction Summary

**Domain layer extracted from apps/api/src/domain/ to libs/domain/domain/ as standalone shared library with all 444 tests passing**

## What Was Done

### Task 1: Extract domain layer to libs/domain/
- Used `git mv` to move `apps/api/src/domain/` to `libs/domain/domain/` (preserves full git history)
- Used `git mv` to move domain unit tests from `apps/api/tests/unit/domain/` to `libs/domain/tests/unit/domain/`
- Created `libs/domain/pyproject.toml` with minimal dependencies (typeid-python, returns only -- no infrastructure deps)
- Created `libs/domain/project.json` registering domain as Nx library with test and lint targets
- Updated root `pyproject.toml`:
  - hatch packages: added `libs/domain/domain` for editable install
  - pytest testpaths: added `libs/domain/tests`
  - coverage source: added `libs/domain/domain`
- Used `uv pip install -e . --no-deps` to update editable install without triggering typeid-python rebuild

### Task 2: Rewrite all imports from src.domain.* to domain.*
- Replaced `from src.domain.` with `from domain.` across 61 Python files
- Updated import-linter configuration:
  - `root_packages = ["src", "domain"]` (was `["src"]`)
  - Forbidden contract source: `domain` (was `src.domain`)
  - Layers contract bottom layer: `domain` (was `src.domain`)
- Zero remaining occurrences of `src.domain` in active Python code
- Verified domain package resolves: `python -c "from domain.model.money import Money"` works

### Task 3: Verify all tests pass with extracted domain
- 192 domain unit tests pass (`libs/domain/tests/`)
- 252 API tests pass (`apps/api/tests/`)
- 444 total tests pass when run together
- import-linter: 2 contracts kept, 0 broken
- `npx nx test domain` succeeds
- `npx nx test api` succeeds
- `alembic upgrade head` applies cleanly
- `alembic check` shows no drift

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed hatch packages path for domain**
- **Found during:** Task 1
- **Issue:** `packages = ["libs/domain"]` caused Python to find `libs/domain/` as `domain` package (a directory containing a `domain/` subdirectory), not `libs/domain/domain/` as the actual domain package
- **Fix:** Changed to `packages = ["libs/domain/domain"]` so hatch adds `libs/domain` to sys.path, making `domain/` (the actual package) importable
- **Files modified:** pyproject.toml
- **Commit:** c7baa3f

**2. [Rule 3 - Blocking] Recovered from uv pip install -e . failure**
- **Found during:** Task 1
- **Issue:** Initial `uv pip install -e .` (without --no-deps) triggered typeid-python Rust rebuild which failed due to no network. This uninstalled the existing editable package
- **Fix:** Used `uv pip install -e . --no-deps --python .venv/bin/python` to install editable package in venv without resolving dependencies
- **Files modified:** None (runtime fix)
- **Commit:** N/A (runtime operation)

**3. [Rule 3 - Blocking] Fixed pytest test collection conflict**
- **Found during:** Task 3
- **Issue:** Both `apps/api/tests/` and `libs/domain/tests/` have `tests/__init__.py`, causing module name collision when pytest tries to import `tests.unit.domain.test_account` from both locations
- **Fix:** Added `--import-mode=importlib` to pytest addopts configuration
- **Files modified:** pyproject.toml
- **Commit:** b5fca35

## Verification Results

| Check | Result |
|-------|--------|
| Domain files at libs/domain/domain/ | Pass |
| Domain tests at libs/domain/tests/ | Pass |
| No src.domain references in Python files | Pass (0 occurrences) |
| `import domain` resolves to libs/domain/domain/ | Pass |
| `from domain.model.money import Money` works | Pass |
| 444 tests pass | Pass (252 API + 192 domain) |
| import-linter: architecture contracts | Pass (2 kept, 0 broken) |
| Nx test domain | Pass |
| Nx test api | Pass |
| alembic upgrade head | Pass |
| alembic check | Pass (no drift) |

## Commits

| # | Hash | Message |
|---|------|---------|
| 1 | c7baa3f | feat(07-03): extract domain layer to libs/domain/ |
| 2 | 1fc9c71 | refactor(07-03): rewrite all imports from src.domain.* to domain.* |
| 3 | b5fca35 | fix(07-03): add pytest importlib mode for monorepo test discovery |

## Next Phase Readiness

Domain extraction is complete. The domain layer is now a standalone shared library that:
- Can be imported by any app (API, future CLI, etc.) via `from domain.model.money import Money`
- Has its own Nx test and lint targets for independent validation
- Enforces zero infrastructure dependencies via import-linter
- Has full git history preserved via `git mv`

Ready for 07-04 (CI Pipeline Configuration).
