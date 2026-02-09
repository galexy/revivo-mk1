---
phase: 06-transactional-email-infrastructure
plan: 02
subsystem: email
tags: [smtp, mjml, jinja2, email-templates, protocol]

# Dependency graph
requires:
  - phase: 06-01
    provides: MJML build tooling (npx mjml, Makefile build-emails target)
  - phase: 01-foundation
    provides: Protocol pattern (repository.py), structlog logging
provides:
  - EmailService protocol in domain/ports (send_email method)
  - SmtpEmailAdapter implementing EmailService
  - MJML source templates for verification email
  - Compiled HTML email templates (table-based, email-client compatible)
  - Jinja2 template rendering for verification emails
  - get_email_service() factory from environment variables
affects: [06-03-email-verification-handler, 06-04-integration-tests]

# Tech tracking
tech-stack:
  added: [Jinja2]
  patterns: [MJML-to-HTML compilation, Jinja2 template rendering, multipart email composition]

key-files:
  created:
    - src/domain/ports/email_service.py
    - src/adapters/email/__init__.py
    - src/adapters/email/smtp_adapter.py
    - src/adapters/email/templates/base.mjml
    - src/adapters/email/templates/verification.mjml
    - src/adapters/email/templates/verification.html
    - src/adapters/email/templates/verification.txt
  modified:
    - src/domain/ports/__init__.py
    - pyproject.toml
    - uv.lock

key-decisions:
  - "Jinja2 for template rendering (runtime variable substitution in compiled HTML)"
  - "FileSystemLoader with StrictUndefined for template safety"
  - "recipient_name formatted as space-prefixed greeting for clean Hi/Hi Name rendering"
  - "Default SMTP_PORT 1025 for Mailpit dev server"
  - "Lazy is_available() check with cached result for SMTP connectivity"
  - "EmailDeliveryError wraps both SMTPException and OSError for connection failures"

patterns-established:
  - "MJML compilation workflow: edit .mjml -> make build-emails -> commit both .mjml and .html"
  - "Email PII masking: first 3 chars + *** for log output"
  - "EmailService Protocol in domain/ports with adapter in adapters/email"
  - "Factory function get_email_service() reads env vars with sensible dev defaults"

# Metrics
duration: 4min
completed: 2026-02-06
---

# Phase 6 Plan 2: EmailService Protocol and SMTP Adapter Summary

**EmailService protocol with SMTP adapter, MJML-compiled HTML templates, and Jinja2 rendering for verification emails**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-06T22:10:55Z
- **Completed:** 2026-02-06T22:14:57Z
- **Tasks:** 2
- **Files modified:** 10

## Accomplishments
- EmailService Protocol defined in domain/ports with send_email method and EmailDeliveryError exception
- SmtpEmailAdapter composes multipart HTML+text emails via EmailMessage with STARTTLS support
- MJML source templates compiled to table-based HTML preserving Jinja2 variables
- render_verification_email() renders both HTML and plain text with recipient, link, expiry variables
- get_email_service() factory creates adapter from SMTP_HOST/PORT/USER/PASSWORD env vars

## Task Commits

Each task was committed atomically:

1. **Task 1: Create EmailService protocol in domain/ports** - `358ecb8` (feat)
2. **Task 2: Create SMTP adapter with MJML templates** - `737ef46` (feat)

**Plan metadata:** TBD (docs: complete plan)

## Files Created/Modified
- `src/domain/ports/email_service.py` - EmailService Protocol and EmailDeliveryError exception
- `src/domain/ports/__init__.py` - Added EmailService and EmailDeliveryError exports
- `src/adapters/email/__init__.py` - Package exports, Jinja2 template env, render_verification_email(), get_email_service()
- `src/adapters/email/smtp_adapter.py` - SmtpEmailAdapter with multipart email composition and PII-safe logging
- `src/adapters/email/templates/base.mjml` - MJML base template with header/footer structure
- `src/adapters/email/templates/verification.mjml` - MJML source for verification email
- `src/adapters/email/templates/verification.html` - Compiled table-based HTML from MJML
- `src/adapters/email/templates/verification.txt` - Plain text fallback template
- `pyproject.toml` - Added Jinja2 dependency
- `uv.lock` - Updated lockfile

## Decisions Made
- Added Jinja2 as project dependency (not already present; needed for template rendering)
- Used FileSystemLoader with StrictUndefined for template safety (catches missing variables)
- Formatted recipient_name as space-prefixed (" Name") for clean "Hi Name" / "Hi" rendering
- Default SMTP_PORT 1025 and use_tls=False for Mailpit dev compatibility
- Lazy is_available() with cached result to avoid repeated SMTP connection checks
- EmailDeliveryError wraps both SMTPException (protocol errors) and OSError (connection errors)
- CSS class-based word-break for URL display (MJML does not support word-break attribute directly)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Installed Jinja2 dependency via uv**
- **Found during:** Task 2 (SMTP adapter creation)
- **Issue:** Jinja2 not in project dependencies, import failed
- **Fix:** Added Jinja2>=3.1.0 to pyproject.toml dependencies, ran uv sync
- **Files modified:** pyproject.toml, uv.lock
- **Verification:** Import succeeds, template rendering works
- **Committed in:** 737ef46 (Task 2 commit)

**2. [Rule 1 - Bug] Fixed MJML word-break attribute warning**
- **Found during:** Task 2 (MJML compilation)
- **Issue:** MJML does not support word-break attribute on mj-text, produced warning
- **Fix:** Used css-class with custom CSS rule for word-break behavior
- **Files modified:** src/adapters/email/templates/verification.mjml
- **Verification:** MJML compiles without warnings
- **Committed in:** 737ef46 (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 bug)
**Impact on plan:** Both fixes necessary for correct operation. No scope creep.

## Issues Encountered
- Jinja2 was installed via pip to user site-packages but project uses uv-managed venv; resolved by adding to pyproject.toml and running uv sync

## User Setup Required
None - no external service configuration required. SMTP defaults target Mailpit (localhost:1025).

## Next Phase Readiness
- EmailService protocol and SMTP adapter ready for handler integration in 06-03
- Template rendering tested with all variables (recipient_name, verification_link, expiry_hours)
- 432 existing tests continue to pass (zero regressions)

---
*Phase: 06-transactional-email-infrastructure*
*Completed: 2026-02-06*
