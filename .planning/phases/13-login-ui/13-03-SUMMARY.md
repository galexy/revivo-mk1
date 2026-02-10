---
phase: 13-login-ui
plan: 03
subsystem: auth
tags: [react, tanstack-router, auth-context, cookies, jwt]

# Dependency graph
requires:
  - phase: 13-01
    provides: "HTTP client with token refresh interceptor and cookie handling"
  - phase: 13-02
    provides: "shadcn/ui Form, Checkbox, DropdownMenu, Avatar components"
provides:
  - "AuthContext provider with optimistic token refresh on mount"
  - "useAuth hook for consuming auth state across components"
  - "ProtectedRoute component for guarding authenticated routes"
  - "TanStack Router route tree with type-safe navigation"
affects: [13-04, 13-05, 13-06, authentication, routing, navigation]

# Tech tracking
tech-stack:
  added: ["@tanstack/react-router route definitions"]
  patterns:
    - "AuthContext with optimistic refresh via /auth/refresh on mount"
    - "AbortController cleanup for StrictMode double-mount prevention"
    - "Form-encoded body for OAuth2PasswordRequestForm compatibility"
    - "window.location.href for logout redirect (full state reset)"
    - "Route-level beforeLoad for auth guards with context injection"
    - "Router type registration for type-safe navigation"
    - "ProtectedRoute layout with loading state"

key-files:
  created:
    - "apps/web/src/features/auth/context/AuthContext.tsx"
    - "apps/web/src/features/auth/context/useAuth.ts"
    - "apps/web/src/features/auth/components/ProtectedRoute.tsx"
    - "apps/web/src/routes.tsx"
  modified:
    - "apps/web/src/main.tsx"
    - "apps/web/src/app/App.tsx"

key-decisions:
  - "Use window.location.href for logout redirect instead of router.navigate for clean state reset"
  - "Auth guard logic in route beforeLoad rather than component useEffect for type-safe redirects"
  - "Form-encoded URLSearchParams body for /auth/token to match OAuth2PasswordRequestForm"
  - "AbortController in refresh useEffect prevents StrictMode double-mount race condition"
  - "isLoading state starts true, prevents flash of login page during auth check"

patterns-established:
  - "AuthContext provides: user, isAuthenticated, isLoading, login, logout"
  - "useAuth hook validates context exists, throws error if outside provider"
  - "ProtectedRoute shows loading spinner while isLoading, redirects if !isAuthenticated"
  - "Route context injection via RouterProvider context={{ auth }}"
  - "beforeLoad redirects with throw redirect({ to })"

# Metrics
duration: 2min
completed: 2026-02-10
---

# Phase 13 Plan 03: Auth Context & Router Summary

**AuthContext with optimistic refresh, useAuth hook, ProtectedRoute guard, and TanStack Router with type-safe route tree**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-10T23:37:32Z
- **Completed:** 2026-02-10T23:39:38Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- AuthProvider attempts silent token refresh on mount, fetches user profile from /auth/me
- useAuth() hook exposes user, isAuthenticated, isLoading, login, logout
- login() method handles form-encoded OAuth2 body, stores token and profile
- logout() method clears server cookie and client state, full page reload
- ProtectedRoute component guards authenticated routes with loading state
- TanStack Router route tree: /login, /register, /verify (public), /dashboard (protected), / (redirect)
- Route-level beforeLoad auth checks with context injection
- Router type registration enables type-safe navigation

## Task Commits

Each task was committed atomically:

1. **Task 1: Create AuthContext provider with optimistic refresh and useAuth hook** - `525dd6e` (feat)
2. **Task 2: Create ProtectedRoute and set up TanStack Router routing** - `c2ed09c` (feat)

## Files Created/Modified

**Created:**
- `apps/web/src/features/auth/context/AuthContext.tsx` - Auth state manager with token refresh, login/logout
- `apps/web/src/features/auth/context/useAuth.ts` - Hook for consuming auth context with validation
- `apps/web/src/features/auth/components/ProtectedRoute.tsx` - Route guard with loading state
- `apps/web/src/routes.tsx` - TanStack Router route tree with auth guards

**Modified:**
- `apps/web/src/main.tsx` - Router setup with auth context injection
- `apps/web/src/app/App.tsx` - Marked as legacy, preserved for Plan 05 reference

## Decisions Made

**1. Use window.location.href for logout redirect**
- Rationale: Full page reload clears all state (router cache, component state, etc.) and avoids coupling AuthContext to TanStack Router
- Alternative considered: router.navigate() - but requires injecting router into context
- Trade-off: Less elegant but more reliable state cleanup

**2. Auth guard in beforeLoad instead of component useEffect**
- Rationale: TanStack Router's beforeLoad provides type-safe redirects with context
- Benefit: ProtectedRoute component only handles loading state, not redirect logic
- Pattern: `throw redirect({ to })` is idiomatic TanStack Router

**3. Form-encoded body for /auth/token**
- Rationale: Backend uses OAuth2PasswordRequestForm which requires application/x-www-form-urlencoded
- Implementation: URLSearchParams with explicit Content-Type header
- Note: remember_me param controls session vs persistent cookie

**4. AbortController cleanup in refresh useEffect**
- Rationale: React StrictMode double-mounts components in dev, can cause race condition
- Pattern: controller.abort() in cleanup, check !controller.signal.aborted before setState
- Prevents: "Can't perform state update on unmounted component" warning

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

**Ready for Plan 04 (Login & Register Pages):**
- AuthContext provides login() method accepting email, password, rememberMe
- /login route exists with placeholder component
- /register route exists with placeholder component
- Router context provides auth state for conditional rendering

**Ready for Plan 05 (Dashboard Page):**
- /dashboard route exists with placeholder component
- ProtectedRoute guards dashboard from unauthenticated access
- AuthContext provides user profile with display_name
- Legacy App.tsx contains sidebar + dark mode toggle for reference

**Ready for Plan 06 (Email Verification Page):**
- /verify route exists with placeholder component
- AuthContext already handling email_verified status in user profile
- Router useSearch() available for ?token= query param

**No blockers:** All auth infrastructure in place for UI pages.

---
*Phase: 13-login-ui*
*Completed: 2026-02-10*
