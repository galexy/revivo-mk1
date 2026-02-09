"""Unit tests for Category entity.

Tests cover:
- Factory methods (create, create_system_category)
- Update methods (name, parent, icon, sort_order)
- Delete operation
- System category protection
- Event emission on state changes
- Hierarchy properties
"""

from datetime import UTC, datetime

import pytest

from domain.events.transaction_events import (
    CategoryCreated,
    CategoryDeleted,
    CategoryUpdated,
)
from domain.model.category import SYSTEM_CATEGORY_UNCATEGORIZED, Category, CategoryType
from domain.model.entity_id import CategoryId, HouseholdId, UserId

# --- Fixtures ---


@pytest.fixture
def user_id() -> UserId:
    """Generate test UserId."""
    return UserId.generate()


@pytest.fixture
def parent_category_id() -> CategoryId:
    """Generate test parent CategoryId."""
    return CategoryId.generate()


# --- TestCategoryCreate ---


class TestCategoryCreate:
    """Test Category.create() factory method."""

    def test_create_with_required_fields(self, user_id: UserId):
        """Creates category with required fields and default values."""
        category = Category.create(
            user_id=user_id,
            name="Groceries",
        )

        assert category.id is not None
        assert str(category.id).startswith("cat_")
        assert category.user_id == user_id
        assert category.name == "Groceries"
        assert category.parent_id is None  # Top-level by default
        assert category.category_type == CategoryType.EXPENSE  # Default
        assert category.is_system is False
        assert category.is_hidden is False
        assert category.sort_order == 0

    def test_create_generates_unique_category_id(self, user_id: UserId):
        """Each create generates a unique CategoryId."""
        cat1 = Category.create(user_id=user_id, name="Category 1")
        cat2 = Category.create(user_id=user_id, name="Category 2")

        assert cat1.id != cat2.id

    def test_create_sets_timestamps(self, user_id: UserId):
        """Sets created_at and updated_at timestamps."""
        before = datetime.now(UTC)
        category = Category.create(user_id=user_id, name="Test")
        after = datetime.now(UTC)

        assert before <= category.created_at <= after
        assert before <= category.updated_at <= after

    def test_create_emits_category_created_event(self, user_id: UserId):
        """Emits CategoryCreated event."""
        category = Category.create(user_id=user_id, name="Groceries")

        assert len(category.events) == 1
        event = category.events[0]
        assert isinstance(event, CategoryCreated)
        assert event.aggregate_id == str(category.id)
        assert event.aggregate_type == "Category"
        assert event.category_name == "Groceries"
        assert event.parent_id is None
        assert event.is_system is False

    def test_create_with_optional_fields(
        self, user_id: UserId, parent_category_id: CategoryId
    ):
        """Creates category with optional parent, icon, category_type."""
        category = Category.create(
            user_id=user_id,
            name="Restaurants",
            parent_id=parent_category_id,
            icon="🍽️",
            sort_order=10,
            category_type=CategoryType.EXPENSE,
        )

        assert category.parent_id == parent_category_id
        assert category.icon == "🍽️"
        assert category.sort_order == 10
        assert category.category_type == CategoryType.EXPENSE

    def test_create_income_category(self, user_id: UserId):
        """Can create income category."""
        category = Category.create(
            user_id=user_id,
            name="Salary",
            category_type=CategoryType.INCOME,
        )

        assert category.category_type == CategoryType.INCOME

    def test_create_uses_default_household_id(self, user_id: UserId):
        """Uses default household ID when not provided."""
        category = Category.create(user_id=user_id, name="Test")

        assert category.household_id == HouseholdId.from_string(
            "hh_00000000000000000000000000"
        )

    def test_create_strips_whitespace_from_name(self, user_id: UserId):
        """Strips whitespace from category name."""
        category = Category.create(user_id=user_id, name="  Groceries  ")

        assert category.name == "Groceries"

    def test_create_rejects_empty_name(self, user_id: UserId):
        """Raises ValueError for empty name."""
        with pytest.raises(ValueError, match="name cannot be empty"):
            Category.create(user_id=user_id, name="")

    def test_create_rejects_whitespace_only_name(self, user_id: UserId):
        """Raises ValueError for whitespace-only name."""
        with pytest.raises(ValueError, match="name cannot be empty"):
            Category.create(user_id=user_id, name="   ")


# --- TestCategoryCreateSystem ---


class TestCategoryCreateSystem:
    """Test Category.create_system_category() factory method."""

    def test_create_system_category(self, user_id: UserId):
        """Creates system category with is_system=True."""
        category = Category.create_system_category(
            user_id=user_id,
            name=SYSTEM_CATEGORY_UNCATEGORIZED,
        )

        assert category.is_system is True
        assert category.name == SYSTEM_CATEGORY_UNCATEGORIZED
        assert category.parent_id is None  # Always top-level
        assert category.sort_order == -1  # Sort first

    def test_create_system_category_emits_event(self, user_id: UserId):
        """System category emits CategoryCreated with is_system=True."""
        category = Category.create_system_category(
            user_id=user_id,
            name=SYSTEM_CATEGORY_UNCATEGORIZED,
        )

        assert len(category.events) == 1
        event = category.events[0]
        assert isinstance(event, CategoryCreated)
        assert event.is_system is True
        assert event.parent_id is None


# --- TestCategoryUpdate ---


class TestCategoryUpdate:
    """Test category update methods."""

    def test_update_name(self, user_id: UserId):
        """update_name() changes name and emits event."""
        category = Category.create(user_id=user_id, name="Old Name")
        category.clear_events()

        category.update_name("New Name")

        assert category.name == "New Name"
        assert len(category.events) == 1
        event = category.events[0]
        assert isinstance(event, CategoryUpdated)
        assert event.field == "name"
        assert event.old_value == "Old Name"
        assert event.new_value == "New Name"

    def test_update_name_strips_whitespace(self, user_id: UserId):
        """update_name() strips whitespace."""
        category = Category.create(user_id=user_id, name="Old")
        category.clear_events()

        category.update_name("  New  ")

        assert category.name == "New"

    def test_update_name_rejects_empty(self, user_id: UserId):
        """Raises ValueError for empty name."""
        category = Category.create(user_id=user_id, name="Test")

        with pytest.raises(ValueError, match="name cannot be empty"):
            category.update_name("")

    def test_update_name_rejects_whitespace_only(self, user_id: UserId):
        """Raises ValueError for whitespace-only name."""
        category = Category.create(user_id=user_id, name="Test")

        with pytest.raises(ValueError, match="name cannot be empty"):
            category.update_name("   ")

    def test_update_name_on_system_category_raises_error(self, user_id: UserId):
        """Raises ValueError when updating system category name."""
        category = Category.create_system_category(
            user_id=user_id,
            name=SYSTEM_CATEGORY_UNCATEGORIZED,
        )

        with pytest.raises(ValueError, match="Cannot modify system category"):
            category.update_name("New Name")

    def test_update_parent(self, user_id: UserId, parent_category_id: CategoryId):
        """update_parent() changes parent_id and emits event."""
        category = Category.create(user_id=user_id, name="Child")
        category.clear_events()

        category.update_parent(parent_category_id)

        assert category.parent_id == parent_category_id
        assert len(category.events) == 1
        event = category.events[0]
        assert isinstance(event, CategoryUpdated)
        assert event.field == "parent_id"
        assert event.new_value == str(parent_category_id)

    def test_update_parent_to_none_makes_top_level(self, user_id: UserId):
        """update_parent(None) makes category top-level."""
        parent_id = CategoryId.generate()
        category = Category.create(user_id=user_id, name="Child", parent_id=parent_id)
        category.clear_events()

        category.update_parent(None)

        assert category.parent_id is None
        assert category.is_top_level is True

    def test_update_parent_rejects_self_as_parent(self, user_id: UserId):
        """Raises ValueError when setting self as parent."""
        category = Category.create(user_id=user_id, name="Test")

        with pytest.raises(ValueError, match="cannot be its own parent"):
            category.update_parent(category.id)

    def test_update_parent_on_system_category_raises_error(self, user_id: UserId):
        """Raises ValueError when updating system category parent."""
        category = Category.create_system_category(
            user_id=user_id,
            name=SYSTEM_CATEGORY_UNCATEGORIZED,
        )

        with pytest.raises(ValueError, match="Cannot modify system category"):
            category.update_parent(CategoryId.generate())

    def test_update_icon(self, user_id: UserId):
        """update_icon() changes icon."""
        category = Category.create(user_id=user_id, name="Test")
        category.clear_events()

        category.update_icon("🎉")

        assert category.icon == "🎉"
        assert len(category.events) == 1

    def test_update_icon_on_system_category_raises_error(self, user_id: UserId):
        """Raises ValueError when updating system category icon."""
        category = Category.create_system_category(
            user_id=user_id,
            name=SYSTEM_CATEGORY_UNCATEGORIZED,
        )

        with pytest.raises(ValueError, match="Cannot modify system category"):
            category.update_icon("🎉")

    def test_update_sort_order(self, user_id: UserId):
        """update_sort_order() changes sort_order."""
        category = Category.create(user_id=user_id, name="Test")
        category.clear_events()

        category.update_sort_order(99)

        assert category.sort_order == 99
        assert len(category.events) == 1

    def test_hide(self, user_id: UserId):
        """hide() sets is_hidden to True."""
        category = Category.create(user_id=user_id, name="Test")

        category.hide()

        assert category.is_hidden is True

    def test_hide_on_system_category_raises_error(self, user_id: UserId):
        """Raises ValueError when hiding system category."""
        category = Category.create_system_category(
            user_id=user_id,
            name=SYSTEM_CATEGORY_UNCATEGORIZED,
        )

        with pytest.raises(ValueError, match="Cannot hide system category"):
            category.hide()

    def test_unhide(self, user_id: UserId):
        """unhide() sets is_hidden to False."""
        category = Category.create(user_id=user_id, name="Test")
        category.hide()

        category.unhide()

        assert category.is_hidden is False

    def test_mutation_updates_timestamp(self, user_id: UserId):
        """All mutation methods update updated_at timestamp."""
        category = Category.create(user_id=user_id, name="Test")
        original_updated_at = category.updated_at

        category.update_name("New Name")

        assert category.updated_at >= original_updated_at


# --- TestCategoryDelete ---


class TestCategoryDelete:
    """Test category delete operation."""

    def test_delete_emits_category_deleted_event(self, user_id: UserId):
        """delete() emits CategoryDeleted event."""
        category = Category.create(user_id=user_id, name="Test")
        category.clear_events()

        category.delete()

        assert len(category.events) == 1
        event = category.events[0]
        assert isinstance(event, CategoryDeleted)
        assert event.aggregate_id == str(category.id)

    def test_delete_on_system_category_raises_error(self, user_id: UserId):
        """Raises ValueError when deleting system category."""
        category = Category.create_system_category(
            user_id=user_id,
            name=SYSTEM_CATEGORY_UNCATEGORIZED,
        )

        with pytest.raises(ValueError, match="Cannot delete system category"):
            category.delete()


# --- TestCategoryEvents ---


class TestCategoryEvents:
    """Test event collection."""

    def test_events_property_returns_list(self, user_id: UserId):
        """events property returns list of domain events."""
        category = Category.create(user_id=user_id, name="Test")

        events = category.events
        assert len(events) == 1
        assert isinstance(events[0], CategoryCreated)

    def test_clear_events_empties_list(self, user_id: UserId):
        """clear_events() empties the events list."""
        category = Category.create(user_id=user_id, name="Test")

        assert len(category.events) == 1
        category.clear_events()
        assert len(category.events) == 0

    def test_multiple_mutations_accumulate_events(self, user_id: UserId):
        """Multiple mutations accumulate events."""
        category = Category.create(user_id=user_id, name="Test")
        category.clear_events()

        category.update_name("New Name")
        category.update_icon("🎉")

        assert len(category.events) == 2
        assert isinstance(category.events[0], CategoryUpdated)
        assert isinstance(category.events[1], CategoryUpdated)


# --- TestCategoryType ---


class TestCategoryType:
    """Test CategoryType enum."""

    def test_income_and_expense_values_exist(self):
        """INCOME and EXPENSE values exist."""
        assert CategoryType.INCOME.value == "income"
        assert CategoryType.EXPENSE.value == "expense"

    def test_str_enum_behavior(self):
        """CategoryType is StrEnum (supports string comparison)."""
        assert CategoryType.INCOME == "income"
        assert CategoryType.EXPENSE == "expense"


# --- TestCategoryHierarchy ---


class TestCategoryHierarchy:
    """Test category hierarchy properties."""

    def test_is_top_level_with_no_parent(self, user_id: UserId):
        """is_top_level is True when parent_id is None."""
        category = Category.create(user_id=user_id, name="Parent")

        assert category.is_top_level is True

    def test_is_top_level_with_parent(self, user_id: UserId):
        """is_top_level is False when parent_id is set."""
        parent_id = CategoryId.generate()
        category = Category.create(user_id=user_id, name="Child", parent_id=parent_id)

        assert category.is_top_level is False
