"""Payee entity for managed payee list.

Payees are a managed entity list with autocomplete support.
New payees are auto-created when entering transactions.

Key features:
- Name normalization for case-insensitive matching
- Optional default category for auto-categorization
- Usage tracking for sorting autocomplete by relevance
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Self

from src.domain.model.entity_id import CategoryId, PayeeId, UserId


@dataclass(eq=False)
class Payee:
    """Managed payee entity for transaction payee autocomplete.

    Per CONTEXT:
    - Payees are a managed entity list
    - New payees auto-created when entering transactions
    - Optional default_category_id for auto-fill (Claude's discretion)

    Attributes:
        id: Unique payee identifier.
        user_id: Owner of this payee.
        name: Display name of the payee.
        normalized_name: Lowercase name for matching/deduplication.
        default_category_id: Optional default category for auto-categorization.
        last_used_at: When this payee was last used in a transaction.
        usage_count: Number of times this payee has been used.
        created_at: When the payee was created.
        updated_at: When the payee was last modified.

    Note:
        eq=False because entity identity is by ID, not field comparison.
    """

    id: PayeeId
    user_id: UserId
    name: str
    normalized_name: str
    default_category_id: CategoryId | None = None

    # Usage tracking for autocomplete relevance
    last_used_at: datetime | None = None
    usage_count: int = 0

    # Audit timestamps
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @classmethod
    def create(
        cls,
        user_id: UserId,
        name: str,
        default_category_id: CategoryId | None = None,
    ) -> Self:
        """Create a new payee with normalized name for matching.

        Args:
            user_id: Owner of the payee.
            name: Display name (will be trimmed).
            default_category_id: Optional default category for auto-fill.

        Returns:
            New Payee instance.

        Raises:
            ValueError: If name is empty or whitespace-only.
        """
        stripped_name = name.strip()
        if not stripped_name:
            raise ValueError("Payee name cannot be empty")

        return cls(
            id=PayeeId.generate(),
            user_id=user_id,
            name=stripped_name,
            normalized_name=stripped_name.lower(),
            default_category_id=default_category_id,
        )

    def update_name(self, new_name: str) -> None:
        """Update the payee name.

        Args:
            new_name: New display name for the payee.

        Raises:
            ValueError: If new_name is empty or whitespace-only.
        """
        stripped_name = new_name.strip()
        if not stripped_name:
            raise ValueError("Payee name cannot be empty")

        self.name = stripped_name
        self.normalized_name = stripped_name.lower()
        self.updated_at = datetime.now(UTC)

    def set_default_category(self, category_id: CategoryId | None) -> None:
        """Set or clear the default category for auto-categorization.

        Args:
            category_id: Category to use as default, or None to clear.
        """
        self.default_category_id = category_id
        self.updated_at = datetime.now(UTC)

    def record_usage(self) -> None:
        """Track that this payee was used in a transaction.

        Updates last_used_at and increments usage_count for
        sorting autocomplete by relevance.
        """
        self.last_used_at = datetime.now(UTC)
        self.usage_count += 1
        self.updated_at = datetime.now(UTC)
