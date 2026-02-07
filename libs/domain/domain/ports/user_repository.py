"""UserRepository protocol defining user persistence operations.

This is a domain port - an interface that defines how the domain layer
interacts with persistence. The actual implementation lives in the
adapters layer (UserRepository).
"""

from typing import Protocol

from src.domain.model.entity_id import UserId
from src.domain.model.user import User


class UserRepositoryProtocol(Protocol):
    """Repository protocol for User aggregate.

    Defines the persistence operations available for User entities.
    Implementations must satisfy this structural interface.
    """

    def add(self, user: User) -> None:
        """Add a new user to the repository.

        Args:
            user: The user to add.
        """
        ...

    def get_by_id(self, user_id: UserId) -> User | None:
        """Get user by ID.

        Args:
            user_id: The user identifier.

        Returns:
            The user if found, None otherwise.
        """
        ...

    def get_by_email(self, email: str) -> User | None:
        """Get user by email address.

        Email lookup is case-insensitive (emails are stored lowercase).

        Args:
            email: The email address to search for.

        Returns:
            The user if found, None otherwise.
        """
        ...

    def update(self, user: User) -> None:
        """Update an existing user in the repository.

        Args:
            user: The user with updated fields.
        """
        ...
