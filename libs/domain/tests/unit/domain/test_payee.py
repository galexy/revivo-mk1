"""Unit tests for Payee entity.

Tests cover:
- Factory method (create)
- Update methods (name, default_category)
- Usage tracking (record_usage)
- Name normalization
"""

from datetime import UTC, datetime

import pytest

from domain.model.entity_id import CategoryId, HouseholdId, UserId
from domain.model.payee import Payee

# --- Fixtures ---


@pytest.fixture
def user_id() -> UserId:
    """Generate test UserId."""
    return UserId.generate()


@pytest.fixture
def category_id() -> CategoryId:
    """Generate test CategoryId."""
    return CategoryId.generate()


# --- TestPayeeCreate ---


class TestPayeeCreate:
    """Test Payee.create() factory method."""

    def test_create_with_required_fields(self, user_id: UserId):
        """Creates payee with required fields and default values."""
        payee = Payee.create(
            user_id=user_id,
            name="Starbucks",
        )

        assert payee.id is not None
        assert str(payee.id).startswith("payee_")
        assert payee.user_id == user_id
        assert payee.name == "Starbucks"
        assert payee.normalized_name == "starbucks"  # Lowercase
        assert payee.default_category_id is None
        assert payee.usage_count == 0
        assert payee.last_used_at is None

    def test_create_generates_unique_payee_id(self, user_id: UserId):
        """Each create generates a unique PayeeId."""
        payee1 = Payee.create(user_id=user_id, name="Payee 1")
        payee2 = Payee.create(user_id=user_id, name="Payee 2")

        assert payee1.id != payee2.id

    def test_create_sets_timestamps(self, user_id: UserId):
        """Sets created_at and updated_at timestamps."""
        before = datetime.now(UTC)
        payee = Payee.create(user_id=user_id, name="Test")
        after = datetime.now(UTC)

        assert before <= payee.created_at <= after
        assert before <= payee.updated_at <= after

    def test_create_with_default_category(
        self, user_id: UserId, category_id: CategoryId
    ):
        """Creates payee with default category."""
        payee = Payee.create(
            user_id=user_id,
            name="Starbucks",
            default_category_id=category_id,
        )

        assert payee.default_category_id == category_id

    def test_create_uses_default_household_id(self, user_id: UserId):
        """Uses default household ID when not provided."""
        payee = Payee.create(user_id=user_id, name="Test")

        assert payee.household_id == HouseholdId.from_string(
            "hh_00000000000000000000000000"
        )

    def test_create_strips_whitespace_from_name(self, user_id: UserId):
        """Strips whitespace from payee name."""
        payee = Payee.create(user_id=user_id, name="  Starbucks  ")

        assert payee.name == "Starbucks"
        assert payee.normalized_name == "starbucks"

    def test_create_rejects_empty_name(self, user_id: UserId):
        """Raises ValueError for empty name."""
        with pytest.raises(ValueError, match="name cannot be empty"):
            Payee.create(user_id=user_id, name="")

    def test_create_rejects_whitespace_only_name(self, user_id: UserId):
        """Raises ValueError for whitespace-only name."""
        with pytest.raises(ValueError, match="name cannot be empty"):
            Payee.create(user_id=user_id, name="   ")


# --- TestPayeeUpdate ---


class TestPayeeUpdate:
    """Test payee update methods."""

    def test_update_name(self, user_id: UserId):
        """update_name() changes name and normalized_name."""
        payee = Payee.create(user_id=user_id, name="Old Name")

        payee.update_name("New Name")

        assert payee.name == "New Name"
        assert payee.normalized_name == "new name"

    def test_update_name_strips_whitespace(self, user_id: UserId):
        """update_name() strips whitespace."""
        payee = Payee.create(user_id=user_id, name="Old")

        payee.update_name("  New  ")

        assert payee.name == "New"
        assert payee.normalized_name == "new"

    def test_update_name_rejects_empty(self, user_id: UserId):
        """Raises ValueError for empty name."""
        payee = Payee.create(user_id=user_id, name="Test")

        with pytest.raises(ValueError, match="name cannot be empty"):
            payee.update_name("")

    def test_update_name_rejects_whitespace_only(self, user_id: UserId):
        """Raises ValueError for whitespace-only name."""
        payee = Payee.create(user_id=user_id, name="Test")

        with pytest.raises(ValueError, match="name cannot be empty"):
            payee.update_name("   ")

    def test_update_name_updates_timestamp(self, user_id: UserId):
        """update_name() updates updated_at timestamp."""
        payee = Payee.create(user_id=user_id, name="Old")
        original_updated_at = payee.updated_at

        payee.update_name("New")

        assert payee.updated_at >= original_updated_at

    def test_set_default_category(self, user_id: UserId, category_id: CategoryId):
        """set_default_category() changes default_category_id."""
        payee = Payee.create(user_id=user_id, name="Test")

        payee.set_default_category(category_id)

        assert payee.default_category_id == category_id

    def test_set_default_category_to_none_clears_it(
        self, user_id: UserId, category_id: CategoryId
    ):
        """set_default_category(None) clears default category."""
        payee = Payee.create(
            user_id=user_id,
            name="Test",
            default_category_id=category_id,
        )

        payee.set_default_category(None)

        assert payee.default_category_id is None

    def test_set_default_category_updates_timestamp(self, user_id: UserId):
        """set_default_category() updates updated_at timestamp."""
        payee = Payee.create(user_id=user_id, name="Test")
        original_updated_at = payee.updated_at

        payee.set_default_category(CategoryId.generate())

        assert payee.updated_at >= original_updated_at

    def test_record_usage_increments_count(self, user_id: UserId):
        """record_usage() increments usage_count."""
        payee = Payee.create(user_id=user_id, name="Test")

        assert payee.usage_count == 0

        payee.record_usage()
        assert payee.usage_count == 1

        payee.record_usage()
        assert payee.usage_count == 2

    def test_record_usage_sets_last_used_at(self, user_id: UserId):
        """record_usage() sets last_used_at timestamp."""
        payee = Payee.create(user_id=user_id, name="Test")

        assert payee.last_used_at is None

        before = datetime.now(UTC)
        payee.record_usage()
        after = datetime.now(UTC)

        assert payee.last_used_at is not None
        assert before <= payee.last_used_at <= after

    def test_record_usage_updates_timestamp(self, user_id: UserId):
        """record_usage() updates updated_at timestamp."""
        payee = Payee.create(user_id=user_id, name="Test")
        original_updated_at = payee.updated_at

        payee.record_usage()

        assert payee.updated_at >= original_updated_at


# --- TestPayeeNormalization ---


class TestPayeeNormalization:
    """Test payee name normalization."""

    def test_normalized_name_is_lowercase(self, user_id: UserId):
        """normalized_name converts to lowercase."""
        payee = Payee.create(user_id=user_id, name="STARBUCKS Coffee")

        assert payee.normalized_name == "starbucks coffee"

    def test_normalized_name_preserves_spaces(self, user_id: UserId):
        """normalized_name preserves whitespace structure."""
        payee = Payee.create(user_id=user_id, name="Whole Foods Market")

        assert payee.normalized_name == "whole foods market"

    def test_update_name_updates_normalized_name(self, user_id: UserId):
        """update_name() updates both name and normalized_name."""
        payee = Payee.create(user_id=user_id, name="Old")

        payee.update_name("NEW NAME")

        assert payee.name == "NEW NAME"
        assert payee.normalized_name == "new name"
