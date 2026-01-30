"""Base class for domain events.

Domain events represent something that happened in the domain that other
parts of the system might be interested in. They are used for:
- Decoupling aggregates (communicate via events, not direct references)
- Triggering side effects (send notifications, sync with external systems)
- Audit trail (when combined with outbox pattern)

Events are immutable records of facts. They capture:
- What aggregate produced them (aggregate_id, aggregate_type)
- When it happened (occurred_at)
- Event-specific data (subclass fields)
"""

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True)
class DomainEvent:
    """Base class for all domain events.

    All domain events should inherit from this class and add their
    event-specific fields. Events are immutable (frozen).

    Attributes:
        aggregate_id: ID of the aggregate that produced this event.
        aggregate_type: Type name of the aggregate (e.g., "Account", "Transaction").
        occurred_at: UTC timestamp when the event occurred.

    Example:
        @dataclass(frozen=True)
        class AccountCreated(DomainEvent):
            account_name: str
            initial_balance: Decimal
    """

    aggregate_id: str
    aggregate_type: str
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def event_type(self) -> str:
        """Return the event type name (class name).

        Used for serialization and event routing.
        """
        return self.__class__.__name__

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary for serialization.

        Handles datetime conversion to ISO format string.

        Returns:
            Dictionary representation of the event.
        """
        result = asdict(self)
        # Convert datetime to ISO format string for JSON serialization
        if isinstance(result.get("occurred_at"), datetime):
            result["occurred_at"] = result["occurred_at"].isoformat()
        return result
