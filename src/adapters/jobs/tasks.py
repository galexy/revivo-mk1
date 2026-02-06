"""Job task definitions.

Tasks are decorated with @job_queue.task and executed by workers.
Each task should be idempotent and handle its own error logging.
"""

from procrastinate import RetryStrategy

from src.adapters.jobs.app import job_queue
from src.adapters.logging import get_logger

logger = get_logger(__name__)

# Retry strategy for email tasks (Phase 6 will use this)
email_retry = RetryStrategy(
    max_attempts=5,
    exponential_wait=60,  # 60s, 3600s, 216000s...
    retry_exceptions={ConnectionError, TimeoutError},
)


@job_queue.task(queue="email", retry=email_retry)
async def send_verification_email(
    user_id: str,
    email: str,  # noqa: ARG001 - Used by Phase 6 email sending
    verification_token: str,  # noqa: ARG001 - Used by Phase 6 email sending
) -> None:
    """Send verification email to newly registered user.

    This is a placeholder - actual email sending implemented in Phase 6.

    Args:
        user_id: User ID for correlation
        email: Email address (not logged per PII policy)
        verification_token: Token for email verification
    """
    logger.info(
        "verification_email_job_executed",
        user_id=user_id,
        # Note: Not logging email address (PII) per CONTEXT.md
    )
    # Phase 6 will implement actual email sending
