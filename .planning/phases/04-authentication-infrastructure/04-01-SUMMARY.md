---
phase: 04-authentication-infrastructure
plan: 01
subsystem: domain-model
tags: [user, household, typeid, domain-events, tdd]
dependency-graph:
  requires: [01-foundation, 02-account-domain]
  provides: [User entity, Household entity, HouseholdId, UserRegistered event, EmailVerified event]
  affects: [04-02 (password hashing), 04-03 (auth ports), 04-04 (repositories), 04-05 (auth service)]
tech-stack:
  added: []
  patterns: [aggregate-root-with-events, collect-events-pattern, typeid-entity-ids, tdd-red-green]
key-files:
  created:
    - src/domain/model/user.py
    - src/domain/model/household.py
    - src/domain/events/user_events.py
    - tests/unit/domain/test_user.py
    - tests/unit/domain/test_household.py
  modified:
    - src/domain/model/entity_id.py
    - src/domain/model/__init__.py
    - src/domain/events/__init__.py
decisions:
  - User events are standalone frozen dataclasses (not inheriting DomainEvent base)
  - User.collect_events() pattern (copy-then-clear) for event collection
  - Email normalization in domain (lowercase + strip) not infrastructure
  - verify_email() idempotent (no-op on already-verified user)
  - Household is thin aggregate (no events yet, just factory + update_name)
metrics:
  duration: 3 min
  completed: 2026-02-05
---

# Phase 4 Plan 01: User & Household Domain Entities Summary

**TDD domain model foundation for authentication: User with email/password/verification, Household for data scoping, HouseholdId TypeID, and two domain events (UserRegistered, EmailVerified).**

## What Was Built

### HouseholdId TypeID
- Frozen dataclass with `hh_` prefix following existing AccountId/UserId/etc. pattern
- `generate()`, `from_string()` with prefix validation, `prefix` property
- Added to `entity_id.py` between UserId and CategoryId

### Household Entity
- Aggregate root with `id`, `name`, `owner_id`, `created_at`, `updated_at`
- `create()` factory generates HouseholdId and sets consistent timestamps
- `update_name()` mutation method updates name and timestamp
- Uses `eq=False` matching Account pattern (identity by ID)

### User Entity
- Aggregate root with `id`, `email`, `display_name`, `password_hash`, `household_id`
- `email_verified` (bool) and `email_verified_at` (datetime|None) for verification tracking
- `create()` factory normalizes email (lowercase + strip), strips display_name
- `verify_email()` is idempotent -- no-op if already verified, no duplicate event
- `collect_events()` returns events and clears internal list
- `update_display_name()` mutation method

### Domain Events
- `UserRegistered`: emitted on `User.create()` with user_id, email, household_id
- `EmailVerified`: emitted on `User.verify_email()` with user_id, email
- Both are frozen dataclasses with slots (immutable, memory-efficient)
- Not inheriting from DomainEvent base -- standalone events for User aggregate

## TDD Execution

| Phase | Task | Tests | Result |
|-------|------|-------|--------|
| RED   | Task 1: HouseholdId tests | 4 | All fail (ImportError) |
| GREEN | Task 2: HouseholdId impl | 4 | All pass |
| RED   | Task 3: Household tests | 4 | All fail (ModuleNotFoundError) |
| GREEN | Task 4: Household impl | 8 | All pass (4+4) |
| RED   | Task 5: User tests | 9 | All fail (ModuleNotFoundError) |
| GREEN | Task 6: User + events impl | 17 | All pass (9+8) |

## Commits

| Hash | Type | Description |
|------|------|-------------|
| `439bcf7` | test | Failing tests for HouseholdId TypeID |
| `b82648c` | feat | Implement HouseholdId TypeID |
| `4754498` | test | Failing tests for Household entity |
| `1de6bdd` | feat | Implement Household entity |
| `80a8b7a` | test | Failing tests for User entity and events |
| `5065776` | feat | Implement User entity and domain events |

## Verification

1. `pytest tests/unit/domain/test_user.py tests/unit/domain/test_household.py -v` -- 17/17 pass
2. `python -c "from src.domain.model import HouseholdId, Household, User, UserId"` -- OK
3. `python -c "from src.domain.events.user_events import UserRegistered, EmailVerified"` -- OK
4. `lint-imports` -- 2 contracts kept, 0 broken (no infrastructure imports in domain)
5. Full unit suite: 231 tests pass, no regressions

## Deviations from Plan

None -- plan executed exactly as written.

## Decisions Made

1. **User events standalone (not DomainEvent subclass):** User events use `frozen=True, slots=True` dataclasses directly rather than inheriting from `DomainEvent` base class. This is because User events use `collect_events()` pattern while Account uses `_events` list with `clear_events()`. Both patterns work but User's is simpler for the collect-then-clear use case.

2. **Email normalization in domain layer:** `User.create()` performs `email.lower().strip()` rather than deferring to infrastructure. This is domain logic (email identity) not infrastructure.

3. **Idempotent verify_email():** Calling `verify_email()` on already-verified user is a silent no-op (no event, no timestamp change). This prevents duplicate events and is the expected behavior for email verification links that might be clicked multiple times.

## Next Phase Readiness

Plan 04-01 provides the domain entities that plan 04-02 through 04-08 build upon:
- 04-02: Password hashing adapter (references User.password_hash)
- 04-03: Auth ports (UserRepository protocol references User entity)
- 04-04: Database tables and repositories (persist User/Household)
- 04-05: Auth service (orchestrates User.create, Household.create)
