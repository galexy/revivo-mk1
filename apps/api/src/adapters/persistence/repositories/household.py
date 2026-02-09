"""Household repository implementation.

SQLAlchemy implementation of HouseholdRepositoryProtocol. Uses ORM-mapped
Household entity for persistence via imperative mapping.
"""

from sqlalchemy.orm import Session

from domain.model.entity_id import HouseholdId
from domain.model.household import Household


class HouseholdRepository:
    """SQLAlchemy implementation of HouseholdRepositoryProtocol.

    Uses the ORM-mapped Household class for all persistence operations.
    """

    def __init__(self, session: Session) -> None:
        """Initialize repository with SQLAlchemy session.

        Args:
            session: Active SQLAlchemy session for database operations.
        """
        self._session = session

    def add(self, household: Household) -> None:
        """Add household to session for persistence.

        Args:
            household: Household entity to persist.
        """
        self._session.add(household)

    def get_by_id(self, household_id: HouseholdId) -> Household | None:
        """Get household by ID, or None if not found.

        Args:
            household_id: The household identifier.

        Returns:
            Household entity or None.
        """
        return (
            self._session.query(Household)
            .filter(
                Household.id == household_id  # type: ignore[arg-type]  # SQLAlchemy imperative mapping: domain attr becomes Column at runtime
            )
            .first()
        )

    def update(self, household: Household) -> None:
        """Update an existing household.

        Args:
            household: The household with updated fields.
        """
        self._session.merge(household)
