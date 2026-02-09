---
phase: 09-type-safety-test-cleanup
plan: "01"
subsystem: type-safety
tags:
  - type-safety
  - typeddict
  - test-cleanup
  - pyright
requires:
  - "08-05-PLAN.md"  # CI code quality setup
provides:
  - CategoryTree TypedDict for type-safe category tree access
  - Reduced test suite without redundant immutability tests
affects:
  - "09-02-PLAN.md"  # Continued type safety improvements
tech-stack:
  added: []
  patterns:
    - TypedDict for structured dict returns
    - Rely on pyright strict for frozen dataclass enforcement
key-files:
  created: []
  modified:
    - apps/api/src/application/services/category_service.py
    - apps/api/src/adapters/api/routes/categories.py
    - libs/domain/tests/unit/domain/test_institution.py
    - libs/domain/tests/unit/domain/test_rewards_balance.py
    - libs/domain/tests/unit/domain/test_split_line.py
key-decisions:
  - decision: "Use TypedDict for category tree structure"
    rationale: "Provides distinct types per key (root/children), eliminating need for type: ignore comments"
    alternatives: "Keep loose dict type with type: ignore comments"
  - decision: "Remove frozen dataclass immutability tests"
    rationale: "Pyright strict catches these at compile time; runtime tests requiring type: ignore[misc] are redundant"
    alternatives: "Keep tests for runtime validation"
patterns-established:
  - "TypedDict for structured dict returns with distinct key types"
  - "Remove tests that verify language mechanics already enforced by static analysis"
duration: "3m"
completed: "2026-02-09"
---

# Phase 9 Plan 1: Type Safety & Test Cleanup Summary

**Introduced CategoryTree TypedDict for type-safe tree access and removed 7 redundant immutability tests caught by pyright strict**

## Performance

- **Duration:** 3 minutes
- **Tasks:** 2/2 completed
- **Test reduction:** 192 → 185 domain tests (7 removed)
- **Type safety:** Eliminated 2 type: ignore[assignment] comments in categories.py
- **Quality gates:** All passing (typecheck 0 errors, tests 437 passing: 252 API + 185 domain)

## Accomplishments

### 1. Added CategoryTree TypedDict for Type-Safe Access

**Problem:** `get_category_tree` returned `dict[str, list[Category] | dict[str, list[Category]]]`, a union type that required `type: ignore` comments when accessing specific keys because the type checker couldn't distinguish between `tree["root"]` (should be `list[Category]`) and `tree["children"]` (should be `dict[str, list[Category]]`).

**Solution:** Introduced `CategoryTree` TypedDict with distinct types per key:

```python
class CategoryTree(TypedDict):
    root: list[Category]
    children: dict[str, list[Category]]
```

**Impact:**
- Routes can access `tree["root"]` and `tree["children"]` without type: ignore
- Type checker provides accurate autocomplete and validation
- Zero runtime overhead (TypedDict is purely static)

### 2. Removed Redundant Frozen Dataclass Tests

**Analysis:** Found 7 tests across 3 files that verified frozen dataclass fields can't be assigned at runtime. These tests themselves required `type: ignore[misc]` to compile, proving pyright strict already catches these errors.

**Removed:**
- 4 tests from `test_institution.py` (name, website, phone, notes assignment)
- 2 tests from `test_rewards_balance.py` (value, unit assignment)
- 1 test from `test_split_line.py` (amount assignment)

**Kept:** `test_arithmetic_returns_new_instance` in rewards_balance tests — this verifies behavioral contract (new instance returned, originals unchanged), not just language mechanics.

**Renamed:** `TestRewardsBalanceImmutability` → `TestRewardsBalanceArithmeticBehavior` to reflect actual purpose.

## Task Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 | 1a1a38a | Add CategoryTree TypedDict and update get_category_tree |
| 2 | e7335d0 | Remove redundant frozen dataclass immutability tests |

## Files Created/Modified

### Modified

**apps/api/src/application/services/category_service.py**
- Added CategoryTree TypedDict definition
- Updated get_category_tree return type from loose dict to CategoryTree

**apps/api/src/adapters/api/routes/categories.py**
- Imported CategoryTree from service module
- Removed type: ignore[assignment] comments (2 instances)
- Simplified tree access with clean typed references

**libs/domain/tests/unit/domain/test_institution.py**
- Removed TestInstitutionDetailsImmutability class (4 tests)

**libs/domain/tests/unit/domain/test_rewards_balance.py**
- Renamed TestRewardsBalanceImmutability to TestRewardsBalanceArithmeticBehavior
- Removed test_cannot_modify_value and test_cannot_modify_unit
- Kept test_arithmetic_returns_new_instance (behavioral test)

**libs/domain/tests/unit/domain/test_split_line.py**
- Removed test_split_line_immutable_with_id

## Decisions Made

### Use TypedDict for Structured Dict Returns

**Context:** `get_category_tree` returns a dict with known keys and distinct types per key.

**Decision:** Define CategoryTree TypedDict with explicit key types.

**Rationale:**
- Eliminates type: ignore comments in consuming code
- Provides better IDE autocomplete and type checking
- Documents structure at definition site
- Zero runtime cost (purely static)

**Alternatives considered:**
1. Keep loose dict with type: ignore — rejected (defeats purpose of strict typing)
2. Create CategoryTreeResponse dataclass — rejected (unnecessary overhead for internal API)

### Remove Tests Redundant with Static Analysis

**Context:** Pyright strict mode catches frozen dataclass field assignments at compile time with clear error messages.

**Decision:** Remove immutability tests that require type: ignore[misc] to even compile.

**Rationale:**
- Test code requiring type: ignore proves static analysis already catches the error
- Runtime tests of language mechanics add no value when static analysis is stricter
- Reduces test suite maintenance burden
- Keeps tests focused on behavior, not language features

**Guidelines established:**
- Remove tests that verify language/framework guarantees already enforced by static analysis
- Keep tests that verify domain behavior and business rules
- Keep tests that verify behavioral contracts (e.g., "arithmetic returns new instance")

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - straightforward refactoring with strong type system support.

## Next Phase Readiness

**Ready for 09-02:** Continue type safety improvements in other modules.

**Pattern established:** TypedDict is the preferred approach for structured dict returns with distinct key types. Eliminates type: ignore comments while maintaining Python dict ergonomics.

**Test philosophy clarified:** Static analysis in pyright strict mode is authoritative for type and immutability guarantees. Tests should focus on behavior and contracts, not language mechanics.

**Test count:** 437 total (252 API + 185 domain) - down 7 from previous (444). All passing with zero type errors.
