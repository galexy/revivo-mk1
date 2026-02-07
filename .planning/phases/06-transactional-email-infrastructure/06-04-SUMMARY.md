---
phase: 06-transactional-email-infrastructure
plan: 04
subsystem: email-testing
tags: [mock-email, integration-tests, e2e-verification, defer-async]

# Dependency graph
requires:
  - phase: 06-03
    provides: Event handler wiring, send_verification_email job
  - phase: 04-06
    provides: Auth integration test patterns
provides:
  - MockEmailAdapter for test email assertions
  - Integration tests for email verification flow
  - E2E verified: register -> Mailpit -> verify link -> login
affects: [06-05]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "MockEmailAdapter implementing EmailService protocol for test injection"
    - "Module-scoped test fixtures with per-test transactional rollback"

key-files:
  created:
    - tests/mocks/__init__.py
    - tests/mocks/email.py
    - tests/integration/test_email_verification.py
  modified:
    - src/application/handlers/user_handlers.py

key-decisions:
  - "defer_async + create_task workaround for sync handler calling async connector (interim fix)"
  - "Separate client_with_handlers fixture to register event handlers without full lifespan"

patterns-established:
  - "MockEmailAdapter for recording sent emails in tests"

# Metrics
duration: ~15min (spread across sessions due to E2E debugging)
completed: 2026-02-07
---

# Phase 6 Plan 4: Integration Tests and End-to-End Verification Summary

**MockEmailAdapter, integration tests, and E2E verification of email flow — with sync/async defer issue discovered and interim fix applied**

## Performance

- **Duration:** ~15 min (across sessions, including E2E debugging)
- **Started:** 2026-02-06
- **Completed:** 2026-02-07
- **Tasks:** 3
- **Files created:** 3, **Files modified:** 1

## Accomplishments
- Created MockEmailAdapter in tests/mocks/ implementing EmailService protocol
- Created 11 integration tests covering email verification flow
- E2E verified full flow: register -> Mailpit email arrives -> verify link works -> login succeeds -> idempotent re-verify

## Task Commits

1. **Task 1: Create MockEmailAdapter** - `b0f3ed1` (feat)
2. **Task 2: Create integration tests** - `e188870` (feat)
3. **Task 3: E2E checkpoint** - manually verified, all 8 steps passed
4. **Deviation fix: defer_async workaround** - `996849d` (fix)

## Files Created/Modified
- `tests/mocks/__init__.py` - MockEmailAdapter export
- `tests/mocks/email.py` - MockEmailAdapter with SentEmail record, get_last_email, get_emails_to, clear
- `tests/integration/test_email_verification.py` - 11 tests across 4 test classes
- `src/application/handlers/user_handlers.py` - Changed defer() to defer_async() via create_task

## Deviations from Plan

### 1. [Rule 1 - Bug] Sync defer() fails under async FastAPI context

- **Found during:** Task 3 E2E verification
- **Issue:** `send_verification_email.defer()` (sync) fails with `AppNotOpen` because the PsycopgConnector was opened with `open_async()` in FastAPI lifespan. When called from the main asyncio thread, `asgiref.async_to_sync()` raises because an event loop is already running.
- **Interim fix:** Changed to `asyncio.get_running_loop().create_task(send_verification_email.defer_async(...))` — schedules async defer on the running event loop from the sync handler.
- **Limitation:** Fire-and-forget — if `defer_async()` fails asynchronously, the error is not caught by the handler's try/except. For email (non-critical side effect), this is tolerable but not ideal.
- **Root cause:** The event bus calls handlers synchronously (`handler(event)`), but Procrastinate's connector is async-only after `open_async()`. The proper fix is making the event bus async-aware so handlers can `await defer_async()` directly.
- **Committed in:** 996849d

### 2. [Known gap] Integration test mocks wrong method

- **Issue:** `test_registration_enqueues_verification_email` mocks `send_verification_email.defer` but the code now calls `defer_async` via `create_task`. The test passes because the mock prevents the real call, but it's not testing the actual code path.
- **Resolution:** Deferred to 06-05 which will convert the event bus to async and fix the tests.

## Issues Discovered

**The integration tests did not catch the sync/async mismatch because:**
1. Most tests use `JOB_QUEUE_ENABLED=false` or don't register event handlers, bypassing the defer path entirely
2. The one test that exercises the handler mocks `defer` to a MagicMock, so the real Procrastinate connector is never called
3. This confirms the CHECKPOINTS.md warning: integration tests with mocks can mask issues that only appear with real infrastructure

## Carries Forward to 06-05

- Convert event bus to async (publish/publish_all become async, handlers can be async)
- Convert UoW.commit() to async (so it can await publish_all)
- Update integration tests to test real defer path (not mocked)
- Remove create_task workaround in favor of proper await

---
*Phase: 06-transactional-email-infrastructure*
*Completed: 2026-02-07*
