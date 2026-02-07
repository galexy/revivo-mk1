"""Repository protocol for aggregate persistence.

The Repository pattern provides a collection-like interface for accessing
domain objects. Each aggregate root has its own repository with operations
specific to that aggregate.

This module defines the generic Repository protocol. Concrete repository
interfaces (AccountRepository, TransactionRepository) will be defined in
later phases when their aggregates are created.

Key principles:
- One repository per aggregate root
- Repositories expose domain-specific operations, not generic CRUD
- Uses Protocol for interface definition (structural subtyping)
"""

from typing import Generic, Protocol, TypeVar

from src.domain.exceptions import EntityNotFoundError

# Type variables for generic repository
T = TypeVar("T")  # Entity/Aggregate type
ID = TypeVar("ID")  # Entity ID type


class Repository(Protocol[T, ID]):
    """Generic repository protocol for aggregate persistence.

    Concrete repositories should implement this protocol for their
    specific aggregate type. Additional domain-specific methods
    can be added as needed.

    Type Parameters:
        T: The aggregate/entity type this repository manages.
        ID: The identifier type for the aggregate.

    Example:
        class AccountRepository(Protocol):
            def add(self, account: Account) -> None: ...
            def get(self, account_id: AccountId) -> Account | None: ...
            def get_by_user(self, user_id: UserId) -> list[Account]: ...
    """

    def add(self, entity: T) -> None:
        """Add a new entity to the repository.

        Args:
            entity: The entity to add.

        Note:
            The entity is not persisted until UnitOfWork.commit() is called.
        """
        ...

    def get(self, id: ID) -> T | None:
        """Retrieve an entity by its identifier.

        Args:
            id: The entity's identifier.

        Returns:
            The entity if found, None otherwise.
        """
        ...

    def get_or_raise(self, id: ID) -> T:
        """Retrieve an entity by its identifier, raising if not found.

        Args:
            id: The entity's identifier.

        Returns:
            The entity.

        Raises:
            EntityNotFoundError: If no entity with the given ID exists.
        """
        ...
