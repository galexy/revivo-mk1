"""Mock adapters for testing.

Provides test doubles that implement domain port protocols
without requiring real infrastructure (SMTP, databases, etc.).
"""

from tests.mocks.email import MockEmailAdapter, SentEmail

__all__ = ["MockEmailAdapter", "SentEmail"]
