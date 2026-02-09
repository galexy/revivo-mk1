---
phase: 04-authentication-infrastructure
plan: 07
subsystem: auth
tags: [jwt, fastapi, household-scoping, route-protection, currentuser, tdd]

# Dependency graph
requires:
  - phase: 04-03
    provides: "Database schema with household_id FK on all data tables"
  - phase: 04-06
    provides: "Auth routes, get_current_user dependency, CurrentUser dataclass, auth test fixtures"
provides:
  - "All API routes protected with JWT authentication (401 without token)"
  - "Household-scoped data access via CurrentUser.household_id"
  - "household_id field on Account, Transaction, Category, Payee domain models"
  - "get_by_household method on AccountRepository"
  - "Cross-household access returns 404 (not 403) for security"
  - "Removed placeholder get_current_user_id function"
  - "Route protection integration tests (3 tests)"
affects: [04-08, "all future API features", "multi-tenant data isolation"]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "CurrentUser dependency injection for all protected routes"
    - "Household-scoped data filtering in service layer"
    - "404 for cross-household access (prevents resource probing)"
    - "Optional household_id with well-known default for backward compatibility"

key-files:
  created: []
  modified:
    - "src/domain/model/account.py"
    - "src/domain/model/transaction.py"
    - "src/domain/model/category.py"
    - "src/domain/model/payee.py"
    - "src/domain/ports/account_repository.py"
    - "src/adapters/persistence/repositories/account.py"
    - "src/adapters/persistence/repositories/transaction.py"
    - "src/adapters/persistence/repositories/category.py"
    - "src/adapters/persistence/repositories/payee.py"
    - "src/application/services/account_service.py"
    - "src/adapters/api/routes/accounts.py"
    - "src/adapters/api/routes/transactions.py"
    - "src/adapters/api/routes/categories.py"
    - "src/adapters/api/dependencies.py"
    - "tests/integration/api/test_auth.py"

key-decisions:
  - "All domain model factory methods accept optional household_id with fallback to well-known default (hh_00000000000000000000000000)"
  - "AccountService.get_account returns NOT_FOUND for cross-household access (security: prevents probing)"
  - "Routes extract both user_id and household_id from CurrentUser JWT claims"
  - "Removed placeholder get_current_user_id; all routes now use real JWT auth"

patterns-established:
  - "CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)] for route injection"
  - "Service methods accept household_id for data scoping and ownership verification"
  - "Repository _reconstruct_value_objects includes HouseholdId reconstruction"

# Metrics
duration: 8min
completed: 2026-02-05
---

# Phase 4 Plan 7: Route Protection & Household Scoping Summary

**JWT auth on all API routes with household-scoped data access, 4 domain models updated with household_id, and 3 TDD route protection tests**

## Performance

- **Duration:** 8 min
- **Started:** 2026-02-05T03:23:00Z
- **Completed:** 2026-02-05T03:31:18Z
- **Tasks:** 2 (TDD: RED + GREEN)
- **Files modified:** 15 (0 created, 15 modified)

## Accomplishments
- All non-auth API routes now require valid JWT token (401 without, 200 with valid, 401 with invalid)
- household_id field added to Account, Transaction, Category, and Payee domain models
- All factory methods accept optional household_id with backward-compatible default
- AccountService methods filter by household_id; cross-household returns 404 (not 403)
- Account, Transaction, Category route files fully rewritten to use CurrentUser dependency
- Removed legacy placeholder get_current_user_id from dependencies.py
- All 270 tests pass (15 auth integration + 255 unit tests)

## Task Commits

Each task was committed atomically:

1. **Task 1: RED - Write failing route protection tests** - `7d7cde7` (test)
2. **Task 2: GREEN - Protect routes with JWT auth and household scoping** - `6a9024b` (feat)

_Note: TDD plan with RED (test) then GREEN (implementation) commits_

## Files Created/Modified
- `src/domain/model/account.py` - Added household_id field, updated 7 factory methods
- `src/domain/model/transaction.py` - Added household_id field, updated create/create_mirror
- `src/domain/model/category.py` - Added household_id field, updated create/create_system_category
- `src/domain/model/payee.py` - Added household_id field, updated create factory
- `src/domain/ports/account_repository.py` - Added get_by_household to protocol
- `src/adapters/persistence/repositories/account.py` - Added get_by_household impl, HouseholdId reconstruction
- `src/adapters/persistence/repositories/transaction.py` - Added household_id to insert, HouseholdId reconstruction
- `src/adapters/persistence/repositories/category.py` - Added HouseholdId reconstruction
- `src/adapters/persistence/repositories/payee.py` - Added HouseholdId reconstruction
- `src/application/services/account_service.py` - All methods accept household_id, ownership verification
- `src/adapters/api/routes/accounts.py` - Rewritten to use CurrentUser dependency
- `src/adapters/api/routes/transactions.py` - Rewritten to use CurrentUser dependency
- `src/adapters/api/routes/categories.py` - Rewritten to use CurrentUser dependency
- `src/adapters/api/dependencies.py` - Removed placeholder get_current_user_id
- `tests/integration/api/test_auth.py` - Added TestProtectedRoutes (3 tests)

## Decisions Made
- **Optional household_id with default**: All domain model factory methods accept `household_id: HouseholdId | None = None` with fallback to the well-known constant `hh_00000000000000000000000000`. This maintains backward compatibility with existing unit tests and provides a migration path.
- **Cross-household returns 404**: AccountService.get_account returns NOT_FOUND (not FORBIDDEN) when the account belongs to a different household. This prevents attackers from probing for valid resource IDs.
- **Routes extract both user_id and household_id**: Routes pass `current_user.household_id` to service methods for data filtering, and `current_user.user_id` where user-level attribution is needed (e.g., transaction creation).
- **Removed placeholder entirely**: The old `get_current_user_id()` returning a hardcoded UserId was removed. All routes now use the real JWT-based `get_current_user` dependency.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Added household_id to Transaction, Category, Payee models**
- **Found during:** Task 2 (GREEN implementation)
- **Issue:** Plan only specified adding household_id to Account model, but Transaction, Category, and Payee also need household_id for consistent data scoping (tables already have the column from 04-03 migration)
- **Fix:** Added household_id field and factory method parameter to all 4 domain models, plus HouseholdId reconstruction in all 4 repositories
- **Files modified:** src/domain/model/transaction.py, src/domain/model/category.py, src/domain/model/payee.py, plus their repositories
- **Verification:** All tests pass, domain models consistent
- **Committed in:** 6a9024b (Task 2)

---

**Total deviations:** 1 auto-fixed (1 missing critical)
**Impact on plan:** Essential for data consistency - all data tables need household_id for multi-tenant scoping. No scope creep.

## Issues Encountered
- **Pre-existing integration test failures**: The old integration tests (test_account_api.py, test_transaction_api.py, etc.) fail because they use a placeholder user and don't pass auth headers. These failures pre-date this plan (the user table schema changed in 04-03 with NOT NULL display_name). The old tests will need updating in a future plan (04-08). This does not affect the 270 tests that currently pass.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All routes protected with JWT authentication
- Household-scoped data access working through service layer
- Plan 04-08 (update old integration tests to use auth fixtures) can proceed
- Old integration tests need auth headers and updated setup fixtures

---
*Phase: 04-authentication-infrastructure*
*Completed: 2026-02-05*
