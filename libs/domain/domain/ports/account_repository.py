"""AccountRepository protocol defining account persistence operations.

This is a domain port - an interface that defines how the domain layer
interacts with persistence. The actual implementation lives in the
adapters layer (SqlAlchemyAccountRepository).
"""

from typing import Protocol

from domain.model.account import Account
from domain.model.account_types import AccountStatus, AccountType
from domain.model.entity_id import AccountId, HouseholdId, UserId


class AccountRepository(Protocol):
    """Repository protocol for Account aggregate.

    Defines the persistence operations available for Account entities.
    Implementations must satisfy this structural interface.
    """

    def add(self, account: Account) -> None:
        """Add a new account to the repository.

        Args:
            account: The account to add.
        """
        ...

    def get(self, account_id: AccountId) -> Account | None:
        """Get account by ID.

        Args:
            account_id: The account identifier.

        Returns:
            The account if found, None otherwise.
        """
        ...

    def get_or_raise(self, account_id: AccountId) -> Account:
        """Get account by ID, raising if not found.

        Args:
            account_id: The account identifier.

        Returns:
            The account.

        Raises:
            EntityNotFoundError: If account not found.
        """
        ...

    def get_by_user(
        self,
        user_id: UserId,
        status: AccountStatus | None = None,
        account_type: AccountType | None = None,
    ) -> list[Account]:
        """Get all accounts for a user with optional filters.

        Args:
            user_id: The user identifier.
            status: Optional status filter (ACTIVE, CLOSED).
            account_type: Optional account type filter.

        Returns:
            List of matching accounts, sorted by sort_order then name.
        """
        ...

    def get_by_household(
        self,
        household_id: HouseholdId,
        status: AccountStatus | None = None,
        account_type: AccountType | None = None,
    ) -> list[Account]:
        """Get all accounts for a household with optional filters.

        Args:
            household_id: The household identifier for data scoping.
            status: Optional status filter (ACTIVE, CLOSED).
            account_type: Optional account type filter.

        Returns:
            List of matching accounts, sorted by sort_order then name.
        """
        ...

    def delete(self, account: Account) -> None:
        """Delete an account from the repository.

        Only accounts without transactions can be deleted.
        Use has_transactions() to check before calling.

        Args:
            account: The account to delete.
        """
        ...

    def has_transactions(self, account_id: AccountId) -> bool:
        """Check if account has any transactions.

        Used as a guard before deletion - accounts with transactions
        should be closed, not deleted.

        Args:
            account_id: The account identifier.

        Returns:
            True if account has transactions, False otherwise.
        """
        ...
