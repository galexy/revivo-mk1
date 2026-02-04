# Phase 4: Authentication Infrastructure - Context

**Gathered:** 2026-02-04
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase establishes JWT-based authentication infrastructure for the API. Users will register and login via API endpoints, receive access and refresh tokens, and use those tokens to access protected routes. The phase introduces two new domain concepts: the User entity for authentication and the Household entity for data scoping.

The scope is deliberately limited to backend infrastructure. The login UI belongs to Phase 7 after frontend tooling is established. OIDC and social login will come in a future phase once email/password authentication proves stable. Password reset, rate limiting, and account lockout are security hardening features that can be layered on later without architectural changes.

</domain>

<decisions>
## Implementation Decisions

### User Identity

Email serves as the sole login identifier for this phase. This is the industry standard approach—users expect to log in with their email address, and it eliminates the friction of choosing and remembering a separate username. While OIDC support is desired for the future, starting with email/password establishes the foundational user model that OIDC will later authenticate against.

Password requirements follow the complexity approach: minimum 8 characters with at least one uppercase letter, one lowercase letter, one number, and one symbol. This balances security against usability. Pure length-based requirements (e.g., 12+ characters) are arguably more secure, but complexity rules are more familiar to users and easier to validate with clear error messages.

The User entity stores only essential fields: email, display name, and password hash. Additional metadata like timezone preferences, currency settings, or profile information is deferred to a future phase. This keeps the initial implementation focused on authentication rather than user preferences.

Registration requires email verification, and users cannot log in until verified. This prevents throwaway signups and ensures we have a valid communication channel with every user. The tradeoff is friction during onboarding, but for a financial application, verifying user identity from the start is worth that cost. Password reset functionality is deferred—it requires similar email infrastructure, and users who forget passwords during early development can simply re-register.

### Household Model

The Household entity introduces multi-user data ownership from the start. Rather than scoping accounts and transactions directly to a user, they belong to a household, and users belong to households. This design anticipates the common use case of families or couples managing finances together, where multiple people need access to the same set of accounts.

For this phase, the model is deliberately simple: one household per user, created automatically during registration. When a user registers, the system creates both a User and a Household in a single transaction, linking them together. The household has a display name (e.g., "Smith Family") for UI purposes. User invitations—allowing someone to join an existing household—are deferred to a future phase when we have email infrastructure proven and can handle the invitation flow properly.

Existing test data in the database needs a migration path. The migration will create a "Default" household and assign all existing accounts and transactions to it. This allows development to continue without losing test data while establishing the household foreign key constraints.

### User Context in Service Layer

The authenticated user context flows through the application via dependency injection. A `CurrentUser` dataclass holds the `user_id` and `household_id` extracted from the JWT. FastAPI's `Depends()` mechanism injects this into route handlers, which pass it to services. This approach keeps authentication concerns at the API boundary while giving services the information they need for data scoping and audit logging.

The `CurrentUser` dataclass is intentionally minimal—just two IDs. The service layer primarily needs `household_id` to filter queries (ensuring users only see their household's data) and `user_id` for audit trails (recording who performed an action). Loading the full User entity from the database on every request would add latency without providing information the services actually need. If a route needs additional user details, it can explicitly load them.

### Token Strategy

The token strategy uses separate access and refresh tokens to balance security with user experience. Access tokens are short-lived (15 minutes) and stored only in browser memory—never in localStorage where XSS attacks could steal them. Refresh tokens are longer-lived (7 days) and stored in HttpOnly, Secure, SameSite=Strict cookies that JavaScript cannot access.

This separation means that even if an attacker executes JavaScript on the page, they cannot steal tokens that persist beyond the current session. The refresh token in the HttpOnly cookie allows the SPA to silently obtain new access tokens on page load, so users don't need to re-authenticate every 15 minutes. They only need to log in again after 7 days of inactivity.

The JWT payload includes both `user_id` and `household_id`. This allows route handlers to authorize requests without a database lookup—the token itself carries enough information to scope queries to the correct household. The tradeoff is that if a user's household changes (not currently possible, but might be in future), they'd need a new token.

Refresh tokens are stored in the database rather than being purely stateless JWTs. This adds a database lookup on refresh, but enables future capabilities like session management and forced logout. When a refresh token is used, it rotates—the old token is invalidated and a new one is issued. This limits the window of exposure if a refresh token is somehow compromised.

Concurrent sessions are unlimited. Users can be logged in on their phone, laptop, and tablet simultaneously. Session management features like "logout all devices" are deferred, but the database-backed refresh tokens make this straightforward to add later.

### Login Flow

Authentication for this phase is email and password only. The login endpoint accepts credentials and returns an access token (in the response body) and a refresh token (set as an HttpOnly cookie). Failed login attempts return a generic "Invalid credentials" error regardless of whether the email exists or the password was wrong. This prevents attackers from enumerating valid email addresses.

Rate limiting and account lockout are deferred. These are important security features, but they require infrastructure (Redis for rate limiting, or careful database-backed counting) that adds complexity. The initial implementation assumes a trusted environment; hardening comes later.

### Route Protection

Public routes are limited to authentication endpoints (`/auth/*`), health checks (`/health`, `/ready`), and API documentation (`/docs`, `/openapi.json`). Everything else requires a valid JWT in the Authorization header.

All authentication failures return HTTP 401 with a JSON error body `{"detail": "Not authenticated"}`. This applies whether the token is missing, malformed, expired, or invalid. The client doesn't need to distinguish these cases—any 401 means "get a new token" (via refresh) or "log in again" (if refresh also fails).

Cross-household access attempts return 404 rather than 403. If a user requests an account that exists but belongs to another household, the response is "not found" rather than "forbidden." This prevents information leakage—attackers cannot probe for the existence of resources they don't own.

### API Changes for Household Scoping

Existing API endpoints gain household scoping through the service layer rather than URL changes. The current URL structure (`/api/v1/accounts`, `/api/v1/transactions`) remains unchanged. Services receive the `CurrentUser` and use `household_id` to filter all queries. This is transparent to clients—they simply see their own data.

The accounts and transactions tables require a new `household_id` foreign key column. A migration adds this column and populates it for existing data by creating a "Default" household. This is a breaking change in the sense that the database schema changes, but the API contract remains the same.

Existing E2E tests will use the real authentication flow rather than mocks or bypasses. Tests will register a user, log in, and use the resulting JWT for subsequent requests. This ensures the authentication system is exercised in every test run and prevents drift between test assumptions and production behavior.

### Claude's Discretion

Several implementation details are left to engineering judgment during planning and execution:

The password hashing algorithm should be bcrypt or argon2—both are industry standards. The exact choice depends on library availability and performance characteristics. Email verification tokens can be random strings or signed JWTs; the format matters less than ensuring they expire appropriately (likely 24-48 hours). JWT signing can use HS256 (symmetric) or RS256 (asymmetric); HS256 is simpler for a single-service deployment. The refresh token database schema needs a tokens table with user reference, token hash, expiry, and created timestamp—exact column names and indexes are implementation details. Library choices for JWT handling (python-jose, PyJWT, or a higher-level library like fastapi-users) should be evaluated during research.

</decisions>

<specifics>
## Specific Ideas

The SPA token storage pattern—access token in memory, refresh token in HttpOnly cookie—was explicitly chosen for security. This is the recommended approach for SPAs that need to balance XSS protection with seamless user experience.

User context injection follows the existing pattern in the codebase where dependencies are injected via FastAPI's `Depends()` mechanism. The `CurrentUser` dataclass mirrors the approach used for `UnitOfWork` injection in service dependencies.

E2E tests should exercise the real authentication flow rather than using mocks or test-only backdoors. This validates that authentication actually works and prevents the common failure mode where tests pass but production authentication is broken.

</specifics>

<deferred>
## Deferred Ideas

**OIDC and social login** will be added in a future phase after email/password authentication is stable. The User model should accommodate this—users might eventually authenticate via Google but still have a local User record.

**Password reset** requires the same email infrastructure as verification. Once email sending is proven, adding a reset flow is straightforward.

**User invitations to households** enable the multi-user scenario this architecture anticipates. Deferred until email infrastructure is stable and we have a UI for managing household membership.

**Rate limiting** on login endpoints prevents brute force attacks. Requires either Redis or careful database-backed counting. Important for production but not critical for development.

**Account lockout** after failed attempts is another brute force protection. Often combined with rate limiting. Can be added when hardening for production.

**Session management** (viewing active sessions, logging out other devices) becomes possible with database-backed refresh tokens. The infrastructure will support it; the UI and endpoints can come later.

**User preferences** (timezone, currency, date format) belong on the User entity but aren't needed for authentication. Add when the UI needs them.

**User profile** (avatar, phone number) is similarly deferred until there's a UI that displays this information.

</deferred>

<planning_guidance>
## Planning Guidance

### TDD-Oriented Task Breakdown

Plans should structure tasks as TDD exercises where the pattern applies: write a failing test, implement the minimal code to pass, then refactor. This is particularly natural for domain entities, services, and API endpoints. Each task should be small enough that the test-implement-refactor cycle completes in a focused session.

Some tasks don't fit the TDD pattern—configuration, migrations, and infrastructure setup are better handled as "make it work, verify it works" rather than test-first. The planner should distinguish these and not force TDD where it doesn't apply.

### Human Interaction Waves

Certain work requires human action outside the codebase:

- Setting up email service credentials (SendGrid, AWS SES, or similar)
- Configuring environment variables for JWT secrets
- MCP server or plugin setup if using external tools
- Any configuration requiring Claude Code restart

Group these into dedicated waves so the human can batch the work. Avoid interleaving "write code" tasks with "configure external service" tasks—it breaks flow. Instead, a wave might be: "Configure email provider and set environment variables" followed by a code wave that uses those capabilities.

### Research Priorities

The researcher agent should investigate:

- **FastAPI JWT libraries**: Compare python-jose, PyJWT, and fastapi-users. Evaluate complexity, maintenance status, and fit with the existing codebase patterns.
- **Email verification libraries**: Options for generating and validating verification tokens, sending emails, and handling the verification callback.
- **HttpOnly cookie handling in FastAPI**: How to set secure cookies in responses, read them in requests, and integrate with the existing request/response flow.
- **Refresh token rotation patterns**: Best practices for token rotation, handling race conditions when multiple requests try to refresh simultaneously, and token family tracking for detecting theft.
- **Database schema for refresh tokens**: Reference implementations, indexing strategies, and cleanup of expired tokens.

</planning_guidance>

---

*Phase: 04-authentication-infrastructure*
*Context gathered: 2026-02-04*
