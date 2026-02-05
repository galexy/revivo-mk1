"""Household aggregate root for multi-user data scoping.

A Household owns all financial data (accounts, transactions, categories).
Users belong to households. Initially one household per user, but the
model supports multiple users per household (future Phase 25).
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Self

from .entity_id import HouseholdId, UserId


@dataclass(eq=False)
class Household:
    """Household aggregate root.

    Owns all financial data. Users are members of households.

    Attributes:
        id: Unique household identifier
        name: Display name (e.g., "Smith Family")
        owner_id: UserId of the household creator/owner
        created_at: When household was created
        updated_at: Last modification timestamp
    """

    id: HouseholdId
    name: str
    owner_id: UserId
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @classmethod
    def create(
        cls,
        name: str,
        owner_id: UserId,
    ) -> Self:
        """Create a new household.

        Args:
            name: Display name for the household
            owner_id: User who owns/created the household

        Returns:
            New Household instance with generated ID
        """
        now = datetime.now(UTC)
        return cls(
            id=HouseholdId.generate(),
            name=name,
            owner_id=owner_id,
            created_at=now,
            updated_at=now,
        )

    def update_name(self, name: str) -> None:
        """Update household display name."""
        self.name = name
        self.updated_at = datetime.now(UTC)
