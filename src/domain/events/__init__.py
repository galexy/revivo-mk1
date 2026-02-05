"""Domain events for cross-aggregate communication."""

from src.domain.events.base import DomainEvent
from src.domain.events.user_events import EmailVerified, UserRegistered

__all__ = ["DomainEvent", "EmailVerified", "UserRegistered"]
