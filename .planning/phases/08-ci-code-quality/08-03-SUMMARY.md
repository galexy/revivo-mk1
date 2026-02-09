---
phase: 08-ci-code-quality
plan: 03
subsystem: api
tags: [ruff, linting, code-quality, imports, datetime]

# Dependency graph
requires:
  - phase: 08-02
    provides: Zero pyright strict errors in API project
  - phase: 08-01
    provides: Ruff config with select rules, B008/SLF001 ignores, isort known-first-party
provides:
  - Zero ruff lint errors in API project (src + tests)
  - Per-file-ignores for ARG in routes, persistence, and tests
  - All relative imports converted to absolute imports
  - All datetime.date.today() calls replaced with timezone-aware alternatives
affects: [08-04]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Per-file-ignores for framework-required unused args (FastAPI routes, SQLAlchemy TypeDecorator)"
    - "datetime.now(UTC).date() for timezone-aware date creation"
    - "Absolute imports (from src.adapters...) in all route files"
    - "contextlib.suppress instead of try/except/pass"
    - "Exception chaining (raise ... from e) in all except blocks"

key-files:
  created: []
  modified:
    - pyproject.toml
    - apps/api/src/adapters/api/routes/accounts.py
    - apps/api/src/adapters/api/routes/auth.py
    - apps/api/src/adapters/api/routes/health.py
    - apps/api/src/adapters/api/routes/transactions.py
    - apps/api/src/adapters/api/routes/categories.py
    - apps/api/src/adapters/persistence/orm/mappers.py
    - apps/api/src/adapters/persistence/unit_of_work.py
    - apps/api/src/application/services/transaction_service.py
    - apps/api/tests/integration/test_transaction_api.py
    - apps/api/tests/integration/test_database.py
    - apps/api/tests/integration/conftest.py

key-decisions:
  - "Per-file-ignores for ARG001/ARG002 in routes, persistence, and tests (framework-required params cannot be renamed)"
  - "noqa: PT012 for multi-statement pytest.raises where IntegrityError can occur on either execute or commit"
  - "TYPE_CHECKING block for Session/sessionmaker/DomainEvent in unit_of_work.py (already has __future__ annotations)"

patterns-established:
  - "Per-file-ignores over noqa comments for systematic framework noise (ARG in routes, SLF in tests)"
  - "datetime.now(UTC).date() as standard pattern for timezone-aware date creation"
  - "Absolute imports only in src/ (no relative parent imports)"

# Metrics
duration: 16min
completed: 2026-02-09
---

# Phase 8 Plan 3: Fix API Ruff Lint Errors Summary

**Zero ruff lint errors in API project via auto-fix, per-file-ignores for framework patterns, absolute imports, timezone-aware dates, and exception chaining**

## Performance

- **Duration:** 16 min
- **Started:** 2026-02-09T07:00:56Z
- **Completed:** 2026-02-09T07:17:46Z
- **Tasks:** 2
- **Files modified:** 40

## Accomplishments
- Reduced API ruff lint errors from 173 to 0 across 13 error categories
- Converted all 19 relative imports in routes/ to absolute imports (TID252)
- Replaced 47 `date.today()` calls with timezone-aware `datetime.now(UTC).date()` (DTZ011)
- Added exception chaining to 7 raise-in-except blocks (B904)
- All 252 API tests pass, pyright typecheck still at 0 errors

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix auto-fixable and configuration-fixable lint errors** - `4773a45` (fix)
2. **Task 2: Fix remaining manual lint errors** - `b9acdba` (fix)

## Files Created/Modified

### Task 1: Auto-fix and Configuration (31 files)
- `pyproject.toml` - Added per-file-ignores for ARG001/ARG002 in routes, persistence, tests; SLF001 in tests
- `apps/api/tests/integration/test_transaction_api.py` - Replaced 47 date.today() with datetime.now(UTC).date()
- 29 other files across src/ and tests/ - Import sorting (I001), unused imports (F401), __all__ sorting (RUF022)

### Task 2: Manual Fixes (9 files)
- `apps/api/src/adapters/api/routes/accounts.py` - Absolute imports, exception chaining (from e)
- `apps/api/src/adapters/api/routes/auth.py` - Absolute imports (..dependencies -> src.adapters.api.dependencies)
- `apps/api/src/adapters/api/routes/health.py` - Absolute import for get_settings
- `apps/api/src/adapters/api/routes/transactions.py` - Exception chaining (from e)
- `apps/api/src/adapters/persistence/orm/mappers.py` - contextlib.suppress instead of try/except/pass
- `apps/api/src/adapters/persistence/unit_of_work.py` - Moved Session/sessionmaker/DomainEvent to TYPE_CHECKING
- `apps/api/src/application/services/transaction_service.py` - Collapsed nested if (SIM102)
- `apps/api/tests/integration/conftest.py` - Renamed Session -> test_session_factory (N806)
- `apps/api/tests/integration/test_database.py` - Added noqa: PT012 for multi-statement pytest.raises

## Decisions Made

1. **Per-file-ignores for framework-required unused args** - FastAPI route handlers have dependency-injected parameters (current_user, request) that are required by the framework but appear unused in the function body. SQLAlchemy TypeDecorator methods require `dialect` parameter by interface contract. Per-file-ignores are the pragmatic solution over hundreds of noqa comments.

2. **noqa: PT012 for pytest.raises with execute+commit** - SQLAlchemy IntegrityError can be raised during either execute() or commit() depending on the driver's flush behavior. Both statements must be inside pytest.raises. This is a legitimate multi-statement pattern.

3. **TYPE_CHECKING for Session/sessionmaker/DomainEvent** - unit_of_work.py already has `from __future__ import annotations`, so all annotations are lazy strings at runtime. Moving these to TYPE_CHECKING is correct and eliminates TC001/TC002 warnings.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] PT012 fix caused test failures, reverted to noqa approach**
- **Found during:** Task 2 (PT012 fix)
- **Issue:** Moving session.execute() outside pytest.raises caused IntegrityError during execute (not commit) because psycopg2 raises eagerly on constraint violations
- **Fix:** Reverted to original multi-statement pytest.raises with noqa: PT012 comment
- **Files modified:** apps/api/tests/integration/test_database.py
- **Verification:** All 252 tests pass
- **Committed in:** b9acdba (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Minor - the initial PT012 approach was incorrect for this driver behavior. noqa: PT012 is the correct solution.

## Issues Encountered

- **psycopg2 eager constraint checking**: Initially tried to split `execute()` and `commit()` to satisfy PT012. But psycopg2 raises IntegrityError during execute() for unique constraint violations (not deferred to commit). Both statements must be in the pytest.raises block, requiring noqa: PT012.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- API project has zero ruff lint errors, ready for CI gate in plan 08-04
- All 252 API tests pass
- Pyright typecheck still at 0 errors
- No relative imports remain in src/
- No timezone-naive date calls remain
- No blockers for plan 08-04 (CI pipeline configuration)

---
*Phase: 08-ci-code-quality*
*Completed: 2026-02-09*
