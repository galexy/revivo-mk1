"""Handlers for User domain events.

These handlers are called synchronously after UoW commit.
For side effects (email, external calls), they enqueue jobs.
"""

from src.adapters.logging import get_logger
from src.domain.events.user_events import EmailVerified, UserRegistered

logger = get_logger(__name__)


def on_user_registered(event: UserRegistered) -> None:
    """Handle UserRegistered event.

    Enqueues welcome/verification email job.
    Actual email sending is implemented in Phase 6.

    Args:
        event: The UserRegistered event
    """
    logger.info(
        "user_registered_handler",
        user_id=event.user_id,
        household_id=event.household_id,
        # Note: Not logging email (PII)
    )
    # Phase 6 will add: await send_verification_email.defer_async(...)
    # For now, just log that the handler was called


def on_email_verified(event: EmailVerified) -> None:
    """Handle EmailVerified event.

    Currently a no-op. Future phases may add welcome email, analytics, etc.

    Args:
        event: The EmailVerified event
    """
    logger.info(
        "email_verified_handler",
        user_id=event.user_id,
    )
