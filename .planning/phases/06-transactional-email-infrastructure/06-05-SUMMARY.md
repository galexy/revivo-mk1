---
phase: 06-transactional-email-infrastructure
plan: 05
subsystem: async-event-chain
tags: [async, event-bus, uow, service-layer, routes, defer-async]

# Dependency graph
requires:
  - phase: 06-04
    provides: Integration tests, create_task workaround for sync/async mismatch
  - phase: 05-01
    provides: Event bus infrastructure (sync publish/publish_all)
provides:
  - Async event bus with mixed sync/async handler support
  - Async UoW commit with proper await chain
  - Async service methods for all write operations
  - Proper await of defer_async (no more create_task workaround)
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "inspect.iscoroutinefunction() for mixed sync/async handler dispatch"
    - "asyncio.run() in sync tests to call async functions"
    - "AsyncMock for mocking async methods in unit tests"

key-files:
  created: []
  modified:
    - src/application/event_bus.py
    - src/domain/ports/unit_of_work.py
    - src/adapters/persistence/unit_of_work.py
    - src/application/services/auth_service.py
    - src/application/services/account_service.py
    - src/application/services/category_service.py
    - src/application/services/transaction_service.py
    - src/adapters/api/routes/auth.py
    - src/adapters/api/routes/accounts.py
    - src/adapters/api/routes/categories.py
    - src/adapters/api/routes/transactions.py
    - src/application/handlers/user_handlers.py
    - tests/integration/test_event_publishing.py
    - tests/integration/test_email_verification.py
    - tests/unit/application/test_event_bus.py
    - tests/unit/application/test_auth_service.py
    - tests/unit/application/test_account_service.py

key-decisions:
  - "Mixed handler support via inspect.iscoroutinefunction (async handlers awaited, sync handlers called directly)"
  - "UoW context manager stays sync (__enter__/__exit__), only commit() is async"
  - "Read-only routes stay sync def for FastAPI thread pool execution"
  - "asyncio.run() in sync test functions to call async methods (no pytest-asyncio dependency)"

patterns-established:
  - "route (async def) -> await service.method() -> await uow.commit() -> await publish_all() -> await handler()"

# Metrics
duration: ~12min
completed: 2026-02-07
---

# Phase 6 Plan 5: Async Event Bus, UoW, Services, and Routes Summary

**Full async conversion of publish chain from route to handler, eliminating fire-and-forget create_task workaround with proper await of defer_async**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-02-07
- **Completed:** 2026-02-07
- **Tasks:** 6
- **Files modified:** 17

## Accomplishments

- Converted event bus publish/publish_all to async with mixed sync/async handler support
- Made UoW commit() async, properly awaiting event publishing after DB commit
- Converted 30 service write methods to async across 4 service files
- Updated all route handlers to await async service methods
- Replaced create_task workaround with direct await of defer_async in user handler
- Updated all unit and integration tests for async compatibility
- Full test suite passes (444 tests), smoke test verified against running service

## Task Commits

1. **Task 1: Make event bus async with mixed handler support** - `29e6d5b` (feat)
2. **Task 2: Make UoW commit async** - `6b84ad9` (feat)
3. **Task 3: Make service methods async** - `0d64877` (feat)
4. **Task 4: Update routes to await service calls** - `05ea5d8` (feat)
5. **Task 5: Make handler async, remove create_task workaround** - `9a1ad5c` (feat)
6. **Task 6: Fix tests for async event bus and services** - `ea0da7f` (test)

## Files Modified

### Core async conversion
- `src/application/event_bus.py` - publish/publish_all now async, added inspect for mixed handler dispatch
- `src/domain/ports/unit_of_work.py` - UoW protocol commit() now async
- `src/adapters/persistence/unit_of_work.py` - SqlAlchemyUnitOfWork.commit() async, awaits publish_all
- `src/application/handlers/user_handlers.py` - on_user_registered async, direct await defer_async

### Service methods
- `src/application/services/auth_service.py` - 5 methods async (register, login, refresh, verify_email, logout_all_sessions)
- `src/application/services/account_service.py` - 11 methods async (all create_*, close, reopen, delete, update_name)
- `src/application/services/category_service.py` - 5 methods async (ensure_system_categories, create, update_name, update_parent, delete)
- `src/application/services/transaction_service.py` - 7 methods async (create, update_memo, update_dates, update_splits, mark_cleared, mark_reconciled, delete)

### Route handlers
- `src/adapters/api/routes/auth.py` - Added await to async service calls
- `src/adapters/api/routes/accounts.py` - Added await to async service calls
- `src/adapters/api/routes/categories.py` - Converted write routes to async def, added await
- `src/adapters/api/routes/transactions.py` - Converted write routes to async def, added await

### Test updates
- `tests/integration/test_event_publishing.py` - asyncio.run() for async publish/commit calls
- `tests/integration/test_email_verification.py` - AsyncMock for defer_async mock
- `tests/unit/application/test_event_bus.py` - asyncio.run() for async publish/publish_all
- `tests/unit/application/test_auth_service.py` - AsyncMock for commit, asyncio.run() for service calls
- `tests/unit/application/test_account_service.py` - AsyncMock for commit, asyncio.run() for service calls

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Unit tests failed after service methods became async**

- **Found during:** Task 6 (test verification)
- **Issue:** Unit tests in test_auth_service.py, test_account_service.py, and test_event_bus.py called service methods synchronously with MagicMock UoW. After services became async, these returned unawaited coroutines.
- **Fix:** Updated all unit test files: changed `uow.commit = MagicMock()` to `AsyncMock()`, wrapped async service calls in `asyncio.run()`, wrapped async event bus calls in `asyncio.run()`
- **Files modified:** tests/unit/application/test_auth_service.py, tests/unit/application/test_account_service.py, tests/unit/application/test_event_bus.py
- **Commit:** ea0da7f (included in Task 6 commit)

## Verification

All success criteria met:
1. Event bus publish/publish_all are async with mixed handler support (inspect.iscoroutinefunction)
2. Proper await chain: route -> service -> commit -> publish_all -> handler -> defer_async
3. No fire-and-forget create_task workaround (removed in Task 5)
4. Error handling works: defer_async failures caught by handler try/except (direct await)
5. All 444 tests pass with no regressions
6. Service smoke tested per CHECKPOINTS.md: register (202), verify (200), login (200), accounts (200/201), categories (200)

## Resolves from 06-04

This plan resolves all issues carried forward from 06-04-SUMMARY.md:
- Converted event bus to async (publish/publish_all)
- Converted UoW.commit() to async
- Updated integration tests to properly mock defer_async (not defer)
- Removed create_task workaround in favor of proper await

---
*Phase: 06-transactional-email-infrastructure*
*Completed: 2026-02-07*
