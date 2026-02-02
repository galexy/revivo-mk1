"""SQLAlchemy implementation of CategoryRepository.

Handles persistence of Category entity with value object reconstruction.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.domain.model.category import Category, SYSTEM_CATEGORY_UNCATEGORIZED
from src.domain.model.entity_id import CategoryId, UserId
from src.adapters.persistence.orm.tables import categories, split_lines


class SqlAlchemyCategoryRepository:
    """SQLAlchemy implementation of CategoryRepository.

    Handles loading and saving Category entities.
    """

    def __init__(self, session: Session) -> None:
        """Initialize repository with SQLAlchemy session.

        Args:
            session: Active SQLAlchemy session for database operations.
        """
        self._session = session

    def add(self, category: Category) -> None:
        """Add a new category to the session.

        Args:
            category: Category entity to persist.
        """
        self._session.add(category)

    def get(self, category_id: CategoryId) -> Category | None:
        """Get category by ID.

        Args:
            category_id: The category identifier.

        Returns:
            Category entity or None if not found.
        """
        category = self._session.get(Category, str(category_id))
        if category is not None:
            self._reconstruct_value_objects(category)
        return category

    def get_by_user(self, user_id: UserId) -> list[Category]:
        """Get all categories for a user (including system categories).

        Args:
            user_id: The user identifier.

        Returns:
            List of Category entities ordered by sort_order and name.
        """
        stmt = (
            select(Category)
            .where(Category.user_id == str(user_id))
            .order_by(Category.sort_order, Category.name)
        )
        result = self._session.execute(stmt)
        categories = list(result.scalars().all())

        for category in categories:
            self._reconstruct_value_objects(category)

        return categories

    def get_children(self, parent_id: CategoryId) -> list[Category]:
        """Get child categories of a parent.

        Args:
            parent_id: The parent category identifier.

        Returns:
            List of child Category entities.
        """
        stmt = (
            select(Category)
            .where(Category.parent_id == str(parent_id))
            .order_by(Category.sort_order, Category.name)
        )
        result = self._session.execute(stmt)
        children = list(result.scalars().all())

        for category in children:
            self._reconstruct_value_objects(category)

        return children

    def get_system_category(self, user_id: UserId, name: str) -> Category | None:
        """Get a system category by name.

        Args:
            user_id: The user identifier.
            name: The system category name (e.g., 'Uncategorized').

        Returns:
            Category entity or None if not found.
        """
        stmt = (
            select(Category)
            .where(Category.user_id == str(user_id))
            .where(Category.is_system == True)  # noqa: E712
            .where(Category.name == name)
        )
        category = self._session.scalar(stmt)
        if category is not None:
            self._reconstruct_value_objects(category)
        return category

    def get_or_create_uncategorized(self, user_id: UserId) -> Category:
        """Get or create the 'Uncategorized' system category for a user.

        Args:
            user_id: The user identifier.

        Returns:
            The 'Uncategorized' category for the user.
        """
        existing = self.get_system_category(user_id, SYSTEM_CATEGORY_UNCATEGORIZED)
        if existing:
            return existing

        category = Category.create_system_category(user_id, SYSTEM_CATEGORY_UNCATEGORIZED)
        self._session.add(category)
        return category

    def update(self, category: Category) -> None:
        """Update an existing category.

        Args:
            category: Category entity with updates.

        Note:
            SQLAlchemy automatically tracks changes to managed entities,
            so this method exists primarily for protocol compliance.
        """
        # Changes are tracked by SQLAlchemy session
        pass

    def delete(self, category_id: CategoryId) -> None:
        """Delete a category.

        Args:
            category_id: The category identifier to delete.
        """
        category = self.get(category_id)
        if category:
            self._session.delete(category)

    def count_transactions(self, category_id: CategoryId) -> int:
        """Count transactions using this category.

        Used for deletion validation - prevents deleting categories in use.

        Args:
            category_id: The category identifier.

        Returns:
            Number of split lines referencing this category.
        """
        stmt = (
            select(func.count())
            .select_from(split_lines)
            .where(split_lines.c.category_id == str(category_id))
        )
        return self._session.scalar(stmt) or 0

    def _reconstruct_value_objects(self, category: Category) -> None:
        """Reconstruct value objects from database primitives.

        Args:
            category: Category entity loaded from database.
        """
        # Reconstruct CategoryId from string
        if isinstance(category.id, str):
            object.__setattr__(category, "id", CategoryId.from_string(category.id))

        # Reconstruct UserId from string
        if isinstance(category.user_id, str):
            object.__setattr__(category, "user_id", UserId.from_string(category.user_id))

        # Reconstruct parent_id CategoryId from string
        if category.parent_id is not None and isinstance(category.parent_id, str):
            object.__setattr__(
                category, "parent_id", CategoryId.from_string(category.parent_id)
            )

        # Ensure _events list exists (transient field, not loaded from DB)
        if not hasattr(category, "_events") or getattr(category, "_events", None) is None:
            object.__setattr__(category, "_events", [])
