---
phase: 13-login-ui
plan: 04
subsystem: ui
tags: [react, tanstack-router, react-hook-form, zod, shadcn-ui, authentication]

# Dependency graph
requires:
  - phase: 13-03
    provides: AuthContext, useAuth hook, TanStack Router configuration
provides:
  - Login page with email/password/remember-me form
  - Registration page with email/password/display-name form
  - Password field with eye toggle visibility control
  - Form validation with Zod schemas
  - Type-safe routing with search params
affects: [13-05-email-verification, 13-06-dashboard]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Centered card layout for auth pages (Linear/Vercel style)"
    - "PasswordInput with forwardRef for react-hook-form compatibility"
    - "Form error handling: field-level via FormMessage, server errors via banner"
    - "Optional search params in TanStack Router with validateSearch return type"

key-files:
  created:
    - apps/web/src/features/auth/validation.ts
    - apps/web/src/features/auth/components/PasswordInput.tsx
    - apps/web/src/features/auth/components/LoginForm.tsx
    - apps/web/src/features/auth/components/RegisterForm.tsx
    - apps/web/src/pages/LoginPage.tsx
    - apps/web/src/pages/RegisterPage.tsx
  modified:
    - apps/web/src/routes.tsx

key-decisions:
  - "Login form validates non-empty password (server handles actual validation)"
  - "Registration form mirrors backend password rules for immediate feedback"
  - "Registration success shows verification notice, does NOT auto-login"
  - "Authenticated users redirected to /dashboard via useEffect in page components"
  - "Search params made optional with validateSearch return type annotation"

patterns-established:
  - "PasswordInput uses forwardRef + tabIndex=-1 on toggle button"
  - "Server errors displayed as destructive banner above submit button"
  - "Form submission loading state shows alternate button text + disabled"
  - "Link to="/path" search={{}} pattern for optional search params"

# Metrics
duration: 3min
completed: 2026-02-10
---

# Phase 13 Plan 04: Login & Registration Pages Summary

**Login and registration pages with Zod validation, password visibility toggle, inline error display, and centered card layout**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-10T23:42:26Z
- **Completed:** 2026-02-10T23:45:50Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- Login page with email, password (with eye toggle), remember me checkbox, and server error handling
- Registration page with email, password, display name fields showing verification notice on success
- Zod validation schemas matching backend password rules for immediate client-side feedback
- Centered card layout (Linear/Vercel style) for both auth pages with authenticated user redirect

## Task Commits

Each task was committed atomically:

1. **Task 1: Create Zod validation schemas and PasswordInput component** - `6a449d2` (feat)
2. **Task 2: Create LoginForm, RegisterForm, and their page wrappers** - `3cabdae` (feat)

## Files Created/Modified
- `apps/web/src/features/auth/validation.ts` - Zod schemas for login (email/password/rememberMe) and register (email/password/displayName with backend validation rules)
- `apps/web/src/features/auth/components/PasswordInput.tsx` - Password input with eye toggle using forwardRef for react-hook-form
- `apps/web/src/features/auth/components/LoginForm.tsx` - Login form with react-hook-form, calls useAuth().login(), navigates to /dashboard on success
- `apps/web/src/features/auth/components/RegisterForm.tsx` - Registration form with api.post('/auth/register'), shows verification notice on success (no auto-login)
- `apps/web/src/pages/LoginPage.tsx` - Centered card layout wrapping LoginForm with authenticated redirect
- `apps/web/src/pages/RegisterPage.tsx` - Centered card layout wrapping RegisterForm with authenticated redirect
- `apps/web/src/routes.tsx` - Updated login/register routes to use real page components, fixed validateSearch to return optional search params

## Decisions Made

**Password visibility toggle implementation:**
- Used EyeOpenIcon/EyeClosedIcon from @radix-ui/react-icons
- Toggle button has tabIndex={-1} to keep tab order on input
- Button positioned absolute with right-2 top-1/2 -translate-y-1/2

**Search params type safety:**
- TanStack Router validateSearch requires explicit return type for optional params
- Pattern: `validateSearch: (search): { param?: Type } => ({ param: value })`
- All Link and navigate calls include `search={{}}` for type safety

**Error display strategy:**
- Field-level errors: FormMessage component below each field (shadcn/ui pattern)
- Server errors: Destructive banner above submit button with extracted error.response?.data?.detail
- 422 validation errors: Extract field name from FastAPI error format and set field-level errors

**Registration flow:**
- On success: Show "Check your email to verify your account" message
- Does NOT call useAuth().login() per user decision (no auto-login)
- Replaces form with success message + "Back to login" link

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed TanStack Router search params type errors**
- **Found during:** Task 2 typecheck
- **Issue:** validateSearch return type defaulted to required params, causing Link and navigate calls to fail typecheck with missing 'search' property
- **Fix:** Added explicit return type annotation `{ expired?: boolean }` and `{ token?: string }` to validateSearch functions, updated all Link/navigate/redirect calls to include `search: {}`
- **Files modified:** apps/web/src/routes.tsx, apps/web/src/features/auth/components/RegisterForm.tsx (auto-formatted by linter)
- **Verification:** `npx nx typecheck web` passes
- **Committed in:** 3cabdae (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking type error)
**Impact on plan:** Essential fix for type safety. No scope creep - TanStack Router requires explicit search param handling.

## Issues Encountered

**Auto-import system modified routes.tsx:**
- Auto-import added VerifyEmailPage and DashboardPage imports when creating page files
- Auto-import also updated verify and dashboard routes to use imported components
- This was outside plan scope but harmless - routes now reference real components instead of placeholders
- VerifyEmailPage had existing search param usage, requiring the validateSearch fix documented above

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

**Ready for Phase 13-05 (Email Verification):**
- Login page complete with link to register
- Registration page complete with email/password/displayName form
- Registration shows "Check your email" message after success
- Verify route configured with token search param (VerifyEmailPage already exists from previous plan)

**Ready for Phase 13-06 (Dashboard):**
- Login flow redirects to /dashboard on success
- DashboardPage component exists (from previous plan)
- Auth guard prevents unauthenticated access to protected routes

**No blockers or concerns**

---
*Phase: 13-login-ui*
*Completed: 2026-02-10*
