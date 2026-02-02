"""Domain events for Transaction aggregate.

Events are emitted during transaction lifecycle and processed via the outbox pattern.
Following the established pattern from account_events.py.

Events capture:
- Transaction CRUD operations
- Status progression (Pending -> Cleared -> Reconciled)
- Mirror transaction lifecycle for transfers
- Category and payee management
"""

from dataclasses import dataclass

from src.domain.events.base import DomainEvent


@dataclass(frozen=True)
class TransactionCreated(DomainEvent):
    """Emitted when a new transaction is created.

    Attributes:
        account_id: Primary account for this transaction.
        amount: Total transaction amount as string (for serialization).
        currency: Currency code (e.g., "USD").
        is_mirror: True for auto-created mirror transactions (transfers).
    """

    account_id: str = ""
    amount: str = ""
    currency: str = "USD"
    is_mirror: bool = False


@dataclass(frozen=True)
class TransactionUpdated(DomainEvent):
    """Emitted when transaction fields are modified.

    Attributes:
        field: Name of the field that was updated.
        old_value: Previous value (as string, or None).
        new_value: New value (as string, or None).
    """

    field: str = ""
    old_value: str | None = None
    new_value: str | None = None


@dataclass(frozen=True)
class TransactionDeleted(DomainEvent):
    """Emitted when a transaction is deleted.

    Attributes:
        was_mirror: True if the deleted transaction was a mirror (transfer).
    """

    was_mirror: bool = False


@dataclass(frozen=True)
class TransactionStatusChanged(DomainEvent):
    """Emitted when transaction status changes (Pending -> Cleared -> Reconciled).

    Attributes:
        old_status: Previous status value.
        new_status: New status value.
    """

    old_status: str = ""
    new_status: str = ""


@dataclass(frozen=True)
class SplitUpdated(DomainEvent):
    """Emitted when transaction splits are modified.

    Attributes:
        change_type: Type of split change (added, removed, updated).
        split_count: Number of splits after the change.
    """

    change_type: str = ""
    split_count: int = 0


@dataclass(frozen=True)
class MirrorTransactionCreated(DomainEvent):
    """Emitted when a mirror transaction is auto-created for a transfer.

    Per CONTEXT: Source transaction owns transfer; mirror is auto-created.

    Attributes:
        source_transaction_id: ID of the source transaction.
        mirror_transaction_id: ID of the created mirror transaction.
        target_account_id: Account receiving the transfer.
    """

    source_transaction_id: str = ""
    mirror_transaction_id: str = ""
    target_account_id: str = ""


@dataclass(frozen=True)
class MirrorTransactionDeleted(DomainEvent):
    """Emitted when a mirror transaction is deleted (transfer split removed).

    Attributes:
        source_transaction_id: ID of the source transaction.
        mirror_transaction_id: ID of the deleted mirror transaction.
    """

    source_transaction_id: str = ""
    mirror_transaction_id: str = ""


@dataclass(frozen=True)
class CategoryCreated(DomainEvent):
    """Emitted when a new category is created.

    Attributes:
        category_name: Name of the created category.
        parent_id: Parent category ID (if hierarchical), or None.
        is_system: True for system categories (e.g., "Uncategorized").
    """

    category_name: str = ""
    parent_id: str | None = None
    is_system: bool = False


@dataclass(frozen=True)
class CategoryUpdated(DomainEvent):
    """Emitted when a category is modified.

    Attributes:
        field: Name of the field that was updated.
        old_value: Previous value (as string, or None).
        new_value: New value (as string, or None).
    """

    field: str = ""
    old_value: str | None = None
    new_value: str | None = None


@dataclass(frozen=True)
class CategoryDeleted(DomainEvent):
    """Emitted when a category is deleted.

    No additional fields - base class provides aggregate_id,
    aggregate_type, and occurred_at.
    """

    pass


@dataclass(frozen=True)
class PayeeCreated(DomainEvent):
    """Emitted when a new payee is auto-created.

    Attributes:
        payee_name: Name of the created payee.
    """

    payee_name: str = ""


@dataclass(frozen=True)
class PayeeUpdated(DomainEvent):
    """Emitted when a payee is modified.

    Attributes:
        field: Name of the field that was updated.
        old_value: Previous value (as string, or None).
        new_value: New value (as string, or None).
    """

    field: str = ""
    old_value: str | None = None
    new_value: str | None = None


@dataclass(frozen=True)
class PayeeDeleted(DomainEvent):
    """Emitted when a payee is deleted.

    No additional fields - base class provides aggregate_id,
    aggregate_type, and occurred_at.
    """

    pass
