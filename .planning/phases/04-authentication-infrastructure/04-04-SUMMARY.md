---
phase: 04-authentication-infrastructure
plan: 04
subsystem: database
tags: [sqlalchemy, orm, repository, refresh-token, sha256, unit-of-work]

# Dependency graph
requires:
  - phase: 04-01
    provides: "User and Household domain models with entity IDs"
  - phase: 04-02
    provides: "Auth services (JWT, password hashing) that will use repositories"
  - phase: 04-03
    provides: "Database tables (users, households, refresh_tokens) for persistence"
provides:
  - "UserRepository with ORM-based add/get_by_id/get_by_email/update"
  - "HouseholdRepository with ORM-based add/get_by_id/update"
  - "RefreshTokenRepository with SQLAlchemy Core (create/rotate/revoke/cleanup)"
  - "ORM mappers for User and Household entities"
  - "UnitOfWork integration with users, households, refresh_tokens properties"
affects:
  - "04-05 (auth service implementation needs repositories)"
  - "04-06 (registration TDD needs UserRepository and HouseholdRepository)"
  - "04-07 (login TDD needs UserRepository and RefreshTokenRepository)"
  - "04-08 (integration tests exercise full persistence stack)"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "SQLAlchemy Core for infrastructure records (RefreshTokenRepository)"
    - "SHA-256 token hashing for refresh token storage"
    - "Family-based token rotation with reuse detection"
    - "ORM mapper exclude_properties for transient _events list"

key-files:
  created:
    - "src/adapters/persistence/repositories/user.py"
    - "src/adapters/persistence/repositories/household.py"
    - "src/adapters/persistence/repositories/refresh_token.py"
    - "src/domain/ports/user_repository.py"
    - "src/domain/ports/household_repository.py"
  modified:
    - "src/adapters/persistence/orm/mappers.py"
    - "src/adapters/persistence/repositories/__init__.py"
    - "src/adapters/persistence/unit_of_work.py"
    - "src/domain/ports/unit_of_work.py"

key-decisions:
  - "Separate port files per entity (user_repository.py, household_repository.py) following existing project pattern"
  - "RefreshTokenRepository uses SQLAlchemy Core (not ORM) since tokens are infrastructure records"
  - "RefreshTokenRepository typed as Any in UoW port (avoids domain importing adapter types)"
  - "User._events excluded from ORM mapping, re-initialized in repository after load"
  - "Household mapped without exclude_properties (no transient fields)"

patterns-established:
  - "SQLAlchemy Core for non-aggregate infrastructure records"
  - "Token hashing with hashlib.sha256 for secure storage"
  - "Family-based rotation chain for refresh tokens"
  - "_ensure_events_list pattern in repository for transient field reconstruction"

# Metrics
duration: 4min
completed: 2026-02-05
---

# Phase 4 Plan 04: Auth Repositories Summary

**ORM mappers and repositories for User/Household/RefreshToken with SHA-256 token hashing and family-based rotation**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-05T03:06:34Z
- **Completed:** 2026-02-05T03:10:57Z
- **Tasks:** 3
- **Files modified:** 9

## Accomplishments
- User and Household ORM mappers registered with imperative mapping (User._events excluded)
- Three repositories implemented: UserRepository (ORM), HouseholdRepository (ORM), RefreshTokenRepository (SQLAlchemy Core)
- RefreshTokenRepository with create_token, validate_and_rotate (family rotation + reuse detection), revoke_all_for_user, revoke_family, cleanup_expired
- UnitOfWork integrated with lazy property access for all three new repositories
- Domain ports created for UserRepositoryProtocol and HouseholdRepositoryProtocol

## Task Commits

Each task was committed atomically:

1. **Task 1: Add ORM mappers for User and Household** - `23352c0` (feat)
2. **Task 2: Create repository ports and implementations** - `c68d42e` (feat)
3. **Task 3: Update UnitOfWork with new repositories** - `19ec4be` (feat)

## Files Created/Modified
- `src/adapters/persistence/orm/mappers.py` - Added Household and User imperative mappings
- `src/domain/ports/user_repository.py` - UserRepositoryProtocol port (add, get_by_id, get_by_email, update)
- `src/domain/ports/household_repository.py` - HouseholdRepositoryProtocol port (add, get_by_id, update)
- `src/adapters/persistence/repositories/user.py` - UserRepository with _events reconstruction on load
- `src/adapters/persistence/repositories/household.py` - HouseholdRepository with ORM-based persistence
- `src/adapters/persistence/repositories/refresh_token.py` - RefreshTokenRepository using SQLAlchemy Core with SHA-256 hashing
- `src/adapters/persistence/repositories/__init__.py` - Export new repositories
- `src/adapters/persistence/unit_of_work.py` - Added users, households, refresh_tokens lazy properties
- `src/domain/ports/unit_of_work.py` - Added users, households, refresh_tokens protocol properties

## Decisions Made
- Used separate port files per entity (user_repository.py, household_repository.py) instead of single repositories.py, matching existing project pattern (account_repository.py, category_repository.py, etc.)
- RefreshTokenRepository typed as `Any` in UoW protocol to avoid domain layer importing adapter types (refresh tokens are infrastructure records, not domain aggregates)
- Added `_ensure_events_list` helper in UserRepository to reconstruct transient `_events` field after ORM load

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Adapted port file structure to existing project pattern**
- **Found during:** Task 2 (Create repository ports)
- **Issue:** Plan specified single `src/domain/ports/repositories.py` file, but project uses individual files per entity (account_repository.py, category_repository.py, etc.)
- **Fix:** Created separate `user_repository.py` and `household_repository.py` in ports directory following existing convention
- **Files modified:** src/domain/ports/user_repository.py, src/domain/ports/household_repository.py
- **Verification:** Imports work correctly, matches project structure
- **Committed in:** c68d42e (Task 2 commit)

**2. [Rule 1 - Bug] Fixed F821 undefined name for RefreshTokenRepository in domain port**
- **Found during:** Task 3 (UnitOfWork update)
- **Issue:** String annotation `"RefreshTokenRepository"` in domain port caused ruff F821 since type doesn't exist in domain layer
- **Fix:** Changed to `Any` type with docstring explaining RefreshTokenRepository is infrastructure, not a domain protocol
- **Files modified:** src/domain/ports/unit_of_work.py
- **Verification:** ruff check passes on modified files (remaining errors are pre-existing)
- **Committed in:** 19ec4be (Task 3 commit)

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 bug)
**Impact on plan:** Both fixes necessary for project convention compliance and lint correctness. No scope creep.

## Issues Encountered
None - all tasks completed smoothly.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Repository layer complete for auth domain entities
- Ready for Phase 4 Plan 05 (auth service implementation using repositories)
- Ready for Phase 4 Plans 06-07 (TDD registration/login flows)
- Integration tests (Plan 08) can now exercise full persistence stack

---
*Phase: 04-authentication-infrastructure*
*Completed: 2026-02-05*
