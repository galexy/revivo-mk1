"""Unit of Work protocol for transaction management.

The Unit of Work pattern maintains a list of objects affected by a business
transaction and coordinates the writing of changes. It provides:
- Transaction boundaries (commit/rollback)
- Access to repositories
- Domain event collection for outbox pattern

Key principles:
- All repository operations occur within a UoW context
- Changes are only persisted on commit()
- Events are collected and persisted to outbox on commit()
"""

from typing import TYPE_CHECKING, Any, Protocol, Self

if TYPE_CHECKING:
    from src.domain.events.base import DomainEvent
    from src.domain.ports.account_repository import AccountRepository
    from src.domain.ports.category_repository import CategoryRepository
    from src.domain.ports.household_repository import HouseholdRepositoryProtocol
    from src.domain.ports.payee_repository import PayeeRepository
    from src.domain.ports.transaction_repository import TransactionRepository
    from src.domain.ports.user_repository import UserRepositoryProtocol


class UnitOfWork(Protocol):
    """Protocol for Unit of Work implementations.

    The UoW manages transaction boundaries and provides access to repositories.
    It uses Python's context manager protocol for automatic cleanup.

    Usage:
        with uow:
            account = uow.accounts.get(account_id)
            account.deposit(money)
            uow.collect_events(account.events)
            await uow.commit()

    Repository accessors:
    - accounts: AccountRepository
    - categories: CategoryRepository
    - payees: PayeeRepository
    - transactions: TransactionRepository
    - users: UserRepositoryProtocol
    - households: HouseholdRepositoryProtocol
    - refresh_tokens: RefreshTokenRepository
    """

    @property
    def accounts(self) -> "AccountRepository":
        """Access to Account repository."""
        ...

    @property
    def categories(self) -> "CategoryRepository":
        """Access to Category repository."""
        ...

    @property
    def payees(self) -> "PayeeRepository":
        """Access to Payee repository."""
        ...

    @property
    def transactions(self) -> "TransactionRepository":
        """Access to Transaction repository."""
        ...

    @property
    def users(self) -> "UserRepositoryProtocol":
        """Access to User repository."""
        ...

    @property
    def households(self) -> "HouseholdRepositoryProtocol":
        """Access to Household repository."""
        ...

    @property
    def refresh_tokens(self) -> Any:
        """Access to RefreshToken repository.

        Returns the RefreshTokenRepository implementation. Typed as Any
        because RefreshTokenRepository is infrastructure (not a domain
        protocol) -- refresh tokens are security records, not aggregates.
        """
        ...

    def __enter__(self) -> Self:
        """Enter the UoW context and begin a transaction.

        Returns:
            Self for use in with statement.
        """
        ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> None:
        """Exit the UoW context.

        If an exception occurred, rollback. Always close the session.

        Args:
            exc_type: Exception type if an exception was raised.
            exc_val: Exception instance if an exception was raised.
            exc_tb: Traceback if an exception was raised.
        """
        ...

    async def commit(self) -> None:
        """Commit all changes to the database.

        This persists all added/modified entities and any collected
        domain events to the outbox table. After DB commit succeeds,
        publishes events to registered handlers asynchronously.
        """
        ...

    def rollback(self) -> None:
        """Rollback all changes in the current transaction.

        Discards all pending changes and collected events.
        """
        ...

    def collect_events(self, events: list["DomainEvent"]) -> None:
        """Collect domain events for persistence to outbox.

        Events are written to the outbox table when commit() is called,
        ensuring they are persisted in the same transaction as the
        business data changes.

        Args:
            events: List of domain events to persist.
        """
        ...

    def flush(self) -> None:
        """Flush pending changes to the database without committing.

        Used to ensure entities are visible for subsequent operations
        within the same transaction (e.g., FK constraint satisfaction).
        """
        ...
