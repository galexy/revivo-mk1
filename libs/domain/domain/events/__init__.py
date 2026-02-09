"""Domain events for cross-aggregate communication."""

from domain.events.base import DomainEvent
from domain.events.user_events import EmailVerified, UserRegistered

__all__ = ["DomainEvent", "EmailVerified", "UserRegistered"]
