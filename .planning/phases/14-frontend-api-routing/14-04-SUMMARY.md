---
phase: 14-frontend-api-routing
plan: 04
subsystem: testing
tags: [playwright, e2e, mailpit, auth-fixtures]

# Dependency graph
requires:
  - phase: 13-login-ui
    provides: Auth-guarded app with login flow
provides:
  - Auth setup fixture that registers test user and verifies email via Mailpit API
  - Updated smoke tests that work with auth-guarded app
  - Playwright config with setup project for authenticated test scenarios
affects: [15-account-management, 16-transaction-management, testing]

# Tech tracking
tech-stack:
  added: []
  patterns: [playwright-auth-fixtures, mailpit-api-integration]

key-files:
  created:
    - apps/web/e2e/auth.setup.ts
    - apps/web/.gitignore
  modified:
    - apps/web/playwright.config.ts
    - apps/web/e2e/smoke.spec.ts

key-decisions:
  - "Auth setup uses Mailpit REST API to extract verification token from email (not manual email inspection)"
  - "Setup project runs before chromium project to establish auth state as dependency"
  - "Unauthenticated tests explicitly override storageState to empty cookies/origins"

patterns-established:
  - "Auth setup fixture: register via API, verify via Mailpit API, login via UI, save storageState"
  - "Test suites split by auth context: unauthenticated (login page) vs authenticated (dashboard)"

# Metrics
duration: 2min
completed: 2026-02-11
---

# Phase 14 Plan 04: E2E Test Auth Fixtures Summary

**Playwright smoke tests now work with auth-guarded app using Mailpit API for email verification and storageState for authenticated test scenarios**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-11T05:38:36Z
- **Completed:** 2026-02-11T05:40:17Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Auth setup fixture that registers test user, verifies email via Mailpit REST API, and logs in
- Smoke tests rewritten to work with auth-guarded app (Phase 13 login flow)
- Playwright config uses setup project as dependency to establish auth state before running tests
- Tests split by auth context: unauthenticated (login page) and authenticated (dashboard)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create auth setup fixture and update Playwright config** - `cc7af8e` (test)
2. **Task 2: Rewrite smoke tests for auth-guarded app** - `b367f5e` (test)

## Files Created/Modified
- `apps/web/e2e/auth.setup.ts` - Playwright setup project that registers user, verifies email via Mailpit API, logs in, and saves storageState
- `apps/web/playwright.config.ts` - Added setup project and configured chromium project with storageState dependency
- `apps/web/.gitignore` - Added e2e/.auth/ to ignore auth state files
- `apps/web/e2e/smoke.spec.ts` - Rewritten for auth-guarded app with unauthenticated (login page) and authenticated (dashboard) test suites

## Decisions Made

**Auth fixture approach: API + Mailpit API + UI**
- Register via backend API (POST /auth/register)
- Fetch verification email from Mailpit REST API (GET /api/v1/messages)
- Extract token from email body with regex
- Verify email via backend API (GET /auth/verify?token=...)
- Log in via UI (fill form, click button, wait for dashboard)
- Save storageState to apps/web/e2e/.auth/user.json

**Rationale:** UI login establishes browser cookies/localStorage correctly. API verification is faster and more reliable than manual email inspection.

**Setup project dependency pattern**
- setup project runs first (no storageState)
- chromium project depends on setup and uses saved storageState
- All authenticated tests run with saved auth state by default

**Rationale:** Playwright's dependency system ensures auth happens once before test suite. Individual tests can override with `test.use({ storageState: { cookies: [], origins: [] } })` for unauthenticated scenarios.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - auth setup and smoke tests implemented as specified. Tests will be verified during phase verification with both servers running.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Playwright auth fixtures ready for Phase 15+ feature tests
- All future e2e tests can use the saved auth state without re-registering
- Pattern established: setup project creates test user once, chromium project uses saved state
- Mailpit API integration documented for future email verification tests

**Blocker:** None. e2e tests require both API backend and web frontend running, which will be verified during phase verification.

---
*Phase: 14-frontend-api-routing*
*Completed: 2026-02-11*
