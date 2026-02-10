---
phase: 13-login-ui
plan: 05
subsystem: ui
tags: [react, tanstack-router, auth-ui, email-verification]

# Dependency graph
requires:
  - phase: 13-03
    provides: AuthContext with login/logout, TanStack Router setup with auth guards
  - phase: 13-04
    provides: LoginPage and RegisterPage components
provides:
  - VerifyEmailPage handling email verification link flow
  - UserMenu dropdown with avatar initials and logout
  - DashboardPage shell with sidebar layout and header
  - Session expired message on /login?expired=true
  - All placeholder route components replaced with real implementations
affects: [13-06-account-list, future-dashboard-features]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - validateSearch for optional URL search params in TanStack Router
    - Initials generation from display_name (first + last word)
    - Session expired message via URL search param
    - Email resend via re-registration (enumeration protection)

key-files:
  created:
    - apps/web/src/pages/VerifyEmailPage.tsx
    - apps/web/src/features/auth/components/UserMenu.tsx
    - apps/web/src/pages/DashboardPage.tsx
  modified:
    - apps/web/src/routes.tsx
    - apps/web/src/pages/LoginPage.tsx
    - apps/web/src/features/auth/components/RegisterForm.tsx

key-decisions:
  - "validateSearch returns optional types ({ expired?: boolean }) to make search params optional for type-safe navigation"
  - "Email resend on expired token uses POST /auth/register (enumeration protection via always-202 response)"
  - "UserMenu generates initials from first and last word of display_name (max 2 chars)"
  - "Logout is immediate (no confirmation dialog) per plan specification"
  - "Session expired message shown on /login?expired=true from api.ts interceptor"

patterns-established:
  - "validateSearch with optional types for routes that support optional query params"
  - "navigate({ to: '/path', search: {} }) for routes with validateSearch to satisfy type checker"
  - "DashboardPage owns sidebar + header layout (not App.tsx)"
  - "Dark mode state managed in DashboardPage (localStorage + useEffect)"

# Metrics
duration: 4min
completed: 2026-02-10
---

# Phase 13 Plan 05: Email Verification, User Menu & Dashboard Shell

**Email verification page with token handling, user menu with avatar and immediate logout, dashboard shell with sidebar layout and header**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-10T23:42:50Z
- **Completed:** 2026-02-10T23:46:10Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- VerifyEmailPage handles GET /auth/verify with loading, success, error, and expired states
- Expired token flow includes email resend via re-registration
- UserMenu dropdown with avatar initials, display name, and logout
- DashboardPage with sidebar, header, UserMenu, and placeholder content
- All route placeholders replaced with real page components

## Task Commits

Each task was committed atomically:

1. **Task 1: Create VerifyEmailPage** - `b332d81` (feat)
2. **Task 2: Create UserMenu and DashboardPage, wire into routes** - `985eb8a` (feat)

## Files Created/Modified
- `apps/web/src/pages/VerifyEmailPage.tsx` - Email verification page with token handling and resend flow
- `apps/web/src/features/auth/components/UserMenu.tsx` - User dropdown with avatar initials and logout
- `apps/web/src/pages/DashboardPage.tsx` - Dashboard shell with sidebar, header, and UserMenu
- `apps/web/src/routes.tsx` - Added validateSearch to verify and login routes, replaced placeholders
- `apps/web/src/pages/LoginPage.tsx` - Added session expired message for ?expired=true
- `apps/web/src/features/auth/components/RegisterForm.tsx` - Fixed Link components with search param

## Decisions Made

1. **validateSearch with optional types**: TanStack Router requires search params to be provided when navigating if validateSearch is present. Made expired and token optional ({ expired?: boolean }, { token?: string }) so routes can be navigated without search params.

2. **Email resend via re-registration**: On expired token, users can enter email and submit. The UI calls POST /auth/register which returns 202 even for duplicate emails (enumeration protection). This triggers a new verification email without leaking whether the account exists.

3. **Initials generation logic**: UserMenu generates avatar initials from display_name by taking first letter of first word + first letter of last word (max 2 chars). For single-word names, takes first 2 characters.

4. **Logout is immediate**: Per plan specification, clicking "Log out" triggers logout immediately with no confirmation dialog. Uses AuthContext.logout() which calls API, clears state, and redirects to /login.

5. **Session expired message**: When api.ts interceptor detects expired refresh token (401 on /auth/refresh), it redirects to /login?expired=true. LoginPage shows yellow banner with "Your session has expired. Please log in again."

6. **DashboardPage owns layout**: Moved sidebar layout and dark mode toggle from App.tsx to DashboardPage. DashboardPage is now the post-login landing page with full layout (sidebar + header + main content).

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

**TanStack Router type safety with validateSearch**: When adding validateSearch to loginRoute and verifyRoute, TypeScript required all navigate/redirect calls to include the search parameter. Fixed by:
1. Making search params optional in validateSearch return type
2. Adding `search: {}` to all navigate({ to: '/login' }) calls
3. Fixed in routes.tsx, VerifyEmailPage, LoginPage, RegisterForm

This is expected behavior (not a bug) - TanStack Router enforces type-safe routing.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Email verification flow complete (verify link, expired resend, success → login)
- UserMenu with logout functional (immediate logout, full page redirect)
- Dashboard shell ready for account list and transaction features
- All route placeholders removed - routing is complete
- Ready for 13-06 (Account List UI) to populate sidebar and main content

---
*Phase: 13-login-ui*
*Completed: 2026-02-10*
