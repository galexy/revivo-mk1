---
phase: 13-login-ui
plan: 06
subsystem: ui
tags: [react, vitest, auth-testing, e2e-verification, chrome-devtools]

# Dependency graph
requires:
  - phase: 13-04
    provides: LoginPage and RegisterPage components
  - phase: 13-05
    provides: VerifyEmailPage, UserMenu, DashboardPage, complete routing
provides:
  - Unit tests for LoginForm (7 cases), AuthContext (6 cases), App routing (2 cases)
  - Bug fixes for auth redirect loop, stuck loading, form submission reload, post-login navigation
  - Verified end-to-end login-to-logout cycle via Chrome DevTools
affects: [phase-14-frontend-api-routing]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - router.invalidate() to re-evaluate beforeLoad guards on auth state change
    - window.location.href for post-login redirect (avoids router context race)
    - Skip token refresh for all /auth/ endpoints in Axios interceptor
    - ResizeObserver mock in test-setup.ts for radix-ui components
    - dangerouslyIgnoreUnhandledErrors for TanStack Router in test environment

key-files:
  created:
    - apps/web/src/features/auth/components/LoginForm.test.tsx
    - apps/web/src/features/auth/context/AuthContext.test.tsx
    - apps/web/src/app/App.test.tsx
  modified:
    - apps/web/src/lib/api.ts
    - apps/web/src/main.tsx
    - apps/web/src/features/auth/components/LoginForm.tsx
    - apps/web/src/features/auth/components/RegisterForm.tsx
    - apps/web/src/test-setup.ts
    - apps/web/vite.config.ts

key-decisions:
  - "router.invalidate() in useEffect on [isLoading, isAuthenticated] to re-run beforeLoad guards when auth state changes"
  - "window.location.href for post-login redirect instead of TanStack Router navigate() to avoid context race condition"
  - "Skip token refresh for ALL /auth/ endpoints (not just /auth/refresh) to prevent form submission page reloads"
  - "noValidate on auth forms to let react-hook-form handle validation instead of browser HTML5 validation"
  - "ResizeObserver mock in test-setup.ts for radix-ui dropdown components"
  - "dangerouslyIgnoreUnhandledErrors in router config for test environment"

patterns-established:
  - "router.invalidate() when React context changes affect TanStack Router beforeLoad guards"
  - "Full page navigation (window.location.href) when router context hasn't propagated yet"
  - "Auth endpoint exclusion pattern: check url.startsWith('/auth/') in interceptor"

# Metrics
duration: ~30min (including 4 bug fixes discovered during E2E)
completed: 2026-02-10
---

# Phase 13 Plan 06: Unit Tests & End-to-End Verification

**Unit tests for auth components/context plus full login-to-logout browser verification**

## Performance

- **Duration:** ~30 min (4 min executor + ~26 min E2E debugging/fixes)
- **Started:** 2026-02-10
- **Completed:** 2026-02-10
- **Tasks:** 2 (1 auto + 1 checkpoint:human-verify)
- **Files created:** 3
- **Files modified:** 6
- **Bugs fixed:** 4

## Accomplishments
- 17 unit tests across 4 test files (LoginForm: 7, AuthContext: 6, App routing: 2, existing: 2)
- Fixed auth redirect loop caused by interceptor redirecting on /auth/refresh 401
- Fixed stuck loading screen by adding router.invalidate() on auth state change
- Fixed form submission page reload by excluding all /auth/ endpoints from token refresh
- Fixed post-login navigation failure by using window.location.href instead of navigate()
- Full E2E verification via Chrome DevTools: login, register, logout, protected routes, session persistence

## Task Commits

Each task was committed atomically:

1. **Task 1a: Disable HTML5 validation** - `d609cf1` (fix)
2. **Task 1b: Configure test environment** - `f6d6c21` (test)
3. **Task 1c: Unit tests for auth components** - `cc95758` (test)
4. **Task 2: E2E bug fixes** - `7ab84c6` (fix)

## Files Created/Modified
- `apps/web/src/features/auth/components/LoginForm.test.tsx` - 7 test cases for login form
- `apps/web/src/features/auth/context/AuthContext.test.tsx` - 6 test cases for auth context
- `apps/web/src/app/App.test.tsx` - 2 test cases for routing guards
- `apps/web/src/lib/api.ts` - Fixed interceptor to skip refresh for all /auth/ endpoints
- `apps/web/src/main.tsx` - Added router.invalidate() on auth state change
- `apps/web/src/features/auth/components/LoginForm.tsx` - Changed to window.location.href for post-login redirect
- `apps/web/src/features/auth/components/RegisterForm.tsx` - Added noValidate attribute
- `apps/web/src/test-setup.ts` - Added ResizeObserver mock
- `apps/web/vite.config.ts` - Added dangerouslyIgnoreUnhandledErrors for test router

## Decisions Made

1. **router.invalidate() on auth state change**: TanStack Router's beforeLoad only runs during navigation events. When AuthProvider changes isLoading from true→false, route guards don't re-evaluate. Added useEffect in InnerApp that calls router.invalidate() on [auth.isLoading, auth.isAuthenticated] changes to trigger guard re-evaluation.

2. **window.location.href for post-login redirect**: TanStack Router's navigate({ to: '/dashboard' }) fires before React state update propagates to router context. The protected route's beforeLoad still sees isAuthenticated=false and redirects back to /login. Full page navigation via window.location.href ensures clean state.

3. **Skip refresh for all /auth/ endpoints**: Original interceptor only skipped refresh for /auth/refresh. A 401 from /auth/token (wrong credentials) triggered refresh → 401 on refresh → redirect to /login?expired=true (full page reload). Changed to skip all /auth/ endpoints since auth endpoint 401s have specific meanings (wrong password, not expired session).

4. **noValidate on auth forms**: HTML5 validation shows browser-native popups that conflict with react-hook-form/zod validation. Added noValidate to let the custom validation handle all error display.

## Deviations from Plan

1. **Bug fixes required**: Plan expected E2E to work after unit tests. In practice, 4 bugs discovered during Chrome DevTools verification that required code fixes (not just test fixes).
2. **ResizeObserver mock**: Radix UI dropdown components use ResizeObserver which isn't available in JSDOM. Added global mock in test-setup.ts.
3. **dangerouslyIgnoreUnhandledErrors**: TanStack Router throws unhandled errors from redirect() in test environment. Added config option to suppress.

## Bugs Fixed During E2E

| # | Bug | Root Cause | Fix |
|---|-----|-----------|-----|
| 1 | Infinite redirect loop on load | Interceptor redirected to /login?expired=true on /auth/refresh 401; AuthProvider always tries refresh on mount | Removed redirect from /auth/refresh 401 handler |
| 2 | Stuck on "Loading..." at / | TanStack Router beforeLoad doesn't re-run when React context changes | Added router.invalidate() in useEffect |
| 3 | Form submit causes page reload | /auth/token 401 triggered refresh attempt → /auth/refresh 401 → redirect | Skip refresh for all /auth/ endpoints |
| 4 | Post-login stays on /login | navigate() fires before auth context propagates to router | Changed to window.location.href = '/dashboard' |

## E2E Verification Results (Chrome DevTools)

All tests passed:
- Root "/" redirects to /login when unauthenticated
- Login → Register navigation works
- Registration shows verification notice (no auto-login)
- Login with bad credentials shows "Invalid credentials" error
- Login with valid credentials redirects to /dashboard
- Dashboard shows sidebar + UserMenu with user initials
- UserMenu dropdown with "Log out" works
- Logout redirects to /login
- Protected route /dashboard redirects to /login when unauthenticated
- Session persistence after page refresh works (stays on /dashboard)

## Next Phase Readiness

- Phase 13 (Login UI) is complete — all 5 success criteria met
- Auth flow verified end-to-end in real browser
- 17 unit tests provide regression safety
- Ready for Phase 14 (Frontend API & Routing) or Phase 12.1 (UI Acceptance Testing)

---
*Phase: 13-login-ui*
*Completed: 2026-02-10*
