"""Domain events for User aggregate.

Events emitted during user lifecycle operations:
- Registration (UserRegistered)
- Email verification (EmailVerified)

These events are standalone dataclasses (not inheriting DomainEvent)
because User events use a different pattern from Account events.
User events are collected via the aggregate's collect_events() method.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True, slots=True)
class UserRegistered:
    """Emitted when a new user registers.

    Attributes:
        user_id: The ID of the newly registered user.
        email: The user's email address (normalized).
        household_id: The household created for/assigned to the user.
        occurred_at: When registration occurred.
    """

    user_id: str
    email: str
    household_id: str
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True, slots=True)
class EmailVerified:
    """Emitted when user verifies their email address.

    Attributes:
        user_id: The ID of the user who verified.
        email: The verified email address.
        occurred_at: When verification occurred.
    """

    user_id: str
    email: str
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
