"""SQLAlchemy Unit of Work implementation.

The Unit of Work pattern manages transaction boundaries and coordinates
persistence of changes across multiple repositories. Key responsibilities:
- Start/commit/rollback transactions
- Collect domain events from aggregates
- Write events to outbox table in same transaction as data (atomicity)

This implements the UnitOfWork protocol from src/domain/ports/unit_of_work.py.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Self

from sqlalchemy import insert
from sqlalchemy.orm import Session, sessionmaker

from src.domain.events.base import DomainEvent

from .orm.tables import outbox

if TYPE_CHECKING:
    from .repositories.account import SqlAlchemyAccountRepository
    from .repositories.category import SqlAlchemyCategoryRepository
    from .repositories.household import HouseholdRepository
    from .repositories.payee import SqlAlchemyPayeeRepository
    from .repositories.refresh_token import RefreshTokenRepository
    from .repositories.transaction import SqlAlchemyTransactionRepository
    from .repositories.user import UserRepository


class SqlAlchemyUnitOfWork:
    """Unit of Work that manages transaction boundaries.

    Collects domain events and writes them to outbox in same transaction.
    This ensures that events are only persisted if the business data is
    also persisted (atomicity).

    Usage:
        uow = SqlAlchemyUnitOfWork(session_factory)
        with uow:
            uow.accounts.add(account)
            uow.collect_events(account.events)
            uow.commit()  # Events written to outbox here

    Repositories are lazily created on first access via properties.
    """

    _accounts: SqlAlchemyAccountRepository | None
    _categories: SqlAlchemyCategoryRepository | None
    _households: HouseholdRepository | None
    _payees: SqlAlchemyPayeeRepository | None
    _refresh_tokens: RefreshTokenRepository | None
    _transactions: SqlAlchemyTransactionRepository | None
    _users: UserRepository | None

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        """Initialize Unit of Work.

        Args:
            session_factory: Factory for creating SQLAlchemy sessions.
        """
        self._session_factory = session_factory
        self._events: list[DomainEvent] = []
        self._session: Session | None = None
        self._accounts: SqlAlchemyAccountRepository | None = None
        self._categories: SqlAlchemyCategoryRepository | None = None
        self._households: HouseholdRepository | None = None
        self._payees: SqlAlchemyPayeeRepository | None = None
        self._refresh_tokens: RefreshTokenRepository | None = None
        self._transactions: SqlAlchemyTransactionRepository | None = None
        self._users: UserRepository | None = None

    def __enter__(self) -> Self:
        """Start a new unit of work (transaction).

        Returns:
            Self for use in with statement.
        """
        self._session = self._session_factory()
        # Reset repository instances for fresh session
        self._accounts = None
        self._categories = None
        self._households = None
        self._payees = None
        self._refresh_tokens = None
        self._transactions = None
        self._users = None
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """End the unit of work.

        Rolls back if an exception occurred, then closes session.
        """
        if exc_type:
            self.rollback()
        if self._session:
            self._session.close()

    @property
    def session(self) -> Session:
        """Access to underlying session for repositories.

        Returns:
            Active SQLAlchemy session.

        Raises:
            RuntimeError: If accessed outside of context manager.
        """
        if self._session is None:
            raise RuntimeError("UnitOfWork must be used as context manager")
        return self._session

    @property
    def accounts(self) -> SqlAlchemyAccountRepository:
        """Access to Account repository.

        Lazily creates repository on first access.

        Returns:
            SqlAlchemyAccountRepository for account persistence.
        """
        if self._accounts is None:
            from .repositories.account import SqlAlchemyAccountRepository

            self._accounts = SqlAlchemyAccountRepository(self.session)
        return self._accounts

    @property
    def categories(self) -> SqlAlchemyCategoryRepository:
        """Access to Category repository.

        Lazily creates repository on first access.

        Returns:
            SqlAlchemyCategoryRepository for category persistence.
        """
        if self._categories is None:
            from .repositories.category import SqlAlchemyCategoryRepository

            self._categories = SqlAlchemyCategoryRepository(self.session)
        return self._categories

    @property
    def payees(self) -> SqlAlchemyPayeeRepository:
        """Access to Payee repository.

        Lazily creates repository on first access.

        Returns:
            SqlAlchemyPayeeRepository for payee persistence.
        """
        if self._payees is None:
            from .repositories.payee import SqlAlchemyPayeeRepository

            self._payees = SqlAlchemyPayeeRepository(self.session)
        return self._payees

    @property
    def transactions(self) -> SqlAlchemyTransactionRepository:
        """Access to Transaction repository.

        Lazily creates repository on first access.

        Returns:
            SqlAlchemyTransactionRepository for transaction persistence.
        """
        if self._transactions is None:
            from .repositories.transaction import SqlAlchemyTransactionRepository

            self._transactions = SqlAlchemyTransactionRepository(self.session)
        return self._transactions

    @property
    def users(self) -> UserRepository:
        """Access to User repository.

        Lazily creates repository on first access.

        Returns:
            UserRepository for user persistence.
        """
        if self._users is None:
            from .repositories.user import UserRepository

            self._users = UserRepository(self.session)
        return self._users

    @property
    def households(self) -> HouseholdRepository:
        """Access to Household repository.

        Lazily creates repository on first access.

        Returns:
            HouseholdRepository for household persistence.
        """
        if self._households is None:
            from .repositories.household import HouseholdRepository

            self._households = HouseholdRepository(self.session)
        return self._households

    @property
    def refresh_tokens(self) -> RefreshTokenRepository:
        """Access to RefreshToken repository.

        Lazily creates repository on first access.

        Returns:
            RefreshTokenRepository for refresh token persistence.
        """
        if self._refresh_tokens is None:
            from .repositories.refresh_token import RefreshTokenRepository

            self._refresh_tokens = RefreshTokenRepository(self.session)
        return self._refresh_tokens

    def collect_events(self, events: list[DomainEvent]) -> None:
        """Collect domain events to be persisted with commit.

        Events are not written until commit() is called, ensuring
        they are part of the same transaction as business data.

        Args:
            events: List of domain events to persist.
        """
        self._events.extend(events)

    def commit(self) -> None:
        """Commit transaction, writing events to outbox, then publishing.

        Events are written to the outbox table as part of the same
        transaction. This ensures atomicity - events are only visible
        if the business data commit succeeds.

        Events that don't conform to the DomainEvent protocol (missing
        event_type, aggregate_type, aggregate_id, to_dict) are skipped
        for outbox writing. All events are published to handlers.

        CRITICAL: Events are published AFTER commit succeeds to ensure
        handlers see committed data (see 05-RESEARCH.md Pitfall 1).
        """
        # Capture events before commit clears them
        events_to_publish = list(self._events)

        # Write collected events to outbox
        for event in self._events:
            # Only write events that conform to DomainEvent protocol
            if hasattr(event, "event_type") and hasattr(event, "aggregate_type"):
                self.session.execute(
                    insert(outbox).values(
                        event_type=event.event_type,
                        aggregate_type=event.aggregate_type,
                        aggregate_id=event.aggregate_id,
                        payload=json.dumps(event.to_dict(), default=str),
                    )
                )
        self.session.commit()
        self._events.clear()

        # Publish events to handlers AFTER commit succeeds
        # Import inside method to avoid circular import issues
        from src.application.event_bus import publish_all

        publish_all(events_to_publish)

    def flush(self) -> None:
        """Flush pending changes to database without committing.

        Used to ensure ORM-tracked entities are visible to raw SQL operations
        within the same transaction (e.g., payee must exist before transaction
        insert that references it via FK).
        """
        self.session.flush()

    def rollback(self) -> None:
        """Rollback transaction and discard events.

        Should be called when an error occurs. Also called automatically
        if an exception is raised in the context manager.
        """
        if self._session:
            self._session.rollback()
        self._events.clear()
