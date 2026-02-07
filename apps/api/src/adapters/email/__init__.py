"""Email adapter package for transactional email delivery.

Provides SMTP-based email delivery and Jinja2 template rendering
for transactional emails (verification, password reset, etc.).

Exports:
    SmtpEmailAdapter: SMTP implementation of EmailService protocol
    get_email_service: Factory that creates adapter from environment variables
    render_verification_email: Renders verification email templates

MJML compilation workflow:
    1. Edit .mjml files in templates/ (human-readable source of truth)
    2. Run `make build-emails` to compile to .html (table-based layout)
    3. Commit both .mjml source and .html output
    4. At runtime, Jinja2 renders the .html with actual variable values
"""

import os
from pathlib import Path

import jinja2

from src.adapters.email.smtp_adapter import SmtpEmailAdapter

# Template environment - loads compiled HTML and plain text templates
_TEMPLATE_DIR = Path(__file__).parent / "templates"
_template_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(str(_TEMPLATE_DIR)),
    autoescape=jinja2.select_autoescape(["html"]),
    undefined=jinja2.StrictUndefined,
)


def render_verification_email(
    recipient_name: str | None = None,
    verification_link: str = "",
    expiry_hours: int = 48,
    company_name: str | None = None,
    support_email: str | None = None,
) -> tuple[str, str]:
    """Render verification email from compiled HTML and plain text templates.

    Loads the pre-compiled HTML template (from MJML) and the plain text
    template, then renders both with the provided variables.

    Args:
        recipient_name: Recipient's display name (optional).
        verification_link: URL for email verification.
        expiry_hours: Hours until the verification link expires.
        company_name: Company name for header/footer (default from env).
        support_email: Support email for footer (default from env).

    Returns:
        Tuple of (html_content, text_content) ready for sending.
    """
    # Format recipient greeting
    name_greeting = f" {recipient_name}" if recipient_name else ""

    # Defaults from environment or hardcoded fallbacks
    resolved_company = company_name or os.environ.get(
        "EMAIL_COMPANY_NAME", "Personal Finance"
    )
    resolved_support = support_email or os.environ.get(
        "EMAIL_SUPPORT_ADDRESS", "support@example.com"
    )

    template_vars = {
        "recipient_name": name_greeting,
        "verification_link": verification_link,
        "expiry_hours": expiry_hours,
        "company_name": resolved_company,
        "support_email": resolved_support,
    }

    html_template = _template_env.get_template("verification.html")
    text_template = _template_env.get_template("verification.txt")

    html_content = html_template.render(**template_vars)
    text_content = text_template.render(**template_vars)

    return html_content, text_content


def get_email_service() -> SmtpEmailAdapter:
    """Create an SmtpEmailAdapter configured from environment variables.

    Environment variables:
        SMTP_HOST: SMTP server hostname (default: "localhost")
        SMTP_PORT: SMTP server port (default: 1025 for Mailpit)
        SMTP_USER: SMTP authentication username (optional)
        SMTP_PASSWORD: SMTP authentication password (optional)
        SMTP_FROM_NAME: Sender display name (default: "Personal Finance")
        SMTP_FROM_EMAIL: Sender email address (default: "noreply@example.com")
        SMTP_USE_TLS: Enable STARTTLS (default: "false")

    Returns:
        Configured SmtpEmailAdapter instance.
    """
    return SmtpEmailAdapter(
        host=os.environ.get("SMTP_HOST", "localhost"),
        port=int(os.environ.get("SMTP_PORT", "1025")),
        username=os.environ.get("SMTP_USER"),
        password=os.environ.get("SMTP_PASSWORD"),
        from_name=os.environ.get("SMTP_FROM_NAME", "Personal Finance"),
        from_email=os.environ.get("SMTP_FROM_EMAIL", "noreply@example.com"),
        use_tls=os.environ.get("SMTP_USE_TLS", "false").lower() == "true",
    )


__all__ = [
    "SmtpEmailAdapter",
    "get_email_service",
    "render_verification_email",
]
