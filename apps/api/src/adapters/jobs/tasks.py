"""Job task definitions.

Tasks are decorated with @job_queue.task and executed by workers.
Each task should be idempotent and handle its own error logging.
"""

import os

from procrastinate import RetryStrategy

from src.adapters.jobs.app import job_queue
from src.adapters.logging import get_logger
from domain.ports.email_service import EmailDeliveryError

logger = get_logger(__name__)

# Retry strategy for email tasks
email_retry = RetryStrategy(
    max_attempts=5,
    exponential_wait=60,  # 60s, 3600s, 216000s...
    retry_exceptions={ConnectionError, TimeoutError, EmailDeliveryError},
)


@job_queue.task(queue="email", retry=email_retry)
async def send_verification_email(
    user_id: str,
    email: str,
    verification_token: str,
) -> None:
    """Send verification email to newly registered user.

    Renders the verification email template with a signed token link
    and sends it via the configured SMTP adapter. Retries on transient
    failures (ConnectionError, TimeoutError, EmailDeliveryError).

    Args:
        user_id: User ID for correlation logging
        email: Recipient email address
        verification_token: Signed token for email verification link
    """
    logger.info("sending_verification_email", user_id=user_id)

    from src.adapters.email import get_email_service, render_verification_email

    email_service = get_email_service()

    base_url = os.environ.get("APP_BASE_URL", "http://localhost:8000")
    verification_link = f"{base_url}/auth/verify?token={verification_token}"

    html_content, text_content = render_verification_email(
        recipient_name=None,
        verification_link=verification_link,
        expiry_hours=48,
    )

    email_service.send_email(
        to_email=email,
        subject="Confirm your email to get started",
        html_content=html_content,
        text_content=text_content,
    )

    logger.info("verification_email_sent", user_id=user_id)
