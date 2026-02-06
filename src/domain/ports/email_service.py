"""Email service protocol for sending transactional emails.

The EmailService protocol defines the contract for email delivery.
Infrastructure adapters (SMTP, third-party APIs) implement this
protocol to provide actual email sending capability.

This follows the same Protocol-based port pattern as Repository and
UnitOfWork, enabling dependency inversion: the domain defines what
it needs, and infrastructure adapters implement those interfaces.

Key implementations:
- SmtpEmailAdapter: SMTP-based delivery (src.adapters.email.smtp_adapter)
"""

from typing import Protocol


class EmailDeliveryError(Exception):
    """Raised when an email fails to be delivered.

    This exception wraps underlying transport errors (SMTP failures,
    API errors, etc.) into a domain-level exception that services
    can handle without knowing the delivery mechanism.

    Attributes:
        message: Human-readable error description.
        original_error: The underlying transport error, if available.
    """

    def __init__(
        self,
        message: str = "Failed to deliver email",
        original_error: Exception | None = None,
    ) -> None:
        super().__init__(message)
        self.original_error = original_error


class EmailService(Protocol):
    """Protocol for email delivery services.

    Implementations must provide the send_email method for delivering
    transactional emails (verification, password reset, notifications).

    The protocol accepts pre-rendered HTML and plain text content,
    keeping template rendering separate from delivery concerns.

    Example:
        class SmtpEmailAdapter:
            def send_email(
                self,
                to_email: str,
                subject: str,
                html_content: str,
                text_content: str,
            ) -> None:
                # SMTP delivery logic
                ...
    """

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str,
    ) -> None:
        """Send an email with HTML and plain text content.

        Args:
            to_email: Recipient email address.
            subject: Email subject line.
            html_content: Rendered HTML body content.
            text_content: Plain text fallback content.

        Raises:
            EmailDeliveryError: If the email cannot be delivered.
        """
        ...
