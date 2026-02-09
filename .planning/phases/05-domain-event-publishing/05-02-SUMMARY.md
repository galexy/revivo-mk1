---
phase: 05-domain-event-publishing
plan: 02
subsystem: infra
tags: [procrastinate, event-bus, job-queue, fastapi-lifespan]

# Dependency graph
requires:
  - phase: 05-01
    provides: Event bus infrastructure with publish/register/clear_handlers
provides:
  - Procrastinate job queue app with PsycopgConnector
  - Placeholder email task with retry strategy
  - UoW commit publishes events to handlers
  - Event handler registration during FastAPI lifespan
  - Job queue worker startup in lifespan (optional via JOB_QUEUE_ENABLED)
  - Integration tests for event publishing flow
affects: [06-transactional-email-infrastructure, any-future-event-handlers]

# Tech tracking
tech-stack:
  added: [procrastinate, psycopg]
  patterns: [job-queue-in-lifespan, optional-worker-startup, event-handlers]

key-files:
  created:
    - src/adapters/jobs/__init__.py
    - src/adapters/jobs/app.py
    - src/adapters/jobs/tasks.py
    - src/application/handlers/__init__.py
    - src/application/handlers/user_handlers.py
    - tests/integration/test_event_publishing.py
  modified:
    - src/adapters/persistence/unit_of_work.py
    - src/adapters/api/app.py

key-decisions:
  - "UoW publishes events AFTER commit succeeds (Cosmic Python pattern)"
  - "JOB_QUEUE_ENABLED env var for graceful degradation when job db unavailable"
  - "Handlers are sync; async work delegated to job queue"
  - "Placeholder email task ready for Phase 6 implementation"

patterns-established:
  - "Event handlers registered in lifespan via register_all_handlers()"
  - "Job queue worker runs in same process as API"
  - "Retry strategy pattern for email jobs (5 attempts, exponential backoff)"

# Metrics
duration: 6min
completed: 2026-02-06
---

# Phase 5 Plan 02: Job Queue Integration Summary

**Procrastinate job queue wired to FastAPI lifespan with event handlers called after UoW commit**

## Performance

- **Duration:** 6 min
- **Started:** 2026-02-06T18:52:53Z
- **Completed:** 2026-02-06T18:59:00Z
- **Tasks:** 3
- **Files modified:** 8

## Accomplishments
- Procrastinate job queue app with separate database connection
- UoW commit() now publishes events to handlers after transaction succeeds
- Event handlers registered during FastAPI lifespan startup
- Optional job queue worker in same process (controlled by JOB_QUEUE_ENABLED)
- 9 integration tests proving event publishing flow works

## Task Commits

Each task was committed atomically:

1. **Task 1: Create Procrastinate job queue infrastructure** - `3d7a217` (feat)
2. **Task 2: Modify UoW to publish events and wire handlers** - `c576909` (feat)
3. **Task 3: Wire lifespan and add integration tests** - `46ff411` (feat)

## Files Created/Modified
- `src/adapters/jobs/__init__.py` - Job queue module exports
- `src/adapters/jobs/app.py` - Procrastinate app with PsycopgConnector
- `src/adapters/jobs/tasks.py` - Placeholder email task with retry strategy
- `src/application/handlers/__init__.py` - register_all_handlers() function
- `src/application/handlers/user_handlers.py` - UserRegistered and EmailVerified handlers
- `src/adapters/persistence/unit_of_work.py` - Added event publishing after commit
- `src/adapters/api/app.py` - Handler registration and worker startup in lifespan
- `tests/integration/test_event_publishing.py` - 9 integration tests

## Decisions Made
- **Post-commit event publishing:** Events published AFTER commit to ensure handlers see committed data (RESEARCH.md Pitfall 1)
- **JOB_QUEUE_ENABLED env var:** Allows service to start without job database (graceful degradation)
- **Sync handlers:** Handlers are synchronous; they enqueue jobs for async work
- **Placeholder email task:** Ready for Phase 6, includes retry strategy (5 attempts, exponential backoff)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Pre-existing ruff lint issues in app.py (ARG001 for FastAPI contract parameters) - not introduced by this plan
- postgres-jobs database not running in devcontainer - verified graceful degradation with JOB_QUEUE_ENABLED=false

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Event publishing infrastructure complete
- Job queue ready for Phase 6 email tasks
- 432 tests passing (414 previous + 9 new + 9 from other sources)
- Service starts with event_handlers_registered log confirmation

---
*Phase: 05-domain-event-publishing*
*Completed: 2026-02-06*
