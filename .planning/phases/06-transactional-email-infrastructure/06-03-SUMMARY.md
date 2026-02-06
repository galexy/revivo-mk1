---
phase: 06-transactional-email-infrastructure
plan: 03
subsystem: email
tags: [procrastinate, itsdangerous, smtp, event-handler, job-queue]

# Dependency graph
requires:
  - phase: 06-02
    provides: EmailService protocol, SmtpEmailAdapter, render_verification_email
  - phase: 05-02
    provides: Procrastinate job queue with task deferral
  - phase: 04-02
    provides: itsdangerous verification token generation
provides:
  - Verification email sent on UserRegistered event via job queue
  - 48-hour token expiry aligned with email template
  - Graceful degradation when job queue unavailable
affects: [06-04, password-reset-email, welcome-email]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Sync event handler with try/except around job defer for graceful degradation"
    - "Lazy import of job tasks inside handler to avoid circular imports"
    - "JOB_QUEUE_ENABLED check before attempting defer"

key-files:
  modified:
    - src/adapters/security/tokens.py
    - src/adapters/jobs/tasks.py
    - src/application/handlers/user_handlers.py

key-decisions:
  - "Handler catches defer exceptions for graceful degradation (email is side effect, not critical path)"
  - "48-hour token expiry to match email template promise"
  - "EmailDeliveryError added to retry_exceptions for transient SMTP failures"
  - "Lazy import of send_verification_email inside handler to avoid module-level job queue initialization"

patterns-established:
  - "Event handler graceful degradation: catch job defer failures, log warning, continue"
  - "JOB_QUEUE_ENABLED guard before deferring jobs in event handlers"

# Metrics
duration: 3min
completed: 2026-02-06
---

# Phase 6 Plan 3: Event Handler and Job Queue Email Integration Summary

**UserRegistered event wires to verification email via procrastinate job with 48h token and graceful job queue degradation**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-06T22:19:31Z
- **Completed:** 2026-02-06T22:22:35Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments
- Updated EMAIL_VERIFICATION_MAX_AGE to 172800 seconds (48 hours) matching email template
- Implemented send_verification_email job with actual SMTP delivery via SmtpEmailAdapter
- Wired on_user_registered handler to generate token and defer email job synchronously
- Added graceful degradation: handler catches defer exceptions when job queue unavailable

## Task Commits

Each task was committed atomically:

1. **Task 1: Update verification token expiry to 48 hours** - `f8bc305` (feat)
2. **Task 2: Implement send_verification_email job task** - `bf7d02d` (feat)
3. **Task 3: Wire event handler to enqueue email job** - `9a59b5e` (feat)

## Files Created/Modified
- `src/adapters/security/tokens.py` - EMAIL_VERIFICATION_MAX_AGE updated to 172800 (48h), docstrings updated
- `src/adapters/jobs/tasks.py` - send_verification_email now renders templates and sends via SMTP adapter, EmailDeliveryError in retry
- `src/application/handlers/user_handlers.py` - on_user_registered generates token, defers job, handles failures gracefully

## Decisions Made
- **Graceful degradation over fail-fast for email:** The handler catches defer exceptions rather than letting them propagate through the event bus. Registration must succeed even if the verification email cannot be enqueued. This is consistent with the project's JOB_QUEUE_ENABLED graceful degradation pattern.
- **Lazy import of job task in handler:** The `send_verification_email` task is imported inside the handler function body (not at module level) to avoid triggering procrastinate connector initialization at import time.
- **EmailDeliveryError in retry strategy:** Added to the existing ConnectionError and TimeoutError set, so transient SMTP failures trigger automatic retries with exponential backoff.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Added try/except around job defer for graceful degradation**
- **Found during:** Task 3 (Wire event handler)
- **Issue:** `send_verification_email.defer()` raises `AppNotOpen` when the job queue database is unavailable (e.g., in tests, or when JOB_QUEUE_ENABLED is implicitly true but DB is down). The event bus re-raises handler exceptions, which would crash user registration.
- **Fix:** Wrapped the defer call in try/except, logging a warning on failure. Registration flow continues even if email job cannot be enqueued.
- **Files modified:** src/application/handlers/user_handlers.py
- **Verification:** All 432 tests pass, including integration test that publishes UserRegistered events without job queue DB.
- **Committed in:** 9a59b5e (Task 3 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Essential for correctness. Without this fix, user registration would fail when the job queue is unavailable, breaking all integration tests.

## Issues Encountered
None beyond the deviation documented above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Full email flow wired: UserRegistered -> on_user_registered -> generate_verification_token -> send_verification_email.defer -> SMTP delivery
- Ready for 06-04: End-to-end integration testing of the complete email pipeline
- Mailpit captures emails in dev for visual verification

---
*Phase: 06-transactional-email-infrastructure*
*Completed: 2026-02-06*
