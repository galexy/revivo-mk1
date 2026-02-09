---
phase: 05-domain-event-publishing
plan: 01
subsystem: events
tags: [procrastinate, psycopg, event-bus, domain-events]

# Dependency graph
requires:
  - phase: 04-authentication-infrastructure
    provides: Domain events (UserRegistered, EmailVerified) collected via UoW
provides:
  - In-process event bus with register/publish API
  - Procrastinate job queue dependencies
  - PostgreSQL jobs database configuration
affects: [05-02-job-queue-integration, 05-03-uow-integration, 06-transactional-email]

# Tech tracking
tech-stack:
  added: [procrastinate, psycopg, psycopg-binary, psycopg-pool]
  patterns: [event-bus-handler-registry, post-commit-event-dispatch]

key-files:
  created:
    - src/application/event_bus.py
    - tests/unit/application/test_event_bus.py
  modified:
    - pyproject.toml
    - docker-compose.yml

key-decisions:
  - "Event bus uses dict[type, list[Callable]] for handler registry (Cosmic Python pattern)"
  - "Handlers called synchronously; async work delegated to job queue"
  - "Exception in handler re-raised for fail-fast in development"
  - "Separate postgres-jobs database on port 5433 for job queue isolation"

patterns-established:
  - "Event bus registration: event_bus.register(EventType, handler_function)"
  - "Event publishing: event_bus.publish_all(events) after UoW commit"
  - "Test isolation: autouse fixture calling clear_handlers() after each test"

# Metrics
duration: 4min
completed: 2026-02-06
---

# Phase 5 Plan 01: Event Bus Infrastructure Summary

**In-process event bus with Procrastinate/psycopg job queue dependencies and PostgreSQL jobs database**

## Performance

- **Duration:** 4 min (222 seconds)
- **Started:** 2026-02-06T18:45:54Z
- **Completed:** 2026-02-06T18:49:36Z
- **Tasks:** 3
- **Files modified:** 4

## Accomplishments
- Event bus module with register/publish/publish_all/clear_handlers API
- Procrastinate 3.7.2 and psycopg 3.3.2 installed for job queue
- PostgreSQL jobs database service configured in docker-compose
- 9 unit tests covering all event bus functionality

## Task Commits

Each task was committed atomically:

1. **Task 1: Add dependencies and jobs database** - `d0239b2` (chore)
2. **Task 2: Create event bus module** - `3522cf1` (feat)
3. **Task 3: Unit tests for event bus** - `44b7be5` (test)

## Files Created/Modified
- `src/application/event_bus.py` - In-process event bus with handler registry
- `tests/unit/application/test_event_bus.py` - 9 unit tests (210 lines)
- `pyproject.toml` - Added procrastinate, psycopg[binary], pydantic[email]
- `docker-compose.yml` - Added postgres-jobs service, JOB_QUEUE_DATABASE_URL

## Decisions Made
- Event bus follows Cosmic Python pattern (dict-based handler registry)
- Handlers called synchronously - async work should use job queue
- Separate database for job queue (not same as app database)
- Fail-fast approach: handler exceptions logged and re-raised

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Restored pydantic[email] dependency**
- **Found during:** Task 3 (running all tests)
- **Issue:** email-validator was removed during uv sync (dependency conflict with procrastinate)
- **Fix:** Changed `pydantic>=2.10.0` to `pydantic[email]>=2.10.0` in pyproject.toml
- **Files modified:** pyproject.toml
- **Verification:** All 423 tests pass
- **Committed in:** 44b7be5 (Task 3 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Fix necessary for existing tests to pass. No scope creep.

## Issues Encountered
None - plan executed as specified.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Event bus ready for handler registration in 05-02
- Procrastinate dependencies ready for job queue setup
- Jobs database configuration ready for worker integration

---
*Phase: 05-domain-event-publishing*
*Completed: 2026-02-06*
