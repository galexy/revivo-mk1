---
phase: 10-value-object-orm-mapping
plan: 01
subsystem: database
tags: [sqlalchemy, composite, orm, value-objects, money, domain-model]

# Dependency graph
requires:
  - phase: 09-type-safety-test-cleanup
    provides: Clean pyright strict mode baseline
provides:
  - SQLAlchemy composite() mappings for Money, InstitutionDetails, RewardsBalance
  - Factory functions for nullable composite handling
  - Eliminated manual value object decomposition/reconstruction
affects: [future-orm-changes, value-object-additions]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "SQLAlchemy composite() for value object ORM mapping"
    - "Factory functions for nullable composites (return None when all columns NULL)"

key-files:
  created: []
  modified:
    - libs/domain/domain/model/money.py
    - libs/domain/domain/model/institution.py
    - libs/domain/domain/model/rewards_balance.py
    - apps/api/src/adapters/persistence/orm/mappers.py
    - apps/api/src/adapters/persistence/repositories/account.py

key-decisions:
  - "Use composite() with factory functions instead of direct class constructors to handle nullable composites"
  - "Keep EntityId/Enum reconstruction in repository (TypeDecorators return strings, not domain types)"

patterns-established:
  - "Value objects implement __composite_values__() for SQLAlchemy composite() support"
  - "Nullable composites use factory functions that return None when all component columns are NULL"

# Metrics
duration: 6min
completed: 2026-02-09
---

# Phase 10 Plan 01: Value Object ORM Mapping Summary

**SQLAlchemy composite() replaces manual value object decomposition/reconstruction, eliminating 153 lines of fragile event handler and repository code plus 18 type: ignore comments**

## Performance

- **Duration:** 6 min
- **Started:** 2026-02-09T19:36:49Z
- **Completed:** 2026-02-09T19:43:41Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Added __composite_values__() to Money, InstitutionDetails, RewardsBalance for SQLAlchemy composite() support
- Replaced exclude_properties + before_flush event handler with composite() mappings in Account mapper
- Eliminated _decompose_value_objects event handler (53 lines)
- Eliminated _reconstruct_value_objects repository method (100 lines)
- Removed 18 type: ignore[attr-defined] comments from mappers.py
- All 437 tests pass (252 API + 185 domain)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add __composite_values__ to value objects** - `cfefa0b` (feat)
2. **Task 2: Replace exclude_properties with composite() and clean up repository** - `a9a89ac` (refactor)

**Plan metadata:** (pending)

## Files Created/Modified
- `libs/domain/domain/model/money.py` - Added __composite_values__() returning (amount, currency)
- `libs/domain/domain/model/institution.py` - Added __composite_values__() returning (name, website, phone, notes)
- `libs/domain/domain/model/rewards_balance.py` - Added __composite_values__() returning (value, unit)
- `apps/api/src/adapters/persistence/orm/mappers.py` - Replaced exclude_properties + before_flush with composite() mappings using factory functions
- `apps/api/src/adapters/persistence/repositories/account.py` - Removed _reconstruct_value_objects, simplified to _reconstruct_entity_ids_and_enums

## Decisions Made

**1. Use factory functions for composite() instead of direct class constructors**
- **Rationale:** When all composite columns are NULL (e.g., credit_limit for checking accounts), SQLAlchemy still calls the composite constructor with None values. Direct use of Money/InstitutionDetails/RewardsBalance constructors fails on `Decimal(str(None))`.
- **Solution:** Factory functions (_money_factory, _institution_factory, _rewards_factory) check for NULL and return None before calling constructors.
- **Impact:** Nullable composites work correctly without modifying value object constructors.

**2. Keep EntityId/Enum reconstruction in repository**
- **Rationale:** TypeDecorators return strings from process_result_value, not domain types. The repository layer converts strings to EntityIds and Enums.
- **Solution:** Renamed _reconstruct_value_objects to _reconstruct_entity_ids_and_enums, keeping only EntityId/Enum conversion logic.
- **Impact:** Clear separation of concerns: composite() handles value objects, TypeDecorators handle primitives, repository handles domain types.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

**Issue 1: Nullable composite constructors called with None values**
- **Problem:** When credit_limit_amount and credit_limit_currency are both NULL, SQLAlchemy calls Money(None, None) which fails in __post_init__ with `Decimal(str(None))` → "None" → InvalidOperation.
- **Root cause:** SQLAlchemy composite() always calls the constructor with column values, even if all are NULL.
- **Solution:** Introduced factory functions that check for NULL before calling constructors. _money_factory returns None if both amount and currency are None. _institution_factory returns None if name is None. _rewards_factory returns None if both value and unit are None.
- **Verification:** All 252 API tests pass, including accounts with NULL credit_limit, NULL institution, NULL rewards_balance.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Value object ORM mapping complete and verified
- Cleaner composite() pattern ready for future value objects
- 153 lines of fragile manual mapping code eliminated
- Phase 10 complete (1/1 plans)

---
*Phase: 10-value-object-orm-mapping*
*Completed: 2026-02-09*
