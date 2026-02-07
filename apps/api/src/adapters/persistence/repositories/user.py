"""User repository implementation.

SQLAlchemy implementation of UserRepositoryProtocol. Uses ORM-mapped
User entity for persistence via imperative mapping.
"""

from sqlalchemy.orm import Session

from src.domain.model.entity_id import UserId
from src.domain.model.user import User


class UserRepository:
    """SQLAlchemy implementation of UserRepositoryProtocol.

    Uses the ORM-mapped User class for all persistence operations.
    The User._events list is excluded from mapping (transient) and
    is re-initialized after loading if needed.
    """

    def __init__(self, session: Session) -> None:
        """Initialize repository with SQLAlchemy session.

        Args:
            session: Active SQLAlchemy session for database operations.
        """
        self._session = session

    def add(self, user: User) -> None:
        """Add user to session for persistence.

        Args:
            user: User entity to persist.
        """
        self._session.add(user)

    def get_by_id(self, user_id: UserId) -> User | None:
        """Get user by ID, or None if not found.

        Args:
            user_id: The user identifier.

        Returns:
            User entity or None.
        """
        user = self._session.query(User).filter(User.id == user_id).first()
        if user is not None:
            self._ensure_events_list(user)
        return user

    def get_by_email(self, email: str) -> User | None:
        """Get user by email address, or None if not found.

        Email lookup is case-insensitive (lowercased before query).

        Args:
            email: The email address to search for.

        Returns:
            User entity or None.
        """
        user = self._session.query(User).filter(User.email == email.lower()).first()
        if user is not None:
            self._ensure_events_list(user)
        return user

    def update(self, user: User) -> None:
        """Update an existing user.

        Args:
            user: The user with updated fields.
        """
        self._session.merge(user)

    def _ensure_events_list(self, user: User) -> None:
        """Ensure _events list exists on loaded user.

        _events is excluded from ORM mapping (transient), so it may
        not be present on entities loaded from the database.

        Args:
            user: User entity loaded from database.
        """
        if not hasattr(user, "_events") or getattr(user, "_events", None) is None:
            object.__setattr__(user, "_events", [])
