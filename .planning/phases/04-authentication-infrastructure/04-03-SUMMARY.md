---
phase: 04-authentication-infrastructure
plan: 03
subsystem: database
tags: [alembic, migration, households, auth-tables, refresh-tokens, household-scoping]

# Dependency graph
requires:
  - phase: 04-01
    provides: HouseholdId entity ID in domain model
  - phase: 03-transaction-domain
    provides: Existing tables (accounts, transactions, categories, payees)
provides:
  - households table for multi-user data scoping
  - Expanded users table with auth fields (password_hash, display_name, household_id)
  - refresh_tokens table for JWT token rotation
  - household_id column on all user-owned data tables
  - HouseholdIdType SQLAlchemy type decorator
  - Default household with well-known ID for data migration
affects: [04-04, 04-05, 04-06, 04-07, 04-08]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Circular FK bootstrap: create table with nullable FK, migrate data, add NOT NULL + FK constraint"
    - "Well-known ID constant for default/system records (hh_00000000000000000000000000)"
    - "Household-scoped data model: all user-owned tables have household_id FK"

key-files:
  created:
    - alembic/versions/006_add_auth_tables.py
  modified:
    - src/adapters/persistence/orm/types.py
    - src/adapters/persistence/orm/tables.py

key-decisions:
  - "Default household ID is well-known constant hh_00000000000000000000000000 (valid TypeID)"
  - "Circular FK bootstrap: households.owner_id created nullable, populated, then NOT NULL"
  - "Existing users get display_name from email prefix and placeholder password_hash"
  - "household_id is NOT NULL FK on accounts, transactions, categories, payees"

patterns-established:
  - "HouseholdIdType TypeDecorator: converts HouseholdId <-> String for database storage"
  - "All user-owned data tables include household_id for tenant scoping"

# Metrics
duration: 7min
completed: 2026-02-05
---

# Phase 4 Plan 3: Database Tables & Migration Summary

**Alembic migration 006 adding households table, auth columns on users, refresh_tokens table, and household_id scoping on all data tables**

## Performance

- **Duration:** 7 min
- **Started:** 2026-02-05T02:55:47Z
- **Completed:** 2026-02-05T03:03:02Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments
- Created households table with owner_id FK to users (circular dependency handled via deferred constraints)
- Expanded users table with display_name, password_hash, household_id, email_verified_at for authentication
- Created refresh_tokens table with token_hash, token_family for JWT rotation/revocation
- Added household_id to accounts, transactions, categories, and payees tables
- Migrated all existing data (5 accounts, 21 transactions, 11 categories, 5 payees, 2 users) to Default household
- Round-trip migration (downgrade + upgrade) verified working

## Task Commits

Each task was committed atomically:

1. **Task 1: Add HouseholdIdType to ORM types** - `a234b3d` (feat)
2. **Task 2: Update tables.py with auth tables and household columns** - `6b02ff3` (feat)
3. **Task 3: Create Alembic migration 006** - `d73ae4a` (feat)

## Files Created/Modified
- `src/adapters/persistence/orm/types.py` - Added HouseholdIdType TypeDecorator for HouseholdId <-> String conversion
- `src/adapters/persistence/orm/tables.py` - Added households, refresh_tokens tables; expanded users; added household_id to data tables
- `alembic/versions/006_add_auth_tables.py` - Migration 006 with data migration for Default household

## Decisions Made
- Default household ID is `hh_00000000000000000000000000` (well-known constant, valid TypeID with all-zero suffix)
- Circular FK bootstrap solved by creating households.owner_id as nullable first, then adding NOT NULL after data migration
- Existing users get display_name derived from email prefix (split on @) and a placeholder password_hash
- households.owner_id FK deferred in table definition (comment notes "FK added after users table") to handle SQLAlchemy metadata ordering

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Cleaned stale database schema from previous migration attempts**
- **Found during:** Task 3 (migration creation)
- **Issue:** Database had stale tables (auth_methods, api_keys) and columns (display_name, role, token_version on users) from abandoned previous execution, plus alembic_version stamped at revision 007 which didn't exist
- **Fix:** Dropped stale tables and columns, reset alembic_version to 005, cleaned both main and test databases
- **Files modified:** None (database-only cleanup)
- **Verification:** `alembic current` shows 005 (head), clean migration to 006 succeeds
- **Committed in:** Part of migration development, not separately committed

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Database cleanup was necessary to restore clean state before migration. No scope creep.

## Issues Encountered
- Database had leftover schema from previous plan execution attempts that needed cleanup before migration 006 could be created cleanly
- Existing integration tests will fail until domain models and service layer are updated with household_id (planned for 04-07/04-08)

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Database schema is complete for authentication infrastructure
- Plan 04-04 (repositories and UoW) can proceed: tables exist for User, Household, RefreshToken persistence
- Plan 04-07 will need to update domain models (Account, Category, Payee, Transaction) with household_id
- Plan 04-08 will update existing E2E tests to use real auth flow with household scoping
- Note: Integration tests are expected to fail between 04-03 and 04-07/04-08 due to NOT NULL household_id on tables without matching domain model updates

---
*Phase: 04-authentication-infrastructure*
*Completed: 2026-02-05*
