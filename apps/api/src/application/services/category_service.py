"""Application service for Category use cases.

Handles category CRUD, hierarchy management, and system category initialization.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from domain.model.category import Category, CategoryType, SYSTEM_CATEGORY_UNCATEGORIZED
from domain.model.entity_id import CategoryId, HouseholdId, UserId

if TYPE_CHECKING:
    from domain.ports.unit_of_work import UnitOfWork


@dataclass(frozen=True, slots=True)
class CategoryError:
    """Error result for category operations."""

    code: str
    message: str


class CategoryService:
    """Application service for category management."""

    def __init__(self, uow: "UnitOfWork") -> None:
        self._uow = uow

    async def ensure_system_categories(
        self, user_id: UserId, household_id: HouseholdId | None = None
    ) -> Category:
        """Ensure system categories exist for user.

        Creates 'Uncategorized' if it doesn't exist.
        Returns the Uncategorized category.
        """
        with self._uow:
            category = self._uow.categories.get_or_create_uncategorized(
                user_id, household_id=household_id
            )
            await self._uow.commit()
            return category

    async def create_category(
        self,
        user_id: UserId,
        name: str,
        parent_id: CategoryId | None = None,
        icon: str | None = None,
        category_type: CategoryType = CategoryType.EXPENSE,
        household_id: HouseholdId | None = None,
    ) -> Category | CategoryError:
        """Create a new user category."""
        with self._uow:
            # Validate parent exists and belongs to user
            if parent_id:
                parent = self._uow.categories.get(parent_id)
                if parent is None:
                    return CategoryError("PARENT_NOT_FOUND", "Parent category not found")
                if parent.user_id != user_id:
                    return CategoryError(
                        "PARENT_NOT_OWNED", "Parent category does not belong to user"
                    )
                # Prevent nesting system categories
                if parent.is_system:
                    return CategoryError(
                        "CANNOT_NEST_UNDER_SYSTEM",
                        "Cannot create subcategory under system category",
                    )

            category = Category.create(
                user_id=user_id,
                name=name,
                parent_id=parent_id,
                icon=icon,
                category_type=category_type,
                household_id=household_id,
            )

            self._uow.categories.add(category)
            self._uow.collect_events(category.events)
            category.clear_events()
            await self._uow.commit()

            return category

    def get_category(self, category_id: CategoryId) -> Category | None:
        """Get a category by ID."""
        with self._uow:
            return self._uow.categories.get(category_id)

    def get_user_categories(self, user_id: UserId) -> list[Category]:
        """Get all categories for a user."""
        with self._uow:
            return self._uow.categories.get_by_user(user_id)

    def get_category_tree(self, user_id: UserId) -> dict:
        """Get categories organized as a tree structure.

        Returns dict with 'root' categories and 'children' mapping.
        """
        with self._uow:
            all_categories = self._uow.categories.get_by_user(user_id)

            # Organize into tree
            root_categories = []
            children_by_parent: dict[str, list[Category]] = {}

            for cat in all_categories:
                if cat.parent_id is None:
                    root_categories.append(cat)
                else:
                    parent_key = str(cat.parent_id)
                    if parent_key not in children_by_parent:
                        children_by_parent[parent_key] = []
                    children_by_parent[parent_key].append(cat)

            return {
                "root": root_categories,
                "children": children_by_parent,
            }

    async def update_category_name(
        self,
        user_id: UserId,
        category_id: CategoryId,
        new_name: str,
    ) -> Category | CategoryError:
        """Update category name."""
        with self._uow:
            category = self._uow.categories.get(category_id)
            if category is None:
                return CategoryError("NOT_FOUND", "Category not found")
            if category.user_id != user_id:
                return CategoryError("NOT_OWNED", "Category does not belong to user")

            try:
                category.update_name(new_name)
            except ValueError as e:
                return CategoryError("VALIDATION_ERROR", str(e))

            self._uow.collect_events(category.events)
            category.clear_events()
            await self._uow.commit()

            return category

    async def update_category_parent(
        self,
        user_id: UserId,
        category_id: CategoryId,
        new_parent_id: CategoryId | None,
    ) -> Category | CategoryError:
        """Move category to a new parent (or make top-level)."""
        with self._uow:
            category = self._uow.categories.get(category_id)
            if category is None:
                return CategoryError("NOT_FOUND", "Category not found")
            if category.user_id != user_id:
                return CategoryError("NOT_OWNED", "Category does not belong to user")

            # Validate new parent
            if new_parent_id:
                new_parent = self._uow.categories.get(new_parent_id)
                if new_parent is None:
                    return CategoryError("PARENT_NOT_FOUND", "New parent category not found")
                if new_parent.user_id != user_id:
                    return CategoryError(
                        "PARENT_NOT_OWNED", "New parent does not belong to user"
                    )
                # Check for circular reference
                if new_parent_id == category_id:
                    return CategoryError(
                        "CIRCULAR_REFERENCE", "Category cannot be its own parent"
                    )
                # TODO: Check deeper circular references if unlimited depth

            try:
                category.update_parent(new_parent_id)
            except ValueError as e:
                return CategoryError("VALIDATION_ERROR", str(e))

            self._uow.collect_events(category.events)
            category.clear_events()
            await self._uow.commit()

            return category

    async def delete_category(
        self,
        user_id: UserId,
        category_id: CategoryId,
        reassign_to: CategoryId | None = None,
        household_id: HouseholdId | None = None,
    ) -> bool | CategoryError:
        """Delete a category.

        Args:
            user_id: User making the request
            category_id: Category to delete
            reassign_to: Category to reassign transactions to (defaults to Uncategorized)

        Returns:
            True if deleted, or CategoryError
        """
        with self._uow:
            category = self._uow.categories.get(category_id)
            if category is None:
                return CategoryError("NOT_FOUND", "Category not found")
            if category.user_id != user_id:
                return CategoryError("NOT_OWNED", "Category does not belong to user")
            if category.is_system:
                return CategoryError("CANNOT_DELETE_SYSTEM", "Cannot delete system category")

            # Check for child categories
            children = self._uow.categories.get_children(category_id)
            if children:
                return CategoryError(
                    "HAS_CHILDREN", "Cannot delete category with subcategories"
                )

            # Get or create Uncategorized for reassignment
            if reassign_to is None:
                uncategorized = self._uow.categories.get_or_create_uncategorized(
                    user_id, household_id=household_id
                )
                reassign_to = uncategorized.id

            # TODO: Reassign transactions (will be added when transaction filter by category works)
            # For now, just check if there are transactions
            txn_count = self._uow.categories.count_transactions(category_id)
            if txn_count > 0:
                return CategoryError(
                    "HAS_TRANSACTIONS",
                    f"Category has {txn_count} transaction(s). Reassign them first.",
                )

            category.delete()
            self._uow.collect_events(category.events)
            self._uow.categories.delete(category_id)
            await self._uow.commit()

            return True
