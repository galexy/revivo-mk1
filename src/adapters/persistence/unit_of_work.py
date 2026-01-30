"""SQLAlchemy Unit of Work implementation.

The Unit of Work pattern manages transaction boundaries and coordinates
persistence of changes across multiple repositories. Key responsibilities:
- Start/commit/rollback transactions
- Collect domain events from aggregates
- Write events to outbox table in same transaction as data (atomicity)

This implements the UnitOfWork protocol from src/domain/ports/unit_of_work.py.
"""

import json
from typing import Self

from sqlalchemy import insert
from sqlalchemy.orm import Session, sessionmaker

from src.domain.events.base import DomainEvent

from .orm.tables import outbox


class SqlAlchemyUnitOfWork:
    """Unit of Work that manages transaction boundaries.

    Collects domain events and writes them to outbox in same transaction.
    This ensures that events are only persisted if the business data is
    also persisted (atomicity).

    Usage:
        uow = SqlAlchemyUnitOfWork(session_factory)
        with uow:
            # Do work with uow.session
            uow.collect_events(aggregate.events)
            uow.commit()  # Events written to outbox here

    Future: Repositories will be added as properties as they are created:
        with uow:
            uow.accounts.add(account)
            uow.collect_events(account.events)
            uow.commit()
    """

    def __init__(self, session_factory: sessionmaker[Session]):
        """Initialize Unit of Work.

        Args:
            session_factory: Factory for creating SQLAlchemy sessions.
        """
        self._session_factory = session_factory
        self._events: list[DomainEvent] = []
        self._session: Session | None = None

    def __enter__(self) -> Self:
        """Start a new unit of work (transaction).

        Returns:
            Self for use in with statement.
        """
        self._session = self._session_factory()
        # Repositories will be added here as they're created:
        # self.accounts = SqlAlchemyAccountRepository(self._session)
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

    def collect_events(self, events: list[DomainEvent]) -> None:
        """Collect domain events to be persisted with commit.

        Events are not written until commit() is called, ensuring
        they are part of the same transaction as business data.

        Args:
            events: List of domain events to persist.
        """
        self._events.extend(events)

    def commit(self) -> None:
        """Commit transaction, writing events to outbox.

        Events are written to the outbox table as part of the same
        transaction. This ensures atomicity - events are only visible
        if the business data commit succeeds.
        """
        # Write collected events to outbox
        for event in self._events:
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

    def rollback(self) -> None:
        """Rollback transaction and discard events.

        Should be called when an error occurs. Also called automatically
        if an exception is raised in the context manager.
        """
        if self._session:
            self._session.rollback()
        self._events.clear()
