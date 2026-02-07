"""SMTP email adapter implementing the EmailService protocol.

Sends transactional emails via SMTP using Python's standard library
email and smtplib modules. Composes multipart messages with both
HTML and plain text content for maximum email client compatibility.

Usage:
    adapter = SmtpEmailAdapter(
        host="localhost",
        port=1025,
        from_name="My App",
        from_email="noreply@example.com",
    )
    adapter.send_email(
        to_email="user@example.com",
        subject="Verify your email",
        html_content="<html>...</html>",
        text_content="Verify your email...",
    )
"""

import smtplib
from email.message import EmailMessage

from src.adapters.logging import get_logger
from domain.ports.email_service import EmailDeliveryError

logger = get_logger(__name__)


def _mask_email(email: str) -> str:
    """Mask email for logging (PII protection).

    Shows first 3 characters of local part, masks rest.
    Example: "test@example.com" -> "tes***@example.com"
    """
    if "@" not in email:
        return "***"
    local, domain = email.split("@", 1)
    visible = local[:3] if len(local) >= 3 else local[:1]
    return f"{visible}***@{domain}"


class SmtpEmailAdapter:
    """SMTP implementation of the EmailService protocol.

    Sends emails via SMTP with multipart HTML + plain text content.
    Designed for use in synchronous job queue handlers where async
    is not required.

    Configuration is injected via constructor, typically from
    environment variables through the get_email_service() factory.
    """

    def __init__(
        self,
        host: str,
        port: int,
        from_name: str,
        from_email: str,
        username: str | None = None,
        password: str | None = None,
        use_tls: bool = False,
    ) -> None:
        self._host = host
        self._port = port
        self._from_name = from_name
        self._from_email = from_email
        self._username = username
        self._password = password
        self._use_tls = use_tls
        self._available: bool | None = None

    def is_available(self) -> bool:
        """Check if the SMTP server is reachable (lazy, cached).

        Returns:
            True if the server accepted a connection, False otherwise.
        """
        if self._available is not None:
            return self._available

        try:
            with smtplib.SMTP(self._host, self._port, timeout=5) as smtp:
                smtp.noop()
            self._available = True
        except (smtplib.SMTPException, OSError):
            self._available = False
            logger.warning(
                "smtp_unavailable",
                host=self._host,
                port=self._port,
            )
        return self._available

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str,
    ) -> None:
        """Send an email with HTML and plain text content.

        Composes a multipart/alternative message with plain text as
        the base and HTML as the alternative, following RFC 2046.

        Args:
            to_email: Recipient email address.
            subject: Email subject line.
            html_content: Rendered HTML body content.
            text_content: Plain text fallback content.

        Raises:
            EmailDeliveryError: If the email cannot be delivered.
        """
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = f"{self._from_name} <{self._from_email}>"
        msg["To"] = to_email

        # Set plain text as base content
        msg.set_content(text_content)
        # Add HTML as alternative (preferred by clients that support it)
        msg.add_alternative(html_content, subtype="html")

        try:
            with smtplib.SMTP(self._host, self._port, timeout=30) as smtp:
                if self._use_tls:
                    smtp.starttls()
                if self._username and self._password:
                    smtp.login(self._username, self._password)
                smtp.send_message(msg)

            logger.info(
                "email_sent",
                to_email=_mask_email(to_email),
                subject=subject,
            )
        except smtplib.SMTPException as exc:
            logger.error(
                "email_send_failed",
                to_email=_mask_email(to_email),
                subject=subject,
                error=str(exc),
            )
            raise EmailDeliveryError(
                message=f"SMTP delivery failed: {exc}",
                original_error=exc,
            ) from exc
        except OSError as exc:
            logger.error(
                "email_connection_failed",
                host=self._host,
                port=self._port,
                error=str(exc),
            )
            raise EmailDeliveryError(
                message=f"SMTP connection failed: {exc}",
                original_error=exc,
            ) from exc
