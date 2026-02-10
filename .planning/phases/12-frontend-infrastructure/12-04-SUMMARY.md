---
phase: 12-frontend-infrastructure
plan: 04
subsystem: ui
tags: [shadcn-ui, react, tailwind, radix-ui, cva, monorepo]

# Dependency graph
requires:
  - phase: 12-03
    provides: Tailwind CSS v4 with dark mode, CSS variables, globals.css
provides:
  - libs/ui internal package with @workspace/ui exports
  - shadcn/ui components: Button, Card, Input, Label
  - cn() utility (clsx + tailwind-merge)
  - App shell with sidebar layout and component demo
affects: [12-05, frontend-development]

# Tech tracking
tech-stack:
  added:
    - clsx ^2.1.1
    - tailwind-merge ^3.4.0
    - class-variance-authority ^0.7.1
    - "@radix-ui/react-slot ^1.2.4"
    - "@radix-ui/react-label ^2.1.8"
  patterns:
    - Internal package pattern (no build step, direct TS imports)
    - shadcn/ui new-york style components
    - Button variants with cva (default/destructive/outline/secondary/ghost/link)
    - Card family pattern (Card/CardHeader/CardTitle/CardDescription/CardContent/CardFooter)
    - Sidebar layout with --sidebar-width CSS variable
    - Dark mode toggle with localStorage persistence

key-files:
  created:
    - libs/ui/package.json (@workspace/ui exports)
    - libs/ui/tsconfig.json
    - libs/ui/components.json (shadcn CLI config)
    - libs/ui/src/lib/utils.ts (cn utility)
    - libs/ui/src/components/button.tsx
    - libs/ui/src/components/card.tsx
    - libs/ui/src/components/input.tsx
    - libs/ui/src/components/label.tsx
    - libs/ui/src/index.ts (barrel exports)
  modified:
    - apps/web/src/app/app.tsx (sidebar layout + component demo)
    - .gitignore (allow libs/ui/src/lib/ for shadcn convention)

key-decisions:
  - "Use internal package pattern (no dist/, direct TS imports) for faster iteration"
  - "Manual component creation due to no internet access (shadcn CLI failed)"
  - "shadcn/ui new-york style for component aesthetics"
  - "Fix .gitignore to allow libs/ui/src/lib/ while blocking Python lib/"

patterns-established:
  - "Internal UI library: @workspace/ui with direct TS imports via tsconfig paths + nxViteTsPaths()"
  - "Component exports: Named exports with variants (e.g., buttonVariants)"
  - "cn() utility: Standard pattern for className merging (clsx + tailwind-merge)"
  - "Card family: Composable subcomponents (CardHeader, CardTitle, etc.)"

# Metrics
duration: 4min
completed: 2026-02-10
---

# Phase 12 Plan 04: libs/ui + shadcn/ui components + app shell Summary

**Internal @workspace/ui package with shadcn/ui Button, Card, Input, Label components and app shell demonstrating sidebar layout with dark mode toggle**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-10T07:06:55Z
- **Completed:** 2026-02-10T07:11:27Z
- **Tasks:** 2
- **Files modified:** 11

## Accomplishments
- Internal libs/ui package configured with @workspace/ui exports (no build step)
- shadcn/ui components manually created (Button with cva variants, Card family, Input, Label)
- App shell with left sidebar navigation and account balance cards
- Dark mode toggle button integrated into sidebar with localStorage persistence
- TypeScript compilation verified for both libs/ui and apps/web

## Task Commits

Each task was committed atomically:

1. **Task 1: Set up libs/ui as internal package with shadcn/ui components** - `204980f` (feat)
2. **Task 2: Create app shell with sidebar layout and shadcn component demo** - `291852a` (feat)

## Files Created/Modified
- `libs/ui/package.json` - @workspace/ui internal package with exports for components, hooks, lib
- `libs/ui/tsconfig.json` - TypeScript config extending workspace base
- `libs/ui/components.json` - shadcn/ui CLI config for monorepo (aliases point to @workspace/ui paths)
- `libs/ui/src/lib/utils.ts` - cn() utility combining clsx and tailwind-merge
- `libs/ui/src/components/button.tsx` - Button with cva variants (default/destructive/outline/secondary/ghost/link) and sizes (default/sm/lg/icon)
- `libs/ui/src/components/card.tsx` - Card component family (Card/CardHeader/CardTitle/CardDescription/CardContent/CardFooter)
- `libs/ui/src/components/input.tsx` - Styled native input with focus ring and shadow
- `libs/ui/src/components/label.tsx` - Radix UI label with cva integration
- `libs/ui/src/index.ts` - Barrel exports for all components and utilities
- `apps/web/src/app/app.tsx` - App shell with sidebar (account nav, dark mode toggle) and main content (balance cards, transaction form)
- `.gitignore` - Updated to allow libs/ui/src/lib/ (shadcn convention) while keeping Python lib/ ignored

## Decisions Made

**1. Internal package pattern (no build step)**
- Rationale: Faster iteration, simpler tooling. Vite + tsconfig paths resolve imports directly from source.
- Alternative considered: Building libs/ui with tsc → rejected due to added complexity and slower DX.

**2. Manual component creation**
- Rationale: Environment has no external internet access. shadcn CLI failed with "request to https://ui.shadcn.com/r/styles/new-york-v4/button.json failed".
- Manually created components from shadcn/ui new-york style patterns to maintain consistency.

**3. .gitignore fix for libs/ui/src/lib/**
- Issue: Root .gitignore had `lib/` pattern from Python conventions, blocking libs/ui/src/lib/.
- Fix: Made pattern more specific (`apps/*/lib/`, `libs/*/lib/`) with explicit exception `!libs/ui/src/lib/`.
- Rationale: shadcn/ui convention uses src/lib/ for utilities. Don't want to fight the convention.

**4. shadcn/ui new-york style**
- Rationale: new-york style has refined aesthetics (rounded-xl borders, subtle shadows). Matches modern finance app feel.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed .gitignore blocking libs/ui/src/lib/**
- **Found during:** Task 1 (staging libs/ui/src/lib/utils.ts)
- **Issue:** Root .gitignore had `lib/` pattern from Python conventions, blocking git add
- **Fix:** Updated .gitignore to use `apps/*/lib/` and `libs/*/lib/` patterns with explicit exception `!libs/ui/src/lib/`
- **Files modified:** .gitignore
- **Verification:** `git add libs/ui/src/lib/utils.ts` succeeded
- **Committed in:** 204980f (Task 1 commit)

**2. [Rule 3 - Blocking] Manual component creation (shadcn CLI unavailable)**
- **Found during:** Task 1 (attempting `npx shadcn@latest add button card input label`)
- **Issue:** CLI failed with "request to https://ui.shadcn.com/r/styles/new-york-v4/button.json failed" due to no internet access
- **Fix:** Manually created components using shadcn/ui new-york style patterns from known component structure
- **Files created:** button.tsx, card.tsx, input.tsx, label.tsx (all following shadcn conventions)
- **Verification:** TypeScript compilation passed for libs/ui and apps/web
- **Committed in:** 204980f (Task 1 commit)

---

**Total deviations:** 2 auto-fixed (2 blocking)
**Impact on plan:** Both auto-fixes necessary to unblock task completion. No scope creep. Plan anticipated CLI might fail and provided manual fallback instructions.

## Issues Encountered

**shadcn CLI network failure**
- Issue: `npx shadcn@latest add` failed with network error (no internet access in environment)
- Resolution: Plan anticipated this. Used manual fallback approach: installed dependencies via pnpm, manually created component files from shadcn/ui patterns.
- Outcome: Components created successfully, functionality identical to CLI-generated components.

**Multiple nx serve processes**
- Issue: Background `npx nx serve web` task showed "Waiting for web:serve in another nx process"
- Resolution: Earlier vite process (PID 55630) was already serving on port 5173. Verified server working via curl.
- Outcome: Dev server functional, manual verification completed.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

**Ready for Phase 12 Plan 05:**
- @workspace/ui package fully functional with Button, Card, Input, Label
- App shell demonstrates sidebar layout pattern
- Dark mode toggle working with localStorage persistence
- TypeScript compilation clean for both libs/ui and apps/web
- tsconfig paths + nxViteTsPaths resolving @workspace/ui imports correctly

**Established patterns:**
- Internal package pattern for UI library (no build step)
- shadcn/ui component structure and styling conventions
- Sidebar layout with CSS variable for width
- Dark mode persistence with localStorage + useEffect

**No blockers or concerns.**

---
*Phase: 12-frontend-infrastructure*
*Completed: 2026-02-10*
