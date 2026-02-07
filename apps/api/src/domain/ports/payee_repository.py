"""Payee repository protocol."""

from typing import Protocol

from src.domain.model.entity_id import HouseholdId, PayeeId, UserId
from src.domain.model.payee import Payee


class PayeeRepository(Protocol):
    """Repository protocol for Payee entity."""

    def add(self, payee: Payee) -> None:
        """Add a new payee."""
        ...

    def get(self, payee_id: PayeeId) -> Payee | None:
        """Get payee by ID."""
        ...

    def get_by_user(self, user_id: UserId) -> list[Payee]:
        """Get all payees for a user."""
        ...

    def find_by_name(self, user_id: UserId, name: str) -> Payee | None:
        """Find payee by normalized name (case-insensitive)."""
        ...

    def search(
        self,
        user_id: UserId,
        query: str,
        limit: int = 10,
    ) -> list[Payee]:
        """Search payees by name prefix for autocomplete."""
        ...

    def get_or_create(
        self, user_id: UserId, name: str, household_id: HouseholdId | None = None
    ) -> Payee:
        """Get existing payee or create new one (for auto-creation pattern)."""
        ...

    def update(self, payee: Payee) -> None:
        """Update an existing payee."""
        ...

    def delete(self, payee_id: PayeeId) -> None:
        """Delete a payee."""
        ...
