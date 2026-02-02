"""SQLAlchemy implementation of PayeeRepository.

Handles persistence of Payee entity with autocomplete support.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.model.entity_id import CategoryId, PayeeId, UserId
from src.domain.model.payee import Payee


class SqlAlchemyPayeeRepository:
    """SQLAlchemy implementation of PayeeRepository.

    Provides autocomplete search by name prefix and usage-based sorting.
    """

    def __init__(self, session: Session) -> None:
        """Initialize repository with SQLAlchemy session.

        Args:
            session: Active SQLAlchemy session for database operations.
        """
        self._session = session

    def add(self, payee: Payee) -> None:
        """Add a new payee to the session.

        Args:
            payee: Payee entity to persist.
        """
        self._session.add(payee)

    def get(self, payee_id: PayeeId) -> Payee | None:
        """Get payee by ID.

        Args:
            payee_id: The payee identifier.

        Returns:
            Payee entity or None if not found.
        """
        payee = self._session.get(Payee, str(payee_id))
        if payee is not None:
            self._reconstruct_value_objects(payee)
        return payee

    def get_by_user(self, user_id: UserId) -> list[Payee]:
        """Get all payees for a user.

        Args:
            user_id: The user identifier.

        Returns:
            List of Payee entities ordered by usage count (descending) and name.
        """
        stmt = (
            select(Payee)
            .where(Payee.user_id == str(user_id))
            .order_by(Payee.usage_count.desc(), Payee.name)
        )
        result = self._session.execute(stmt)
        payees = list(result.scalars().all())

        for payee in payees:
            self._reconstruct_value_objects(payee)

        return payees

    def find_by_name(self, user_id: UserId, name: str) -> Payee | None:
        """Find payee by normalized name (case-insensitive).

        Args:
            user_id: The user identifier.
            name: The payee name to search for.

        Returns:
            Payee entity or None if not found.
        """
        normalized = name.strip().lower()
        stmt = (
            select(Payee)
            .where(Payee.user_id == str(user_id))
            .where(Payee.normalized_name == normalized)
        )
        payee = self._session.scalar(stmt)
        if payee is not None:
            self._reconstruct_value_objects(payee)
        return payee

    def search(
        self,
        user_id: UserId,
        query: str,
        limit: int = 10,
    ) -> list[Payee]:
        """Search payees by name prefix for autocomplete.

        Results are sorted by usage count (descending) for relevance.

        Args:
            user_id: The user identifier.
            query: Search prefix.
            limit: Maximum number of results.

        Returns:
            List of matching Payee entities.
        """
        normalized_query = query.strip().lower()
        stmt = (
            select(Payee)
            .where(Payee.user_id == str(user_id))
            .where(Payee.normalized_name.startswith(normalized_query))
            .order_by(Payee.usage_count.desc(), Payee.name)
            .limit(limit)
        )
        result = self._session.execute(stmt)
        payees = list(result.scalars().all())

        for payee in payees:
            self._reconstruct_value_objects(payee)

        return payees

    def get_or_create(self, user_id: UserId, name: str) -> Payee:
        """Get existing payee or create new one.

        Used for auto-creation pattern when entering transactions.

        Args:
            user_id: The user identifier.
            name: The payee name.

        Returns:
            Existing or newly created Payee entity.
        """
        existing = self.find_by_name(user_id, name)
        if existing:
            return existing

        payee = Payee.create(user_id=user_id, name=name)
        self._session.add(payee)
        return payee

    def update(self, payee: Payee) -> None:
        """Update an existing payee.

        Args:
            payee: Payee entity with updates.

        Note:
            SQLAlchemy automatically tracks changes to managed entities,
            so this method exists primarily for protocol compliance.
        """
        # Changes are tracked by SQLAlchemy session
        pass

    def delete(self, payee_id: PayeeId) -> None:
        """Delete a payee.

        Args:
            payee_id: The payee identifier to delete.
        """
        payee = self.get(payee_id)
        if payee:
            self._session.delete(payee)

    def _reconstruct_value_objects(self, payee: Payee) -> None:
        """Reconstruct value objects from database primitives.

        Args:
            payee: Payee entity loaded from database.
        """
        # Reconstruct PayeeId from string
        if isinstance(payee.id, str):
            object.__setattr__(payee, "id", PayeeId.from_string(payee.id))

        # Reconstruct UserId from string
        if isinstance(payee.user_id, str):
            object.__setattr__(payee, "user_id", UserId.from_string(payee.user_id))

        # Reconstruct default_category_id CategoryId from string
        if payee.default_category_id is not None and isinstance(
            payee.default_category_id, str
        ):
            object.__setattr__(
                payee,
                "default_category_id",
                CategoryId.from_string(payee.default_category_id),
            )
