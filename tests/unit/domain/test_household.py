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
