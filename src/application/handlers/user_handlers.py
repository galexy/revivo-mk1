"""Handlers for User domain events.

These handlers are called synchronously after UoW commit.
For side effects (email, external calls), they enqueue jobs.
"""

import os

from src.adapters.logging import get_logger
from src.adapters.security.tokens import generate_verification_token
from src.domain.events.user_events import EmailVerified, UserRegistered

logger = get_logger(__name__)


def on_user_registered(event: UserRegistered) -> None:
    """Handle UserRegistered event.

    Generates a verification token and enqueues a job to send
    the verification email. The job is deferred synchronously
    (the event bus calls handlers without await).

    If the job queue is disabled (JOB_QUEUE_ENABLED=false), the
    defer is skipped and only a log message is emitted.

    Args:
        event: The UserRegistered event
    """
    logger.info(
        "user_registered_handler",
        user_id=event.user_id,
        household_id=event.household_id,
    )

    job_queue_enabled = os.getenv("JOB_QUEUE_ENABLED", "true").lower() == "true"
    if not job_queue_enabled:
        logger.warning(
            "verification_email_skipped_job_queue_disabled",
            user_id=event.user_id,
        )
        return

    verification_token = generate_verification_token(event.email)

    try:
        from src.adapters.jobs.tasks import send_verification_email

        send_verification_email.defer(
            user_id=event.user_id,
            email=event.email,
            verification_token=verification_token,
        )

        logger.info(
            "verification_email_job_enqueued",
            user_id=event.user_id,
        )
    except Exception:
        # Job queue may be unavailable (not opened, DB down, etc.).
        # Email is a side effect -- registration must not fail because
        # the verification email could not be enqueued.
        logger.warning(
            "verification_email_defer_failed",
            user_id=event.user_id,
            exc_info=True,
        )


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
