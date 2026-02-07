"""Category repository protocol."""

from typing import Protocol

from src.domain.model.category import Category
from src.domain.model.entity_id import CategoryId, HouseholdId, UserId


class CategoryRepository(Protocol):
    """Repository protocol for Category entity."""

    def add(self, category: Category) -> None:
        """Add a new category."""
        ...

    def get(self, category_id: CategoryId) -> Category | None:
        """Get category by ID."""
        ...

    def get_by_user(self, user_id: UserId) -> list[Category]:
        """Get all categories for a user (including system categories)."""
        ...

    def get_children(self, parent_id: CategoryId) -> list[Category]:
        """Get child categories of a parent."""
        ...

    def get_system_category(self, user_id: UserId, name: str) -> Category | None:
        """Get a system category by name (e.g., 'Uncategorized')."""
        ...

    def get_or_create_uncategorized(
        self, user_id: UserId, household_id: HouseholdId | None = None
    ) -> Category:
        """Get or create the 'Uncategorized' system category for a user."""
        ...

    def update(self, category: Category) -> None:
        """Update an existing category."""
        ...

    def delete(self, category_id: CategoryId) -> None:
        """Delete a category."""
        ...

    def count_transactions(self, category_id: CategoryId) -> int:
        """Count transactions using this category (for deletion validation)."""
        ...
