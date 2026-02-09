---
phase: 08-ci-code-quality
plan: 01
subsystem: tooling
tags: [pyright, ruff, strict-typing, py.typed, linting]

# Dependency graph
requires:
  - phase: 07-nx-monorepo-restructure
    provides: Nx project structure with domain and api projects
provides:
  - Per-project pyrightconfig.json for api and domain (strict mode, includes tests)
  - PEP 561 py.typed marker for domain library
  - Zero pyright errors in domain (src + tests)
  - Zero ruff lint errors in domain
  - Ruff config with W rules, B008 immutable calls, SLF001 per-file-ignore
  - Pyright version pinned at 1.1.408
affects: [08-02 api pyright fixes, 08-03 CI pipeline, future domain consumers]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Per-project pyrightconfig.json for Nx monorepo (strict, project-specific includes)"
    - "Typed default_factory lambdas for pyright strict (lambda: list[T]() not bare list)"
    - "File-level pyright pragmas for untyped third-party libraries"
    - "from __future__ import annotations for forward-ref return types on frozen dataclasses"

key-files:
  created:
    - "apps/api/pyrightconfig.json"
    - "libs/domain/pyrightconfig.json"
    - "libs/domain/domain/py.typed"
  modified:
    - "pyproject.toml"
    - "libs/domain/domain/model/money.py"
    - "libs/domain/domain/model/rewards_balance.py"
    - "libs/domain/domain/model/entity_id.py"
    - "libs/domain/domain/model/user.py"
    - "libs/domain/domain/model/account.py"
    - "libs/domain/domain/model/category.py"
    - "libs/domain/domain/model/transaction.py"
    - "libs/domain/domain/ports/repository.py"
    - "libs/domain/domain/exceptions.py"
    - "libs/domain/domain/model/__init__.py"
    - "libs/domain/domain/events/account_events.py"
    - "libs/domain/domain/events/transaction_events.py"
    - "libs/domain/tests/unit/domain/test_split_line.py"
    - "libs/domain/tests/unit/domain/test_account.py"
    - "libs/domain/tests/unit/domain/test_entity_id.py"
    - "libs/domain/tests/unit/domain/test_money.py"
    - "libs/domain/tests/unit/domain/test_rewards_balance.py"
    - "libs/domain/tests/unit/domain/test_institution.py"
    - "libs/domain/tests/unit/domain/test_account_types.py"
    - "libs/domain/tests/unit/domain/test_user.py"
    - "libs/domain/tests/unit/domain/test_household.py"
    - "apps/api/project.json"
    - "libs/domain/project.json"

key-decisions:
  - "Use from __future__ import annotations + concrete return types instead of Self for frozen dataclass arithmetic (Self requires cls() calls, not explicit type constructors)"
  - "File-level pyright pragma for entity_id.py to handle untyped typeid library (reportUnknownMemberType=false, reportUnknownVariableType=false)"
  - "Rename DomainException to DomainError (N818 naming convention, not used outside domain)"
  - "Typed default_factory: lambda: list[T]() instead of bare list for pyright strict mode"
  - "Per-project pyrightconfig.json includes tests (catches type errors in test code too)"

patterns-established:
  - "Per-project pyrightconfig.json: Each Nx project has own config, pyright command uses it automatically"
  - "Typed default_factory: Always use lambda: list[Type]() for dataclass fields in strict mode"
  - "Raw match strings: Use r-prefix for pytest.raises match= patterns containing regex metacharacters"
  - "Narrow-scope pytest.raises: Always provide match= parameter for specific error messages"

# Metrics
duration: 10min
completed: 2026-02-09
---

# Phase 08 Plan 01: Tooling & Domain Cleanup Summary

**Per-project pyrightconfig.json (strict + tests), py.typed marker, ruff W/B008/SLF001 config, and 53+ domain pyright+lint errors fixed to zero**

## Performance

- **Duration:** 10 min
- **Started:** 2026-02-09T06:29:09Z
- **Completed:** 2026-02-09T06:39:09Z
- **Tasks:** 2
- **Files modified:** 33 (task 1) + 21 (task 2) = 54 total changes

## Accomplishments
- Created per-project pyrightconfig.json for both api and domain with strict mode including tests
- Fixed 52 pyright errors in domain (20 original src errors + 32 new test errors from including tests in typecheck scope)
- Fixed 33 ruff lint errors in domain (PIE790, I001, F401, RUF043, PT011, RUF022, N818)
- Auto-formatted 26 files across the entire workspace
- Added PEP 561 py.typed marker for domain library
- Pinned pyright version at 1.1.408
- Updated ruff config with W rules, B008 immutable calls, SLF001 per-file-ignore

## Task Commits

Each task was committed atomically:

1. **Task 1: Tooling configuration and auto-format** - `ac20ae6` (chore)
2. **Task 2: Fix all domain pyright and lint errors** - `c8e4953` (fix)

## Files Created/Modified

### Created
- `apps/api/pyrightconfig.json` - Per-project pyright config (strict, src+tests)
- `libs/domain/pyrightconfig.json` - Per-project pyright config (strict, domain+tests)
- `libs/domain/domain/py.typed` - PEP 561 typed package marker

### Modified (key changes)
- `pyproject.toml` - Pinned pyright==1.1.408, added W/B008/SLF001 ruff config
- `libs/domain/domain/model/money.py` - Replace Self with Money return types, use __future__ annotations
- `libs/domain/domain/model/rewards_balance.py` - Replace Self with RewardsBalance return types
- `libs/domain/domain/model/entity_id.py` - Pyright pragma for untyped typeid, typed TypeID.from_string calls
- `libs/domain/domain/model/user.py` - Type _events as list[Any], typed default_factory
- `libs/domain/domain/model/account.py` - Typed default_factory for _events
- `libs/domain/domain/model/category.py` - Typed default_factory for _events
- `libs/domain/domain/model/transaction.py` - Typed default_factory for splits and _events
- `libs/domain/domain/ports/repository.py` - ID TypeVar contravariant
- `libs/domain/domain/exceptions.py` - Rename DomainException to DomainError
- `libs/domain/domain/model/__init__.py` - Sort __all__ alphabetically
- `libs/domain/domain/events/*.py` - Remove unnecessary pass statements
- `libs/domain/tests/**/*.py` - Fix type errors, raw match strings, narrow pytest.raises
- `apps/api/project.json` - Typecheck command uses pyrightconfig.json
- `libs/domain/project.json` - Typecheck command uses pyrightconfig.json

## Decisions Made

1. **from __future__ import annotations for frozen dataclasses:** Money and RewardsBalance use `frozen=True, slots=True` and construct new instances via explicit class name (not cls()), making Self incorrect. Using `from __future__ import annotations` enables forward-reference return types cleanly.

2. **File-level pyright pragma for entity_id.py:** The typeid library ships no type stubs. Rather than adding per-line ignores on every TypeID.from_string() call (9 occurrences), a single file-level pragma suppresses Unknown type propagation.

3. **Rename DomainException to DomainError:** N818 requires exception names to end in "Error". The class is only referenced within domain (parent of EntityNotFoundError, ValidationError, BusinessRuleViolationError) so renaming is safe.

4. **Typed default_factory pattern:** Pyright strict infers `field(default_factory=list)` as `list[Unknown]` even with explicit type annotations. Using `lambda: list[DomainEvent]()` provides the type parameter at the expression level.

5. **Include tests in pyright scope:** Per-project pyrightconfig.json includes both source and tests. This caught 32 additional type errors that were invisible before (test_split_line passing strings to Decimal, test_account accessing Optional without guard, etc.).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Fixed 32 additional pyright errors from test inclusion**
- **Found during:** Task 2
- **Issue:** Plan estimated 20 pyright errors, but including tests in typecheck scope (via pyrightconfig.json) revealed 32 additional errors: untyped TypeID library propagation, untyped list default factories, and test code type mismatches
- **Fix:** Added pyright pragma for entity_id.py, typed default_factory lambdas in account/category/transaction/user models, fixed test type annotations
- **Files modified:** entity_id.py, account.py, category.py, transaction.py, user.py
- **Verification:** `npx nx typecheck domain` passes with 0 errors
- **Committed in:** c8e4953 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (missing critical - additional type errors from expanded scope)
**Impact on plan:** Necessary for correctness. The expanded typecheck scope (including tests) caught errors that would have persisted invisibly. No scope creep.

## Issues Encountered
None - all errors had straightforward fixes.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Domain project has zero pyright strict errors (source + tests)
- Domain project has zero ruff lint errors
- All 192 domain tests pass
- Per-project pyrightconfig.json ready for api project (08-02 will fix api errors)
- Ruff config has B008 immutable calls ready for api Depends() patterns
- SLF001 per-file-ignore ready for persistence adapter layer

---
*Phase: 08-ci-code-quality*
*Completed: 2026-02-09*
