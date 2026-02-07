"""Mock email adapter for testing.

Records sent emails for assertion without making real SMTP calls.
"""

from dataclasses import dataclass, field


@dataclass
class SentEmail:
    """Record of a sent email."""

    to_email: str
    subject: str
    html_content: str
    text_content: str


@dataclass
class MockEmailAdapter:
    """Mock email adapter that records sent emails.

    Implements EmailService protocol for test injection.
    """

    sent_emails: list[SentEmail] = field(default_factory=list)

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str,
    ) -> None:
        """Record email instead of sending."""
        self.sent_emails.append(
            SentEmail(
                to_email=to_email,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
            )
        )

    def get_last_email(self) -> SentEmail | None:
        """Get the most recently sent email."""
        return self.sent_emails[-1] if self.sent_emails else None

    def get_emails_to(self, email: str) -> list[SentEmail]:
        """Get all emails sent to a specific address."""
        return [e for e in self.sent_emails if e.to_email == email]

    def clear(self) -> None:
        """Clear all recorded emails."""
        self.sent_emails.clear()
