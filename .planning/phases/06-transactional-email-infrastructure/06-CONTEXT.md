# Phase 6: Transactional Email Infrastructure - Context

**Gathered:** 2026-02-06
**Status:** Ready for planning
**Depends on:** Phase 5 (Domain Event Publishing)

<domain>
## Phase Boundary

Build email sending capability with SMTP adapter and Mailpit for dev environment. Send verification email on user registration using the event infrastructure from Phase 5. Integration tests mock the email adapter.

This phase establishes reusable infrastructure for all transactional emails (verification now, password reset later).

</domain>

<decisions>
## Implementation Decisions

### Email Content & Branding
- HTML with plain text fallback for all emails
- Sender identity configurable via environment variables (SMTP_FROM_NAME, SMTP_FROM_EMAIL)
- Minimal branding: logo + clean layout, not heavy styling
- **MJML for email templates** — compiles to table-based HTML compatible with all email clients
  - .mjml source files are human-readable and version-controlled
  - Compiled .html files contain Jinja2 variables for runtime rendering
  - Build step: `make build-emails` (requires Node.js/npm for MJML)
  - Both .mjml source and .html output are committed to git
- Subject lines action-focused (e.g., "Confirm your email to get started")
- Tone: friendly but professional
- Include brief teaser about what user can do after verifying
- Full footer with company info and support link

### Verification Flow UX
- Links valid for 48 hours
- Expired link shows error page with resend button
- Successful verification auto-logs user in and redirects to dashboard (implementation details deferred to UI phase)
- Re-clicking valid link when already verified: treat as success (idempotent)
- Long signed token in URL (existing itsdangerous pattern)
- Email body states expiration time explicitly ("This link expires in 48 hours")
- Resend verification available from login page when user attempts login with unverified account
- Rate limiting: 3 resend requests per hour

### Dev Environment Workflow
- Mailpit on localhost:8025 (separate browser tab)
- Mailpit always-on in Docker Compose (not optional profile)
- App starts even if SMTP unavailable, but logs error for observability
- Endpoints that attempt email send return 500 if email service unavailable
- SMTP configuration via individual env vars (SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD)
- No EMAIL_ENABLED toggle — always require SMTP config
- Integration tests use mock email adapter (no real SMTP calls)
- Test verification is test-specific (each test decides what to assert)
- No dev preview endpoint — use Mailpit to view sent emails

### Event Integration
- Email sending triggered by domain event (UserRegistered) via Phase 5 infrastructure
- Event handler enqueues job to job queue (handler doesn't send email directly)
- Registration returns 202 immediately when email job is queued
- If email queuing fails during registration, registration fails (rollback user creation)

### Claude's Discretion
- ~~Email templating library choice~~ → **Decided: MJML + Jinja2** (MJML compiles to HTML, Jinja2 renders at runtime)
- Specific SMTP library choice (smtplib recommended)

</decisions>

<specifics>
## Specific Ideas

- Research email templating solutions that allow editing templates in markup files outside code
- Dev workflow: register user -> open Mailpit UI -> click verification link -> user verified
- No logging of PII — use job IDs for debugging correlation

</specifics>

<deferred>
## Deferred Ideas

- Auto-login JWT delivery mechanism — deferred to UI phase
- Email deliverability (SPF/DKIM/DMARC) — production hardening phase
- Marketing emails / notification preferences — separate capability

</deferred>

---

*Phase: 06-transactional-email-infrastructure*
*Context gathered: 2026-02-06*
