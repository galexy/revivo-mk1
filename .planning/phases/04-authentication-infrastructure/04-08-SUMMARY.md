---
phase: 04-authentication-infrastructure
plan: 08
subsystem: testing
tags: [jwt, integration-tests, household-isolation, auth-fixtures, fastapi-testclient]

# Dependency graph
requires:
  - phase: 04-07
    provides: JWT-protected routes with household scoping
  - phase: 04-06
    provides: Auth API endpoints (register, verify, login, refresh)
provides:
  - All existing API integration tests updated to use real JWT auth flow
  - Household isolation tests verifying cross-household data access denied
  - household_id threading through category and transaction service layers (bug fix)
affects: [05-import-pipeline, 06-balance-calculation]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Auth fixture chain: test_user_data -> registered_user -> auth_tokens -> auth_headers"
    - "Household isolation test pattern: create resource as user A, verify user B gets 404"

key-files:
  created: []
  modified:
    - tests/integration/test_account_api.py
    - tests/integration/test_transaction_api.py
    - tests/integration/test_category_api.py
    - src/application/services/category_service.py
    - src/application/services/transaction_service.py
    - src/adapters/api/routes/categories.py
    - src/adapters/api/routes/transactions.py
    - src/domain/ports/category_repository.py
    - src/domain/ports/payee_repository.py
    - src/adapters/persistence/repositories/category.py
    - src/adapters/persistence/repositories/payee.py

key-decisions:
  - "Auth fixture chain per test file (not shared conftest) for test independence"
  - "Module-scoped DB setup with per-test client for isolation without overhead"
  - "Cross-household access returns 404 (not 403) consistent with route protection design"

patterns-established:
  - "Auth fixture chain: test_user_data -> registered_user (register+verify) -> auth_tokens (login) -> auth_headers (Bearer token dict)"
  - "Household isolation test: create second user with _create_second_user helper, verify 404 on cross-household access"

# Metrics
duration: 9min
completed: 2026-02-05
---

# Phase 4 Plan 8: Update Integration Tests for Auth Summary

**All 96 API integration tests migrated to real JWT auth flow with household isolation verification and household_id FK bug fix**

## Performance

- **Duration:** ~9 min
- **Started:** 2026-02-05T03:40:00Z
- **Completed:** 2026-02-05T03:49:01Z
- **Tasks:** 2
- **Files modified:** 11

## Accomplishments
- Migrated 22 account, 55 transaction, and 17 category API tests from placeholder user IDs to real JWT authentication (register -> verify email -> login -> use bearer token)
- Added 2 household isolation tests verifying cross-household account access returns 404 and listing returns empty
- Fixed critical bug: household_id was not threaded through category and transaction service layers, causing FK violations when creating categories/transactions with real auth (household_id from JWT didn't exist in households table because services defaulted to well-known placeholder)

## Task Commits

Each task was committed atomically:

1. **Task 1: Update existing integration tests to use auth_headers fixture** - `7e5cde8` (feat)
2. **Task 2: Add household isolation tests** - `d612ae8` (feat)

## Files Created/Modified
- `tests/integration/test_account_api.py` - Added auth fixture chain, auth_headers to all 22 tests, TestHouseholdIsolation class with 2 isolation tests
- `tests/integration/test_transaction_api.py` - Added auth fixture chain, auth_headers to all 55 tests
- `tests/integration/test_category_api.py` - Added auth fixture chain, auth_headers to all 17 tests
- `src/application/services/category_service.py` - Added household_id param to create_category(), ensure_system_categories(), delete_category()
- `src/application/services/transaction_service.py` - Added household_id param to create_transaction(), _get_or_create_payee()
- `src/adapters/api/routes/categories.py` - Pass current_user.household_id to service methods
- `src/adapters/api/routes/transactions.py` - Pass current_user.household_id to create_transaction()
- `src/domain/ports/category_repository.py` - Updated get_or_create_uncategorized signature with household_id
- `src/domain/ports/payee_repository.py` - Updated get_or_create signature with household_id
- `src/adapters/persistence/repositories/category.py` - Pass household_id to Category.create_system_category()
- `src/adapters/persistence/repositories/payee.py` - Pass household_id to Payee.create()

## Decisions Made
- Auth fixture chain defined per test file rather than in shared conftest.py for test module independence (each file can run standalone)
- Module-scoped database setup (create/drop tables once per module) with function-scoped TestClient for per-test app isolation
- Household isolation tests use helper method _create_second_user() that performs full register/verify/login flow inline

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] household_id not threaded through category/transaction service layers**
- **Found during:** Task 1 (updating transaction tests)
- **Issue:** After adding real JWT auth, creating categories and transactions failed with FK violation: `Key (household_id)=(hh_00000000000000000000000000) is not present in table "households"`. The category and transaction services never passed household_id from JWT claims to domain entity factory methods, so entities defaulted to the well-known placeholder household_id which doesn't exist as a real row in the households table (real users get real household rows created during registration).
- **Fix:** Added household_id parameter through the entire chain: API routes extract from CurrentUser -> services accept and pass to domain factory methods -> repository ports and implementations accept and pass to entity creation. Fixed in 8 source files.
- **Files modified:** src/application/services/category_service.py, src/application/services/transaction_service.py, src/adapters/api/routes/categories.py, src/adapters/api/routes/transactions.py, src/domain/ports/category_repository.py, src/domain/ports/payee_repository.py, src/adapters/persistence/repositories/category.py, src/adapters/persistence/repositories/payee.py
- **Verification:** All 55 transaction tests and 17 category tests pass with real auth
- **Committed in:** 7e5cde8 (part of Task 1 commit)

**2. [Rule 1 - Bug] Test file paths differ from plan specification**
- **Found during:** Task 1 (locating test files)
- **Issue:** Plan referenced `tests/integration/api/test_accounts.py` but files are at `tests/integration/test_account_api.py` (and similar for transactions/categories)
- **Fix:** Used actual file paths instead of plan paths
- **Files modified:** No extra files - just used correct paths
- **Verification:** All tests found and updated at correct paths

---

**Total deviations:** 2 auto-fixed (2 bugs)
**Impact on plan:** The household_id bug fix was essential for correctness - without it, no category or transaction could be created with real authentication. The file path deviation was trivial. No scope creep.

## Issues Encountered
- Pre-existing failures in `test_account_repository.py` (16 errors) and `test_database.py` (4 failures) due to users table schema changes (display_name NOT NULL) from auth migration. These are repository-level tests, not API integration tests, and were broken before this plan. Not in scope for 04-08.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Phase 4 (Authentication Infrastructure) is now complete with all 8 plans executed
- All 111 API integration tests pass with real JWT authentication (24 account + 55 transaction + 17 category + 15 auth)
- All 255 unit tests pass with no regressions
- Household isolation verified: cross-household access returns 404
- Pre-existing test_account_repository.py and test_database.py failures should be addressed in a future fix (they predate plan 04-08)
- Ready for Phase 5: Import Pipeline

---
*Phase: 04-authentication-infrastructure*
*Completed: 2026-02-05*
