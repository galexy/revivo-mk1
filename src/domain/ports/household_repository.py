"""HouseholdRepository protocol defining household persistence operations.

This is a domain port - an interface that defines how the domain layer
interacts with persistence. The actual implementation lives in the
adapters layer (HouseholdRepository).
"""

from typing import Protocol

from src.domain.model.entity_id import HouseholdId
from src.domain.model.household import Household


class HouseholdRepositoryProtocol(Protocol):
    """Repository protocol for Household aggregate.

    Defines the persistence operations available for Household entities.
    Implementations must satisfy this structural interface.
    """

    def add(self, household: Household) -> None:
        """Add a new household to the repository.

        Args:
            household: The household to add.
        """
        ...

    def get_by_id(self, household_id: HouseholdId) -> Household | None:
        """Get household by ID.

        Args:
            household_id: The household identifier.

        Returns:
            The household if found, None otherwise.
        """
        ...

    def update(self, household: Household) -> None:
        """Update an existing household in the repository.

        Args:
            household: The household with updated fields.
        """
        ...
