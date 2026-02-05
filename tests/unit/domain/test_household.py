"""Tests for Household domain model."""

import pytest


class TestHouseholdId:
    """Tests for HouseholdId TypeID."""

    def test_generate_creates_valid_id(self) -> None:
        """Generated HouseholdId has 'hh_' prefix."""
        from src.domain.model.entity_id import HouseholdId

        hh_id = HouseholdId.generate()

        assert str(hh_id).startswith("hh_")
        assert len(str(hh_id)) > 10  # TypeID format

    def test_from_string_parses_valid_id(self) -> None:
        """HouseholdId can be parsed from valid string."""
        from src.domain.model.entity_id import HouseholdId

        original = HouseholdId.generate()
        parsed = HouseholdId.from_string(str(original))

        assert str(parsed) == str(original)

    def test_from_string_rejects_wrong_prefix(self) -> None:
        """HouseholdId rejects non-hh prefixes."""
        from src.domain.model.entity_id import HouseholdId

        with pytest.raises(ValueError, match="hh"):
            HouseholdId.from_string("user_01h455vb4pex5vsknk084sn02q")

    def test_prefix_property_returns_hh(self) -> None:
        """HouseholdId.prefix returns 'hh'."""
        from src.domain.model.entity_id import HouseholdId

        hh_id = HouseholdId.generate()

        assert hh_id.prefix == "hh"


class TestHousehold:
    """Tests for Household aggregate root."""

    def test_create_generates_id(self) -> None:
        """Household.create() generates a new HouseholdId."""
        from src.domain.model.entity_id import UserId
        from src.domain.model.household import Household

        owner_id = UserId.generate()
        household = Household.create(name="Smith Family", owner_id=owner_id)

        assert household.id is not None
        assert str(household.id).startswith("hh_")

    def test_create_stores_name_and_owner(self) -> None:
        """Household.create() stores name and owner_id."""
        from src.domain.model.entity_id import UserId
        from src.domain.model.household import Household

        owner_id = UserId.generate()
        household = Household.create(name="Test Household", owner_id=owner_id)

        assert household.name == "Test Household"
        assert household.owner_id == owner_id

    def test_create_sets_timestamps(self) -> None:
        """Household.create() sets created_at and updated_at."""
        from src.domain.model.entity_id import UserId
        from src.domain.model.household import Household

        owner_id = UserId.generate()
        household = Household.create(name="Test", owner_id=owner_id)

        assert household.created_at is not None
        assert household.updated_at is not None
        assert household.created_at == household.updated_at

    def test_update_name_changes_name_and_updated_at(self) -> None:
        """update_name() changes name and updates timestamp."""
        from src.domain.model.entity_id import UserId
        from src.domain.model.household import Household
        import time

        owner_id = UserId.generate()
        household = Household.create(name="Old Name", owner_id=owner_id)
        old_updated = household.updated_at

        time.sleep(0.01)  # Ensure timestamp changes
        household.update_name("New Name")

        assert household.name == "New Name"
        assert household.updated_at > old_updated
