"""Category entity for transaction categorization.

CONTEXT DECISIONS:
1. Hierarchical structure (parent/child categories)
2. Transactions can be assigned to any level (parent or leaf)
3. System category "Uncategorized" always exists, cannot be modified/deleted
4. Two-level hierarchy (parent categories and child categories)
5. CategoryType (income/expense) for default transaction direction
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum, auto
from typing import Self

from src.domain.events.base import DomainEvent
from src.domain.events.transaction_events import (
    CategoryCreated,
    CategoryDeleted,
    CategoryUpdated,
)
from src.domain.model.entity_id import CategoryId, HouseholdId, UserId

# System category names that cannot be modified
SYSTEM_CATEGORY_UNCATEGORIZED = "Uncategorized"


class CategoryType(StrEnum):
    """Category type for default transaction direction.

    INCOME: Categories for money coming in (salary, interest, etc.)
    EXPENSE: Categories for money going out (food, utilities, etc.)
    """

    INCOME = auto()
    EXPENSE = auto()


@dataclass(eq=False)
class Category:
    """Category entity for organizing transactions.

    Supports two-level hierarchy: parent categories and child categories.
    System categories (is_system=True) cannot be modified or deleted.
    """

    id: CategoryId
    user_id: UserId
    household_id: HouseholdId
    name: str

    # Hierarchy - parent_id is None for top-level categories
    parent_id: CategoryId | None = None

    # Category metadata
    category_type: CategoryType = CategoryType.EXPENSE  # Income or expense
    is_system: bool = False  # System categories are protected
    is_hidden: bool = False  # Hide from normal views
    sort_order: int = 0
    icon: str | None = None  # Emoji or icon name

    # Audit
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    # Domain events
    _events: list[DomainEvent] = field(default_factory=list, repr=False)

    @property
    def events(self) -> list[DomainEvent]:
        return list(self._events)

    def clear_events(self) -> None:
        self._events.clear()

    @property
    def is_top_level(self) -> bool:
        """Check if this is a top-level (parent) category."""
        return self.parent_id is None

    # --- Factory Methods ---

    @classmethod
    def create(
        cls,
        user_id: UserId,
        name: str,
        parent_id: CategoryId | None = None,
        icon: str | None = None,
        sort_order: int = 0,
        category_type: CategoryType = CategoryType.EXPENSE,
        household_id: HouseholdId | None = None,
    ) -> Self:
        """Create a new user category."""
        if not name or not name.strip():
            raise ValueError("Category name cannot be empty")

        category = cls(
            id=CategoryId.generate(),
            user_id=user_id,
            household_id=household_id
            or HouseholdId.from_string("hh_00000000000000000000000000"),
            name=name.strip(),
            parent_id=parent_id,
            category_type=category_type,
            is_system=False,
            icon=icon,
            sort_order=sort_order,
        )

        category._events.append(
            CategoryCreated(
                aggregate_id=str(category.id),
                aggregate_type="Category",
                category_name=name,
                parent_id=str(parent_id) if parent_id else None,
                is_system=False,
            )
        )
        return category

    @classmethod
    def create_system_category(
        cls,
        user_id: UserId,
        name: str,
        category_type: CategoryType = CategoryType.EXPENSE,
        household_id: HouseholdId | None = None,
    ) -> Self:
        """Create a system category (protected, cannot be modified).

        Used for "Uncategorized" and potentially "Transfer" meta-category.
        """
        category = cls(
            id=CategoryId.generate(),
            user_id=user_id,
            household_id=household_id
            or HouseholdId.from_string("hh_00000000000000000000000000"),
            name=name,
            parent_id=None,  # System categories are always top-level
            category_type=category_type,
            is_system=True,
            is_hidden=False,
            sort_order=-1,  # Sort first
        )

        category._events.append(
            CategoryCreated(
                aggregate_id=str(category.id),
                aggregate_type="Category",
                category_name=name,
                parent_id=None,
                is_system=True,
            )
        )
        return category

    # --- Mutation Methods ---

    def update_name(self, new_name: str) -> None:
        """Update category name."""
        if self.is_system:
            raise ValueError("Cannot modify system category")
        if not new_name or not new_name.strip():
            raise ValueError("Category name cannot be empty")

        old_name = self.name
        self.name = new_name.strip()
        self.updated_at = datetime.now(UTC)

        self._events.append(
            CategoryUpdated(
                aggregate_id=str(self.id),
                aggregate_type="Category",
                field="name",
                old_value=old_name,
                new_value=self.name,
            )
        )

    def update_parent(self, new_parent_id: CategoryId | None) -> None:
        """Move category to different parent (or make top-level)."""
        if self.is_system:
            raise ValueError("Cannot modify system category")
        # Prevent setting self as parent (would create cycle)
        if new_parent_id == self.id:
            raise ValueError("Category cannot be its own parent")

        old_parent = str(self.parent_id) if self.parent_id else None
        self.parent_id = new_parent_id
        self.updated_at = datetime.now(UTC)

        self._events.append(
            CategoryUpdated(
                aggregate_id=str(self.id),
                aggregate_type="Category",
                field="parent_id",
                old_value=old_parent,
                new_value=str(new_parent_id) if new_parent_id else None,
            )
        )

    def update_icon(self, icon: str | None) -> None:
        """Update category icon."""
        if self.is_system:
            raise ValueError("Cannot modify system category")

        old_icon = self.icon
        self.icon = icon
        self.updated_at = datetime.now(UTC)

        self._events.append(
            CategoryUpdated(
                aggregate_id=str(self.id),
                aggregate_type="Category",
                field="icon",
                old_value=old_icon,
                new_value=icon,
            )
        )

    def update_sort_order(self, sort_order: int) -> None:
        """Update category sort order."""
        old_order = self.sort_order
        self.sort_order = sort_order
        self.updated_at = datetime.now(UTC)

        self._events.append(
            CategoryUpdated(
                aggregate_id=str(self.id),
                aggregate_type="Category",
                field="sort_order",
                old_value=str(old_order),
                new_value=str(sort_order),
            )
        )

    def hide(self) -> None:
        """Hide category from normal views."""
        if self.is_system:
            raise ValueError("Cannot hide system category")
        self.is_hidden = True
        self.updated_at = datetime.now(UTC)

    def unhide(self) -> None:
        """Show category in normal views."""
        self.is_hidden = False
        self.updated_at = datetime.now(UTC)

    def delete(self) -> None:
        """Mark category for deletion (emits event).

        System categories cannot be deleted.
        Caller must handle reassignment of transactions using this category.
        """
        if self.is_system:
            raise ValueError("Cannot delete system category")

        self._events.append(
            CategoryDeleted(
                aggregate_id=str(self.id),
                aggregate_type="Category",
            )
        )
