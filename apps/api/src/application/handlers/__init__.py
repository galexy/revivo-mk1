"""Event handler registration.

Handlers are registered at application startup. Each handler
receives domain events and may enqueue jobs for async processing.
"""

from src.application.event_bus import register
from domain.events.user_events import EmailVerified, UserRegistered

from .user_handlers import on_email_verified, on_user_registered


def register_all_handlers() -> None:
    """Register all event handlers.

    Called during application startup in FastAPI lifespan.
    """
    # User domain handlers
    register(UserRegistered, on_user_registered)
    register(EmailVerified, on_email_verified)
