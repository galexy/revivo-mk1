"""Account domain events.

Events emitted by the Account aggregate during lifecycle operations.
These events are captured via the outbox pattern for audit trail
and downstream processing (notifications, sync, etc.).

All events are immutable (frozen dataclass) and inherit from DomainEvent.
"""

from dataclasses import dataclass

from domain.events.base import DomainEvent


@dataclass(frozen=True)
class AccountCreated(DomainEvent):
    """Emitted when a new account is created.

    Attributes:
        account_name: The name given to the account.
        account_type: The type of account (checking, savings, etc.).
    """

    account_name: str = ""
    account_type: str = ""


@dataclass(frozen=True)
class AccountUpdated(DomainEvent):
    """Emitted when account properties change.

    Attributes:
        field: The name of the field that was updated.
        old_value: The previous value (as string, or None).
        new_value: The new value (as string, or None).
    """

    field: str = ""
    old_value: str | None = None
    new_value: str | None = None


@dataclass(frozen=True)
class AccountClosed(DomainEvent):
    """Emitted when an account is closed.

    No additional fields - base class provides aggregate_id,
    aggregate_type, and occurred_at.
    """

    pass


@dataclass(frozen=True)
class AccountReopened(DomainEvent):
    """Emitted when a closed account is reopened.

    No additional fields - base class provides aggregate_id,
    aggregate_type, and occurred_at.
    """

    pass


@dataclass(frozen=True)
class AccountDeleted(DomainEvent):
    """Emitted when an account without transactions is deleted.

    No additional fields - base class provides aggregate_id,
    aggregate_type, and occurred_at.
    """

    pass
