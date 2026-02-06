---
phase: 06-transactional-email-infrastructure
plan: 01
subsystem: infra
tags: [mjml, mailpit, smtp, email, docker-compose, makefile]

requires:
  - phase: 05-domain-event-publishing
    provides: "Event bus and job queue for triggering email sends"
provides:
  - "MJML build tooling for email template compilation"
  - "Mailpit SMTP capture for development email testing"
  - "SMTP environment variables for app email sending"
  - "Makefile build-emails target for template compilation"
affects:
  - "06-02: MJML template creation uses build-emails target"
  - "06-03: Email service uses SMTP_* env vars to connect to Mailpit"
  - "06-04: Email verification flow uses Mailpit for testing"

tech-stack:
  added: ["mjml ^4.15.0", "axllent/mailpit:v1.29"]
  patterns: ["npx for Node.js tool invocation", "Makefile for build orchestration", "SMTP capture for dev email testing"]

key-files:
  created:
    - "package.json"
    - "Makefile"
    - "scripts/verify-mailpit.py"
  modified:
    - ".devcontainer/devcontainer.json"
    - "docker-compose.yml"

key-decisions:
  - "MJML as devDependency via npm (not Python package)"
  - "Mailpit always-on service (not optional Docker profile)"
  - "App starts even if SMTP unavailable (mailpit uses condition: service_started)"
  - "No SMTP_USER/SMTP_PASSWORD for Mailpit (accepts any auth)"
  - "Verification script as reusable tool in scripts/ directory"

patterns-established:
  - "npx mjml: Node.js tool invocation for email template compilation"
  - "Makefile targets: Build orchestration for non-Python tooling"
  - "verify-mailpit.py: Infrastructure verification pattern"

duration: 3min
completed: 2026-02-06
---

# Phase 6 Plan 01: MJML Build Tooling and Mailpit Summary

**MJML email template compiler installed via npm with Makefile build target, Mailpit SMTP capture added to Docker Compose for development email testing**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-06T22:04:20Z
- **Completed:** 2026-02-06T22:07:20Z
- **Tasks:** 6/6
- **Files modified:** 5

## Accomplishments

- MJML v4.18.0 installed via npm with automatic setup on devcontainer rebuild
- Makefile with `build-emails` target compiles MJML templates to HTML via `npx mjml`
- Mailpit service added to Docker Compose with SMTP (port 1025) and web UI (port 8025)
- App service configured with SMTP_* environment variables for email sending
- Verification script created to validate full email infrastructure stack

## Task Commits

Each task was committed atomically:

1. **Task 1: Create package.json with MJML dependency** - `fd1ca76` (feat)
2. **Task 2: Update devcontainer for npm integration** - `a382c53` (feat)
3. **Task 3: Rebuild devcontainer and verify MJML** - checkpoint (devcontainer rebuild)
4. **Task 4: Create Makefile with build-emails target** - `ceca771` (feat)
5. **Task 5: Add Mailpit to Docker Compose** - `65125b9` (feat)
6. **Task 6: Verify full stack and test email capture** - `c3573b9` (feat)

## Files Created/Modified

- `package.json` - MJML devDependency for email template compilation
- `.devcontainer/devcontainer.json` - npm ci in postCreateCommand, port 8025 forwarded
- `Makefile` - build-emails target using npx mjml, help target
- `docker-compose.yml` - Mailpit service, SMTP_* env vars for app, APP_BASE_URL
- `scripts/verify-mailpit.py` - Verification script for Mailpit SMTP and web UI

## Decisions Made

1. **MJML via npm devDependency** - Keeps Node.js tooling separate from Python app, invoked via npx
2. **Mailpit always-on** - Simpler than optional Docker profile, no production impact (dev-only compose file)
3. **condition: service_started for Mailpit** - App doesn't need Mailpit to be healthy to start (graceful degradation)
4. **No SMTP credentials** - Mailpit accepts any auth in dev (MP_SMTP_AUTH_ACCEPT_ANY=1)
5. **Verification script** - Reusable validation tool in scripts/ directory for post-rebuild checks

## Deviations from Plan

### Auto-added Items

**1. [Rule 2 - Missing Critical] Verification script for Mailpit**
- **Found during:** Task 6
- **Issue:** Docker CLI unavailable inside devcontainer; cannot start Mailpit or run live SMTP test
- **Fix:** Created `scripts/verify-mailpit.py` as reusable verification tool to run after devcontainer rebuild
- **Files created:** scripts/verify-mailpit.py
- **Commit:** c3573b9

## Notes

- Mailpit requires a devcontainer rebuild to start (added to docker-compose.yml but compose stack needs restart)
- After rebuild, run `python scripts/verify-mailpit.py` to confirm email infrastructure is fully operational
- The `make build-emails` target will fail until MJML templates are created in Plan 06-02
