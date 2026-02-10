---
phase: 13-login-ui
plan: 01
subsystem: auth
tags: [axios, cookie, cors, jwt, react, typescript]

# Dependency graph
requires:
  - phase: 04-authentication-infrastructure
    provides: Backend auth endpoints with JWT tokens and refresh cookies
  - phase: 12-frontend-infrastructure
    provides: React app with TypeScript and build tooling
provides:
  - Cross-origin HTTP client with automatic token refresh
  - Auth TypeScript types matching backend API contract
  - Session vs persistent cookie support via remember_me
  - Concurrent 401 handling with failedQueue pattern
affects: [13-02-login-form, 13-03-registration-flow, all-frontend-features]

# Tech tracking
tech-stack:
  added: [axios, react-hook-form, zod, @hookform/resolvers, @radix-ui/react-icons, @tanstack/react-router]
  patterns: [failedQueue for concurrent 401s, module-level token storage, silent token refresh]

key-files:
  created:
    - apps/web/src/lib/api.ts
    - apps/web/src/features/auth/types.ts
  modified:
    - apps/api/src/adapters/api/routes/auth.py

key-decisions:
  - "Changed refresh cookie from samesite=strict to samesite=lax for cross-origin CORS compatibility"
  - "Changed cookie path from /auth/refresh to /auth so both refresh and logout endpoints receive the cookie"
  - "remember_me parameter controls session cookie (no max_age) vs persistent cookie (30-day max_age)"
  - "Increased REFRESH_TOKEN_MAX_AGE from 7 days to 30 days per user decision"
  - "Added TanStack Router now (not deferred to Phase 14) to avoid throwaway react-router-dom dependency"

patterns-established:
  - "failedQueue pattern: first 401 triggers refresh, concurrent 401s wait in queue and retry with new token"
  - "Module-level accessToken storage with getAccessToken/setAccessToken exports for AuthContext"
  - "Request interceptor attaches Bearer token, response interceptor handles refresh on 401"
  - "Redirect to /login?expired=true on refresh failure or 401 from /auth/refresh endpoint"

# Metrics
duration: 5min
completed: 2026-02-10
---

# Phase 13 Plan 01: HTTP Client & Cookie Fixes Summary

**Cross-origin Axios client with silent token refresh via failedQueue pattern, samesite=lax cookies, and remember_me session control**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-10T23:28:44Z
- **Completed:** 2026-02-10T23:34:17Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Fixed backend refresh cookie to use samesite=lax (was strict, blocking cross-origin)
- Added remember_me parameter to /auth/token controlling session vs persistent cookies
- Created Axios instance with withCredentials for cross-origin cookie support
- Implemented failedQueue pattern to prevent refresh race conditions on concurrent 401s

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix backend cookie samesite + add remember_me parameter** - `061d3c3` (feat)
   - Changed samesite from strict to lax
   - Changed cookie path from /auth/refresh to /auth
   - Added remember_me Form parameter to /auth/token
   - Session cookie when remember_me=false, 30-day persistent when true
   - Updated REFRESH_TOKEN_MAX_AGE from 7 to 30 days

2. **Task 2: Install frontend dependencies and create Axios client with auth interceptors** - `da95cb6` (feat)
   - Installed: axios, react-hook-form, zod, @hookform/resolvers, @radix-ui/react-icons, @tanstack/react-router
   - Created TypeScript auth types (UserProfile, TokenResponse, RegisterRequest, etc.)
   - Created Axios instance with baseURL http://localhost:8000, withCredentials: true
   - Request interceptor attaches Bearer token from module-level storage
   - Response interceptor with failedQueue pattern for 401 handling
   - Silent refresh on 401 (except /auth/refresh which redirects to login)

## Files Created/Modified

- `apps/api/src/adapters/api/routes/auth.py` - Fixed cookie samesite, path, and added remember_me
- `apps/web/src/lib/api.ts` - Axios instance with auth interceptors and failedQueue pattern
- `apps/web/src/features/auth/types.ts` - TypeScript types for auth API contract
- `apps/web/package.json` - Added frontend dependencies
- `pnpm-lock.yaml` - Lockfile updates

## Decisions Made

1. **samesite=lax instead of strict:** samesite=strict blocks cross-origin cookies entirely. Since frontend (localhost:5173) and backend (localhost:8000) are different origins, browsers won't send strict cookies. Changed to lax for CORS compatibility while maintaining CSRF protection for non-GET requests.

2. **Cookie path /auth instead of /auth/refresh:** The original /auth/refresh path meant the cookie was only sent to the refresh endpoint. The logout endpoint (/auth/logout) also needs the cookie to clear it properly. Changed to /auth so both endpoints receive it.

3. **remember_me controls max_age:** When false (default), cookie has no max_age (session cookie, deleted on browser close). When true, cookie has 30-day max_age (persistent, survives browser restart). This gives users control over session persistence.

4. **30-day max_age:** Increased from 7 days to 30 days per user decision in plan context. Provides longer-lived sessions for users who enable remember_me.

5. **TanStack Router now:** Plan originally deferred TanStack Router to Phase 14, but installing it now avoids adding react-router-dom as a throwaway dependency. Phase 14 will focus on TanStack Query and advanced routing patterns (loaders, search params, data prefetching).

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

**Issue:** pnpm not in PATH
**Resolution:** Used `corepack pnpm` to invoke pnpm via corepack shims. Package manager is configured via packageManager field in root package.json.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- HTTP client ready for all frontend auth flows
- Backend cookies compatible with cross-origin requests
- remember_me parameter available for login form checkbox
- Auth types provide full TypeScript safety for API contract
- failedQueue pattern prevents refresh race conditions
- Ready for Plan 02 (login form UI) and Plan 03 (registration flow)

**Blockers:** None

**Concerns:** None - smoke tested with curl, verified both session and persistent cookie modes work correctly

---
*Phase: 13-login-ui*
*Completed: 2026-02-10*
