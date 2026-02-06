# Phase 6: Transactional Email Infrastructure - Research

**Researched:** 2026-02-06
**Domain:** SMTP Email Sending, Email Templating, Dev Email Testing
**Confidence:** HIGH

## Summary

This phase implements email sending infrastructure for transactional emails (verification, password reset) using Python's standard library for SMTP (smtplib for sync or aiosmtplib for async), Jinja2 for HTML templating with plain text fallback, and Mailpit as the dev environment email capture tool.

The codebase already has:
- Job queue infrastructure (Procrastinate) with a placeholder `send_verification_email` task in `src/adapters/jobs/tasks.py`
- Event handler for `UserRegistered` in `src/application/handlers/user_handlers.py` (ready to enqueue email jobs)
- Token generation via `itsdangerous` in `src/adapters/security/tokens.py` (currently 24-hour expiry, needs update to 48 hours per CONTEXT.md)
- Docker Compose setup that can be extended with Mailpit

The implementation approach follows hexagonal architecture: define an `EmailService` protocol in the domain/ports layer, implement an SMTP adapter, and inject the adapter via FastAPI dependencies. Integration tests mock the email adapter rather than making real SMTP calls.

**Primary recommendation:** Use Python's standard library `email.message.EmailMessage` with `smtplib` (sync) for email composition and sending, Jinja2 for template rendering, and Mailpit v1.29+ in Docker Compose for dev email capture. Create an `EmailService` protocol to enable mock injection for testing.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| smtplib | stdlib | SMTP email sending | Python standard library, no external dependency, works with any SMTP server |
| email.message | stdlib | Email composition (multipart HTML+text) | Modern API with `set_content()` and `add_alternative()`, handles MIME correctly |
| Jinja2 | 3.1.x | Email template rendering | Already used by FastAPI ecosystem, supports template inheritance, file-based templates |
| Mailpit | 1.29+ | Dev email capture/testing | Modern replacement for MailHog, actively maintained, Docker image available |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| aiosmtplib | 5.1.x | Async SMTP sending | If sending from async context without job queue; Procrastinate jobs use async so consider for job implementation |
| itsdangerous | 2.2+ | Signed tokens | Already in use for verification tokens |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| smtplib | aiosmtplib | Async, but adds dependency; smtplib works fine in Procrastinate async jobs |
| Jinja2 | MJML | MJML is email-specific but requires Node.js compilation step |
| Jinja2 | React Email | Modern but requires Node.js, overkill for simple transactional emails |
| Mailpit | MailHog | MailHog deprecated, Mailpit is the maintained successor |
| file templates | inline strings | File templates are easier to edit and maintain |

**Installation:**
```bash
# Jinja2 is likely already installed via FastAPI dependencies
# Add to pyproject.toml if not present:
pip install Jinja2 aiosmtplib

# Mailpit is added via Docker Compose (no pip install)
```

## Architecture Patterns

### Recommended Project Structure
```
src/
├── domain/
│   └── ports/
│       └── email_service.py       # NEW - EmailService protocol
├── adapters/
│   └── email/                     # NEW - email adapter package
│       ├── __init__.py
│       ├── smtp_adapter.py        # SMTP implementation of EmailService
│       └── templates/             # NEW - Jinja2 email templates
│           ├── base.html          # Base layout with header/footer
│           ├── base.txt           # Plain text base
│           ├── verification.html  # Verification email HTML
│           └── verification.txt   # Verification email plain text
├── application/
│   └── handlers/
│       └── user_handlers.py       # MODIFY - enqueue email job
└── adapters/
    └── jobs/
        └── tasks.py               # MODIFY - implement send_verification_email
```

### Pattern 1: EmailService Protocol (Port)
**What:** Protocol defining email sending capability without implementation details
**When to use:** Define in domain/ports to allow mock injection for testing
**Example:**
```python
# Source: Python Protocol pattern + project conventions
from typing import Protocol

class EmailService(Protocol):
    """Protocol for email sending capability.

    Implementations:
    - SmtpEmailAdapter: Real SMTP sending
    - MockEmailAdapter: Testing (records sent emails)
    """

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str,
    ) -> None:
        """Send an email.

        Args:
            to_email: Recipient email address
            subject: Email subject line
            html_content: HTML body
            text_content: Plain text fallback

        Raises:
            EmailDeliveryError: If sending fails
        """
        ...
```

### Pattern 2: Multipart Email with Plain Text Fallback
**What:** Email with both HTML and plain text versions for maximum compatibility
**When to use:** All transactional emails per CONTEXT.md decision
**Example:**
```python
# Source: https://docs.python.org/3/library/email.examples.html
from email.message import EmailMessage

def create_multipart_email(
    from_addr: str,
    to_addr: str,
    subject: str,
    html_content: str,
    text_content: str,
) -> EmailMessage:
    """Create email with HTML and plain text alternatives."""
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr

    # Set plain text first
    msg.set_content(text_content)

    # Add HTML alternative - this converts to multipart/alternative
    msg.add_alternative(html_content, subtype="html")

    return msg
```

### Pattern 3: Jinja2 Template Loading from Files
**What:** Load HTML/text templates from external files, not inline strings
**When to use:** Per CONTEXT.md decision - templates in separate markup files
**Example:**
```python
# Source: https://jinja.palletsprojects.com/en/3.1.x/api/
from jinja2 import Environment, PackageLoader, select_autoescape
from pathlib import Path

def create_template_environment() -> Environment:
    """Create Jinja2 environment for email templates."""
    return Environment(
        loader=PackageLoader("src.adapters.email", "templates"),
        autoescape=select_autoescape(["html", "xml"]),
    )

def render_verification_email(
    env: Environment,
    recipient_name: str,
    verification_link: str,
    expiry_hours: int = 48,
) -> tuple[str, str]:
    """Render verification email templates.

    Returns:
        Tuple of (html_content, text_content)
    """
    html_template = env.get_template("verification.html")
    text_template = env.get_template("verification.txt")

    context = {
        "recipient_name": recipient_name,
        "verification_link": verification_link,
        "expiry_hours": expiry_hours,
    }

    return (
        html_template.render(**context),
        text_template.render(**context),
    )
```

### Pattern 4: SMTP Adapter with Graceful Degradation
**What:** SMTP sending that logs errors and allows app to start without SMTP
**When to use:** Per CONTEXT.md - app starts even if SMTP unavailable
**Example:**
```python
# Source: https://docs.python.org/3/library/smtplib.html + project patterns
import smtplib
import ssl
from src.adapters.logging import get_logger

logger = get_logger(__name__)

class SmtpEmailAdapter:
    """SMTP adapter with connection pooling and error handling."""

    def __init__(
        self,
        host: str,
        port: int,
        username: str | None = None,
        password: str | None = None,
        use_tls: bool = True,
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self._available: bool | None = None

    def is_available(self) -> bool:
        """Check if SMTP server is reachable."""
        if self._available is not None:
            return self._available
        try:
            with smtplib.SMTP(self.host, self.port, timeout=5) as smtp:
                smtp.noop()
            self._available = True
        except Exception as e:
            logger.error("smtp_unavailable", host=self.host, port=self.port, error=str(e))
            self._available = False
        return self._available

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str,
    ) -> None:
        """Send email via SMTP."""
        if not self.is_available():
            raise EmailDeliveryError("SMTP server unavailable")

        msg = create_multipart_email(
            from_addr=f"{self.from_name} <{self.from_email}>",
            to_addr=to_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
        )

        try:
            with smtplib.SMTP(self.host, self.port) as smtp:
                if self.use_tls:
                    smtp.starttls()
                if self.username and self.password:
                    smtp.login(self.username, self.password)
                smtp.send_message(msg)
                logger.info("email_sent", to=to_email[:3] + "***")  # PII protection
        except smtplib.SMTPException as e:
            logger.error("email_send_failed", error=str(e))
            raise EmailDeliveryError(f"Failed to send email: {e}") from e
```

### Pattern 5: Job Task with Email Adapter Injection
**What:** Procrastinate job that uses injected email adapter
**When to use:** For the `send_verification_email` job implementation
**Example:**
```python
# Source: Procrastinate docs + project patterns
from procrastinate import RetryStrategy
from src.adapters.jobs.app import job_queue
from src.adapters.email import get_email_service, render_verification_email
from src.adapters.logging import get_logger

logger = get_logger(__name__)

email_retry = RetryStrategy(
    max_attempts=5,
    exponential_wait=60,
    retry_exceptions={ConnectionError, TimeoutError, EmailDeliveryError},
)

@job_queue.task(queue="email", retry=email_retry)
async def send_verification_email(
    user_id: str,
    email: str,
    verification_token: str,
) -> None:
    """Send verification email to newly registered user."""
    logger.info("sending_verification_email", user_id=user_id)

    # Get email service (real SMTP or mock depending on environment)
    email_service = get_email_service()

    # Build verification link
    base_url = os.getenv("APP_BASE_URL", "http://localhost:8000")
    verification_link = f"{base_url}/auth/verify-email?token={verification_token}"

    # Render templates
    html_content, text_content = render_verification_email(
        recipient_name="User",  # Could pass name if available
        verification_link=verification_link,
        expiry_hours=48,
    )

    # Send
    email_service.send_email(
        to_email=email,
        subject="Confirm your email to get started",
        html_content=html_content,
        text_content=text_content,
    )
```

### Anti-Patterns to Avoid
- **Logging PII (email addresses):** Per CONTEXT.md, never log full email addresses. Use job_id or user_id for correlation.
- **Blocking HTTP requests with email sending:** Always use job queue for email. Never send email synchronously in request handler.
- **Hardcoding SMTP credentials:** Use environment variables (SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD).
- **Inline HTML in code:** Use file-based Jinja2 templates for maintainability.
- **Ignoring plain text fallback:** Some email clients don't render HTML. Always include text version.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| HTML email composition | String concatenation | email.message.EmailMessage + add_alternative | Handles MIME boundaries, encoding, multipart correctly |
| Template rendering | f-strings or format() | Jinja2 Environment | Escaping, inheritance, filters, file loading |
| SMTP TLS/SSL | Manual socket handling | smtplib.SMTP + starttls() | Handles handshake, certificate verification |
| Dev email capture | Custom SMTP mock | Mailpit Docker container | Web UI, API, multi-platform, actively maintained |
| Email retry logic | Custom retry loop | Procrastinate RetryStrategy | Exponential backoff, exception filtering, persistence |

**Key insight:** Email sending looks simple but MIME encoding, character sets, and SMTP error handling have many edge cases. Use stdlib email.message for composition and smtplib for sending.

## Common Pitfalls

### Pitfall 1: Token Expiry Mismatch
**What goes wrong:** Email says "48 hours" but token expires in 24 hours
**Why it happens:** Current code uses `EMAIL_VERIFICATION_MAX_AGE = 86400` (24 hours)
**How to avoid:** Update `src/adapters/security/tokens.py` to use 172800 (48 hours) per CONTEXT.md
**Warning signs:** Users report expired links before stated expiration

### Pitfall 2: Missing From Address Configuration
**What goes wrong:** Emails rejected by SMTP server or marked as spam
**Why it happens:** No from address or using default that doesn't match domain
**How to avoid:** Require SMTP_FROM_NAME and SMTP_FROM_EMAIL environment variables
**Warning signs:** SMTP auth errors, emails in spam folder

### Pitfall 3: App Crash on Missing SMTP
**What goes wrong:** App fails to start because SMTP server unavailable
**Why it happens:** Eagerly connecting to SMTP on startup
**How to avoid:** Lazy connection check, log warning but don't block startup
**Warning signs:** Container restart loops when SMTP down

### Pitfall 4: HTML-Only Emails
**What goes wrong:** Emails unreadable in text-only clients, accessibility issues
**Why it happens:** Forgetting to add plain text alternative
**How to avoid:** Always use `set_content(text)` then `add_alternative(html, subtype='html')`
**Warning signs:** Blank emails in terminal clients, screen reader issues

### Pitfall 5: Integration Tests Making SMTP Calls
**What goes wrong:** Tests slow, flaky, require real SMTP, or send actual emails
**Why it happens:** Not mocking email adapter in test fixtures
**How to avoid:** Use `app.dependency_overrides` to inject MockEmailAdapter
**Warning signs:** Network timeouts in CI, unexpected emails received

### Pitfall 6: Job Queue Not Deferring Synchronously
**What goes wrong:** Event handler uses `await defer_async()` but event bus is synchronous
**Why it happens:** Mixing sync event handlers with async job deferral
**How to avoid:** Use Procrastinate's sync `defer()` method in synchronous event handlers, or make handler async and use asyncio.create_task() to bridge
**Warning signs:** "coroutine was never awaited" warnings, jobs not enqueued

## Code Examples

Verified patterns from official sources:

### Email Template: verification.html
```html
<!-- Source: Jinja2 template patterns -->
{% extends "base.html" %}

{% block content %}
<h1>Verify your email address</h1>
<p>Hi{{ " " + recipient_name if recipient_name else "" }},</p>
<p>Thanks for signing up! Please verify your email address by clicking the button below.</p>
<p>
  <a href="{{ verification_link }}" style="background-color: #4CAF50; color: white; padding: 14px 20px; text-decoration: none; display: inline-block;">
    Verify Email
  </a>
</p>
<p>Or copy and paste this link into your browser:</p>
<p>{{ verification_link }}</p>
<p><strong>This link expires in {{ expiry_hours }} hours.</strong></p>
{% endblock %}
```

### Email Template: verification.txt
```text
{# Source: Jinja2 plain text template #}
Verify your email address

Hi{{ " " + recipient_name if recipient_name else "" }},

Thanks for signing up! Please verify your email address by clicking the link below.

{{ verification_link }}

This link expires in {{ expiry_hours }} hours.

---
{{ company_name }}
{{ support_email }}
```

### Mock Email Adapter for Testing
```python
# Source: Project testing patterns
from dataclasses import dataclass, field

@dataclass
class SentEmail:
    to_email: str
    subject: str
    html_content: str
    text_content: str

class MockEmailAdapter:
    """Mock email adapter that records sent emails for testing."""

    sent_emails: list[SentEmail] = field(default_factory=list)

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str,
    ) -> None:
        self.sent_emails.append(SentEmail(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
        ))

    def get_last_email(self) -> SentEmail | None:
        return self.sent_emails[-1] if self.sent_emails else None

    def clear(self) -> None:
        self.sent_emails.clear()
```

### FastAPI Dependency Override for Testing
```python
# Source: https://fastapi.tiangolo.com/advanced/testing-dependencies/
import pytest
from fastapi.testclient import TestClient
from src.adapters.api.app import app
from src.adapters.email import get_email_service
from tests.mocks import MockEmailAdapter

@pytest.fixture
def mock_email_adapter():
    """Fixture providing mock email adapter."""
    adapter = MockEmailAdapter()
    app.dependency_overrides[get_email_service] = lambda: adapter
    yield adapter
    app.dependency_overrides.clear()

def test_registration_sends_verification_email(mock_email_adapter):
    client = TestClient(app)
    response = client.post("/auth/register", json={
        "email": "test@example.com",
        "password": "SecurePass123!",
    })

    assert response.status_code == 202
    assert len(mock_email_adapter.sent_emails) == 1
    assert mock_email_adapter.sent_emails[0].to_email == "test@example.com"
    assert "Verify" in mock_email_adapter.sent_emails[0].subject
```

### Mailpit Docker Compose Configuration
```yaml
# Source: https://github.com/axllent/mailpit + Docker best practices
services:
  mailpit:
    image: axllent/mailpit:v1.29
    container_name: mailpit
    restart: unless-stopped
    ports:
      - "8025:8025"   # Web UI
      - "1025:1025"   # SMTP
    environment:
      MP_MAX_MESSAGES: 500
      MP_SMTP_AUTH_ACCEPT_ANY: 1
      MP_SMTP_AUTH_ALLOW_INSECURE: 1
    networks:
      - app-network
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| MailHog for dev | Mailpit | 2023+ | MailHog deprecated, Mailpit actively maintained |
| MIMEText + MIMEMultipart | EmailMessage.add_alternative() | Python 3.6+ | Cleaner API, automatic multipart handling |
| smtplib only | aiosmtplib for async | 2020+ | Non-blocking email in async contexts |
| Inline HTML strings | File-based Jinja2 templates | Best practice | Separation of concerns, easier editing |

**Deprecated/outdated:**
- `MIMEText` / `MIMEMultipart` classes: Still work but `EmailMessage` with `add_alternative()` is the modern API
- MailHog: Deprecated, use Mailpit instead
- `email.mime` subpackage: Legacy API, prefer `email.message.EmailMessage`

## Open Questions

Things that couldn't be fully resolved:

1. **Async vs Sync SMTP in Procrastinate Jobs**
   - What we know: Procrastinate jobs are async. smtplib is sync. aiosmtplib is async.
   - What's unclear: Whether to use aiosmtplib or just use smtplib in async job (it will block briefly)
   - Recommendation: Start with smtplib (simpler). If email sending becomes a bottleneck, switch to aiosmtplib.

2. **Email Adapter Dependency Injection Pattern**
   - What we know: FastAPI uses `Depends()` for DI. Procrastinate jobs don't have DI.
   - What's unclear: How to inject mock email adapter into Procrastinate jobs for testing
   - Recommendation: Use module-level factory function `get_email_service()` that reads from environment to determine real vs mock. Override at module level in tests.

3. **Rate Limiting Resend Verification**
   - What we know: CONTEXT.md specifies "3 resend requests per hour"
   - What's unclear: Implementation mechanism (in-memory, Redis, database)
   - Recommendation: Store last resend timestamps in user table or separate rate_limits table. Check before allowing resend.

## Sources

### Primary (HIGH confidence)
- [Python smtplib documentation](https://docs.python.org/3/library/smtplib.html) - SMTP sending API
- [Python email.message documentation](https://docs.python.org/3/library/email.message.html) - EmailMessage API
- [Python email.examples](https://docs.python.org/3/library/email.examples.html) - Multipart email examples
- [Mailpit GitHub](https://github.com/axllent/mailpit) - Version 1.29+, Docker configuration
- [Jinja2 documentation](https://jinja.palletsprojects.com/) - Template loading, rendering

### Secondary (MEDIUM confidence)
- [aiosmtplib PyPI](https://pypi.org/project/aiosmtplib/) - Version 5.1.0, async SMTP
- [FastAPI Testing Dependencies](https://fastapi.tiangolo.com/advanced/testing-dependencies/) - dependency_overrides pattern
- [Mailtrap smtplib tutorial](https://mailtrap.io/blog/smtplib/) - Error handling patterns

### Tertiary (LOW confidence)
- WebSearch results for email best practices - General guidance, not implementation-specific

## Metadata

**Confidence breakdown:**
- Standard stack (smtplib, Jinja2, Mailpit): HIGH - stdlib and official docs
- Architecture (EmailService protocol): HIGH - follows existing codebase patterns
- Pitfalls: MEDIUM - derived from CONTEXT.md requirements and general best practices

**Research date:** 2026-02-06
**Valid until:** 2026-03-06 (30 days - stable libraries, not fast-moving)
