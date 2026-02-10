---
phase: 12-frontend-infrastructure
plan: 06
subsystem: ui
tags: [shadcn-ui, playwright, chromium, react, testing]

# Dependency graph
requires:
  - phase: 12-04
    provides: Manual shadcn/ui components (button, card, input, label)
  - phase: 12-05
    provides: Playwright e2e testing setup
provides:
  - Official shadcn/ui CLI-generated components with correct patterns
  - Playwright configured to use system Chromium (no bundled browser download)
  - Favicon for web app (fixes console error)
affects: [12-UAT, 13-login-ui]

# Tech tracking
tech-stack:
  added: [radix-ui meta-package]
  patterns: [shadcn CLI component generation, system browser for e2e tests]

key-files:
  created: [apps/web/public/favicon.ico]
  modified:
    - libs/ui/src/components/button.tsx
    - libs/ui/src/components/card.tsx
    - libs/ui/src/components/input.tsx
    - libs/ui/src/components/label.tsx
    - apps/web/playwright.config.ts

key-decisions:
  - "Use shadcn CLI with pnpm wrapper script to generate official components"
  - "Replace @radix-ui/* individual packages with radix-ui meta-package (CLI pattern)"
  - "Configure Playwright to use devcontainer's system Chromium instead of downloading bundled browser"
  - "Add minimal favicon to prevent console 404 errors in e2e tests"

patterns-established:
  - "shadcn CLI as source of truth for component updates (use 'shadcn diff' to check)"
  - "System browser preference over bundled downloads for containerized environments"

# Metrics
duration: 5min
completed: 2026-02-10
---

# Phase 12 Plan 06: shadcn/ui CLI Components Summary

**Official shadcn/ui CLI components replace manual versions; Playwright uses system Chromium eliminating 180MB browser download**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-10T16:06:55Z
- **Completed:** 2026-02-10T16:12:04Z
- **Tasks:** 3
- **Files modified:** 7

## Accomplishments
- Replaced 4 manually-created components with official shadcn CLI-generated versions
- All quality gates pass (typecheck, lint, test, format) with CLI components
- Playwright configured to use system Chromium at `/usr/bin/chromium`
- E2e smoke tests pass (2/2) using system browser
- Added favicon to eliminate console 404 errors

## Task Commits

Each task was committed atomically:

1. **Task 1: Replace components with CLI-generated versions** - `5259c18` (feat)
2. **Task 2: Verify all quality gates and tests pass** - (verification only, formatting included in Task 1 amended commit)
3. **Task 3: Fix Playwright to use system Chromium and verify e2e tests** - `2ee5eff` (feat)

## Files Created/Modified
- `libs/ui/src/components/button.tsx` - CLI-generated Button component with new-york style, using Slot.Root from radix-ui
- `libs/ui/src/components/card.tsx` - CLI-generated Card components (Card, CardHeader, CardFooter, CardTitle, CardDescription, CardContent, CardAction)
- `libs/ui/src/components/input.tsx` - CLI-generated Input component
- `libs/ui/src/components/label.tsx` - CLI-generated Label component using LabelPrimitive.Root
- `libs/ui/package.json` - Added radix-ui meta-package (CLI pattern)
- `apps/web/playwright.config.ts` - Configured executablePath to /usr/bin/chromium with container-safe args
- `apps/web/public/favicon.ico` - Simple SVG favicon to prevent 404 errors

## Decisions Made

**1. Create pnpm wrapper script for shadcn CLI**
- shadcn CLI spawns `pnpm` directly (not `npx pnpm`)
- pnpm not in PATH by default
- Created `/tmp/bin/pnpm` wrapper script calling `npx pnpm`
- Alternative considered: install pnpm globally (rejected due to permission issues)

**2. Keep radix-ui meta-package (CLI pattern)**
- CLI added `radix-ui` instead of individual `@radix-ui/*` packages
- Components import `Slot` from "radix-ui", `Label` from "radix-ui"
- This is the official CLI pattern (not an error)
- Verified with `shadcn diff` - no updates needed

**3. Add favicon to fix console errors**
- E2e test checking for console errors caught favicon 404
- Not related to component changes, but blocking test success
- Created minimal SVG favicon (💰 emoji) in apps/web/public/
- Alternative considered: ignore favicon 404s (rejected - should fix root cause)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Created pnpm wrapper script**
- **Found during:** Task 1 (shadcn CLI execution)
- **Issue:** shadcn CLI spawns `pnpm` command directly, but pnpm not in PATH. Command failed with ENOENT.
- **Fix:** Created wrapper script at `/tmp/bin/pnpm` that calls `npx pnpm "$@"`, added to PATH for CLI execution
- **Files modified:** None (temporary script outside project)
- **Verification:** `shadcn add` successfully generated 4 components
- **Committed in:** 5259c18 (Task 1)

**2. [Rule 2 - Missing Critical] Added favicon to prevent console errors**
- **Found during:** Task 3 (e2e test execution)
- **Issue:** Browser requesting `/favicon.ico` returns 404, causing console error. E2e test "app loads without errors" checks for console errors and fails.
- **Fix:** Created `apps/web/public/favicon.ico` with simple SVG emoji
- **Files modified:** apps/web/public/favicon.ico (created)
- **Verification:** E2e tests pass (2/2), no console errors
- **Committed in:** 2ee5eff (Task 3)

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 missing critical)
**Impact on plan:** Both fixes necessary for task completion. Pnpm wrapper enables CLI execution; favicon fixes legitimate test failure. No scope creep.

## Issues Encountered

**1. pnpm not available in PATH**
- **Problem:** shadcn CLI spawns `pnpm` directly, but corepack not enabled in container
- **Attempted:** `corepack enable` (permission denied), `npm install -g pnpm` (permission denied)
- **Solution:** Wrapper script in /tmp/bin calling `npx pnpm`
- **Outcome:** CLI executed successfully

**2. CLI uses radix-ui meta-package (unexpected pattern)**
- **Problem:** Expected individual @radix-ui/* packages, but CLI added `radix-ui` meta-package
- **Investigation:** Checked npm registry - this is a real package exporting all Radix primitives
- **Solution:** Accepted as official CLI pattern, verified with `shadcn diff`
- **Outcome:** Components work correctly, no updates needed

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

**Ready for Phase 12 UAT:**
- All components are official CLI-generated versions matching registry exactly
- `shadcn diff` reports no updates needed
- Quality gates pass (typecheck, lint, test, format)
- E2e tests pass using system Chromium
- No Playwright browser cache needed (~180 MB saved on container rebuild)

**Ready for Phase 13 (Login UI):**
- Component library is official and maintainable via CLI
- Future component additions: `cd libs/ui && PATH="/tmp/bin:$PATH" npx shadcn add <component>`
- Components use correct monorepo import paths (@workspace/ui/*)

**No blockers or concerns.**

---
*Phase: 12-frontend-infrastructure*
*Completed: 2026-02-10*
