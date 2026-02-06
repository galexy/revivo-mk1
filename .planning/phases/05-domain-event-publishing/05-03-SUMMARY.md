---
phase: 05-domain-event-publishing
plan: 03
subsystem: infra
tags: [procrastinate, postgresql, job-queue, bash, operations, runbook]

# Dependency graph
requires:
  - phase: 05-02
    provides: Job queue infrastructure with Procrastinate
provides:
  - Operational scripts for job queue management
  - Operations runbook with procedures and troubleshooting
affects: [production-operations, monitoring, incident-response]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Direct SQL queries via psql for job queue operations"
    - "JOB_QUEUE_DATABASE_URL for separate jobs database connection"

key-files:
  created:
    - scripts/jobs/apply-schema.sh
    - scripts/jobs/list-failed.sh
    - scripts/jobs/job-status.sh
    - scripts/jobs/retry-job.sh
    - scripts/jobs/retry-all-failed.sh
    - scripts/jobs/queue-stats.sh
    - scripts/jobs/purge-old.sh
    - docs/runbooks/job-queue.md
  modified: []

key-decisions:
  - "Direct SQL queries via psql for maximum visibility into Procrastinate internals"
  - "JOB_QUEUE_DATABASE_URL environment variable matches app configuration"
  - "Separate docs/runbooks directory for operational documentation"

patterns-established:
  - "scripts/jobs/ directory for job queue operational scripts"
  - "docs/runbooks/ directory for operational runbooks"

# Metrics
duration: 4min
completed: 2026-02-06
---

# Phase 05 Plan 03: Job Queue Operations Summary

**7 operational bash scripts for job queue management plus 300-line runbook with health checks, troubleshooting, and emergency procedures**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-06T19:02:24Z
- **Completed:** 2026-02-06T19:06:30Z
- **Tasks:** 2
- **Files created:** 8

## Accomplishments
- Created 7 executable bash scripts for common job queue operations
- Created comprehensive 300-line runbook with procedures and troubleshooting
- Documented monitoring queries for Grafana integration
- Documented emergency procedures for production incidents

## Task Commits

Each task was committed atomically:

1. **Task 1: Create job queue operational scripts** - `082c945` (feat)
2. **Task 2: Create job queue runbook** - `c93fd2f` (docs)

## Files Created/Modified

**Scripts:**
- `scripts/jobs/apply-schema.sh` - Apply Procrastinate schema to jobs database
- `scripts/jobs/list-failed.sh` - List failed jobs with error details
- `scripts/jobs/job-status.sh` - Get detailed status of a specific job
- `scripts/jobs/retry-job.sh` - Retry a specific failed job
- `scripts/jobs/retry-all-failed.sh` - Retry all failed jobs, optionally by queue
- `scripts/jobs/queue-stats.sh` - Show job queue statistics
- `scripts/jobs/purge-old.sh` - Purge completed jobs older than N days

**Documentation:**
- `docs/runbooks/job-queue.md` - Comprehensive operations runbook (300 lines)

## Decisions Made
- Direct SQL queries via psql for maximum visibility into Procrastinate internals
- Runbook includes monitoring queries ready for Grafana integration
- JOB_QUEUE_ENABLED=false documented for emergency stop procedure

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Phase 5 (Domain Event Publishing) is now complete:
- Plan 01: Domain event infrastructure with in-memory bus
- Plan 02: Procrastinate job queue integration
- Plan 03: Operational tooling and runbook

Ready for Phase 6: Transactional Email Infrastructure

---
*Phase: 05-domain-event-publishing*
*Completed: 2026-02-06*
