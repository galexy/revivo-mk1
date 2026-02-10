# Phase 13: Login UI - Context

**Gathered:** 2026-02-10
**Status:** Ready for planning

<domain>
## Phase Boundary

User authentication interface for the web app. Includes login page, registration page, email verification landing page, logout, and session/token management in the browser. The backend auth API already exists (Phase 4) — this phase builds the frontend that consumes it.

Out of scope: OAuth/social login (Phase 30), password reset (Phase 27), TanStack Router/Query setup (Phase 14).

</domain>

<decisions>
## Implementation Decisions

### Login form design
- Centered card layout on page with logo above — clean, minimal (Linear/Vercel style)
- App name + logo/icon displayed above the form
- Password field has show/hide eye icon toggle
- "Remember me" checkbox included
- No "Forgot password?" link (Phase 27 implements actual reset — no dead links)
- Registration link below form: "Don't have an account? Sign up"
- Email/password only — no OAuth buttons (Phase 30)

### Registration form
- Separate page (linked from login)
- Fields: email, password, display name
- After successful registration: show verification notice ("Check your email to verify") — do NOT auto-login
- User must verify email before logging in

### Error display
- Claude's discretion on error display pattern (inline vs banner) — pick what fits shadcn/ui best

### Auth flow & redirects
- After successful login: redirect to dashboard/home page
- Root URL (/) behavior: authenticated users go to dashboard, unauthenticated go to login
- Unauthenticated users hitting protected routes: silent redirect to /login (no toast/message)
- Email verification: dedicated /verify?token=... page showing success/failure, with link to login
- Expired verification tokens: show "Token expired" message + button to resend verification email
- Loading state during login: Claude's discretion

### Token & session management
- JWT access token stored in-memory only (JS variable/React state) — lost on page refresh
- Refresh token as HttpOnly cookie (existing Phase 4 setup)
- "Remember me" controls cookie persistence: unchecked = session cookie (lost on browser close), checked = persistent cookie (30-day)
- On page refresh: optimistic approach — render app shell immediately, refresh token in background, block API calls until new JWT arrives
- Silent token refresh: when access token expires, automatically call /auth/refresh and retry the failed request — user never sees interruption
- Session expiry (refresh token expired): redirect to /login with "Your session has expired. Please log in again." message

### Auth React context
- Full auth context provider with useAuth() hook
- Exposes: user, login(), logout(), isAuthenticated, isLoading
- Pre-fetches /auth/me after obtaining token — caches user profile (name, email, avatar initials, household) in context

### Refresh coordination
- Claude's discretion on whether to queue concurrent 401 refresh attempts or retry independently

### Logout experience
- Logout action in user menu dropdown (click user avatar/name in header area)
- User menu shows avatar/initials circle + display name
- No confirmation dialog — click "Log out" triggers immediate logout
- After logout: redirect to /login (no toast)

### Auth loading screen
- Claude's discretion on what to show while determining auth status on first load

### Claude's Discretion
- Error display pattern (inline below fields vs top banner)
- Loading/transition state during login submission
- Auth loading screen on first app load (splash vs blank)
- Refresh token queue coordination pattern
- Exact layout spacing, typography choices within shadcn/ui system

</decisions>

<specifics>
## Specific Ideas

- Centered card layout like Linear or Vercel login pages — minimal, not busy
- Avatar in user menu should be initials-based (no image upload exists yet)
- In-memory JWT + HttpOnly refresh cookie is the security model — no localStorage for tokens
- Optimistic page load: show the app shell while background-fetching the token, don't make the user stare at a blank screen

</specifics>

<deferred>
## Deferred Ideas

- OAuth/social login buttons — Phase 30
- "Forgot password?" link — Phase 27 (password reset)
- Deep link preservation (redirect back to original URL after login) — could revisit in Phase 14 with TanStack Router
- User avatar image upload — Phase 32 (User Preferences & Profile)

</deferred>

---

*Phase: 13-login-ui*
*Context gathered: 2026-02-10*
