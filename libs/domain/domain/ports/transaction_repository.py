"""Transaction repository protocol.

Defines the interface for transaction persistence following the ports/adapters pattern.
"""

from datetime import date
from decimal import Decimal
from typing import Protocol

from src.domain.model.entity_id import AccountId, CategoryId, TransactionId, UserId
from src.domain.model.transaction import Transaction


class TransactionRepository(Protocol):
    """Repository protocol for Transaction aggregate."""

    def add(self, transaction: Transaction) -> None:
        """Add a new transaction."""
        ...

    def get(self, transaction_id: TransactionId) -> Transaction | None:
        """Get transaction by ID."""
        ...

    def get_by_account(
        self,
        account_id: AccountId,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Transaction]:
        """Get transactions for an account (chronological by effective_date)."""
        ...

    def get_by_user(
        self,
        user_id: UserId,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Transaction]:
        """Get all transactions for a user."""
        ...

    def get_mirrors_for_source(
        self,
        source_transaction_id: TransactionId,
    ) -> list[Transaction]:
        """Get mirror transactions for a source transaction."""
        ...

    def search(
        self,
        user_id: UserId,
        query: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Transaction]:
        """Full-text search on payee and memo."""
        ...

    def filter(
        self,
        user_id: UserId,
        account_id: AccountId | None = None,
        category_id: CategoryId | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        amount_min: Decimal | None = None,
        amount_max: Decimal | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Transaction]:
        """Filter transactions by various criteria."""
        ...

    def count_by_account(self, account_id: AccountId) -> int:
        """Count transactions for an account (for deletion validation)."""
        ...

    def update(self, transaction: Transaction) -> None:
        """Update an existing transaction."""
        ...

    def delete(self, transaction_id: TransactionId) -> None:
        """Delete a transaction."""
        ...
