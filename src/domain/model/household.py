"""Household aggregate root for multi-user data scoping.

A Household owns all financial data (accounts, transactions, categories).
Users belong to households. Initially one household per user, but the
model supports multiple users per household (future Phase 25).

Ownership is tracked via the user's role field (role="owner") rather than
a separate owner_id on the household, avoiding circular FK dependencies.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Self

from .entity_id import HouseholdId


@dataclass(eq=False)
class Household:
    """Household aggregate root.

    Owns all financial data. Users are members of households.

    Attributes:
        id: Unique household identifier
        name: Display name (e.g., "Smith Family")
        created_at: When household was created
        updated_at: Last modification timestamp
    """

    id: HouseholdId
    name: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @classmethod
    def create(
        cls,
        name: str,
    ) -> Self:
        """Create a new household.

        Args:
            name: Display name for the household

        Returns:
            New Household instance with generated ID
        """
        now = datetime.now(UTC)
        return cls(
            id=HouseholdId.generate(),
            name=name,
            created_at=now,
            updated_at=now,
        )

    def update_name(self, name: str) -> None:
        """Update household display name."""
        self.name = name
        self.updated_at = datetime.now(UTC)
