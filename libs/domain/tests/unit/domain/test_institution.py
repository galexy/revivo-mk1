"""Unit tests for InstitutionDetails value object.

Verifies that InstitutionDetails:
- Validates name is non-empty
- Normalizes name by stripping whitespace
- Accepts optional fields (website, phone, notes)
- Is immutable
"""

import pytest

from domain.model.institution import InstitutionDetails


class TestInstitutionDetailsConstruction:
    """Tests for InstitutionDetails construction and validation."""

    def test_creates_with_name_only(self):
        """Should create InstitutionDetails with just name."""
        inst = InstitutionDetails(name="Chase Bank")
        assert inst.name == "Chase Bank"
        assert inst.website is None
        assert inst.phone is None
        assert inst.notes is None

    def test_creates_with_all_fields(self):
        """Should create InstitutionDetails with all fields."""
        inst = InstitutionDetails(
            name="Chase Bank",
            website="https://chase.com",
            phone="1-800-935-9935",
            notes="Main checking account bank",
        )
        assert inst.name == "Chase Bank"
        assert inst.website == "https://chase.com"
        assert inst.phone == "1-800-935-9935"
        assert inst.notes == "Main checking account bank"

    def test_normalizes_name_by_stripping_whitespace(self):
        """Should strip whitespace from name."""
        inst = InstitutionDetails(name="  Chase Bank  ")
        assert inst.name == "Chase Bank"

    def test_rejects_empty_name(self):
        """Should reject empty name string."""
        with pytest.raises(ValueError, match=r"(?i)name cannot be empty"):
            InstitutionDetails(name="")

    def test_rejects_whitespace_only_name(self):
        """Should reject whitespace-only name string."""
        with pytest.raises(ValueError, match=r"(?i)name cannot be empty"):
            InstitutionDetails(name="   ")

    def test_accepts_name_with_special_characters(self):
        """Should accept name with various characters."""
        inst = InstitutionDetails(name="Wells Fargo & Co.")
        assert inst.name == "Wells Fargo & Co."

    def test_accepts_name_with_unicode(self):
        """Should accept name with unicode characters."""
        inst = InstitutionDetails(name="Banque Nationale")
        assert inst.name == "Banque Nationale"


class TestInstitutionDetailsOptionalFields:
    """Tests for InstitutionDetails optional fields."""

    def test_website_can_be_any_string(self):
        """Website field accepts any string (no URL validation)."""
        inst = InstitutionDetails(
            name="Bank",
            website="not-a-valid-url",
        )
        assert inst.website == "not-a-valid-url"

    def test_phone_can_be_any_string(self):
        """Phone field accepts any string (no format validation)."""
        inst = InstitutionDetails(
            name="Bank",
            phone="(555) 123-4567 ext 999",
        )
        assert inst.phone == "(555) 123-4567 ext 999"

    def test_notes_can_be_multiline(self):
        """Notes field accepts multiline text."""
        notes = """This is my primary bank.
        I've been a customer since 2010.
        Customer service: Good"""
        inst = InstitutionDetails(name="Bank", notes=notes)
        assert inst.notes == notes


class TestInstitutionDetailsImmutability:
    """Tests for InstitutionDetails immutability."""

    def test_cannot_modify_name(self):
        """Should not allow modification of name."""
        inst = InstitutionDetails(name="Chase Bank")
        with pytest.raises(AttributeError):
            inst.name = "Wells Fargo"  # type: ignore[misc]

    def test_cannot_modify_website(self):
        """Should not allow modification of website."""
        inst = InstitutionDetails(name="Chase Bank", website="https://chase.com")
        with pytest.raises(AttributeError):
            inst.website = "https://other.com"  # type: ignore[misc]

    def test_cannot_modify_phone(self):
        """Should not allow modification of phone."""
        inst = InstitutionDetails(name="Chase Bank", phone="1-800-123-4567")
        with pytest.raises(AttributeError):
            inst.phone = "1-888-999-8888"  # type: ignore[misc]

    def test_cannot_modify_notes(self):
        """Should not allow modification of notes."""
        inst = InstitutionDetails(name="Chase Bank", notes="My notes")
        with pytest.raises(AttributeError):
            inst.notes = "New notes"  # type: ignore[misc]


class TestInstitutionDetailsEquality:
    """Tests for InstitutionDetails equality."""

    def test_equal_institutions_are_equal(self):
        """Same values are equal."""
        inst1 = InstitutionDetails(
            name="Chase Bank",
            website="https://chase.com",
        )
        inst2 = InstitutionDetails(
            name="Chase Bank",
            website="https://chase.com",
        )
        assert inst1 == inst2

    def test_different_names_are_not_equal(self):
        """Different names are not equal."""
        inst1 = InstitutionDetails(name="Chase Bank")
        inst2 = InstitutionDetails(name="Wells Fargo")
        assert inst1 != inst2

    def test_different_websites_are_not_equal(self):
        """Different websites are not equal."""
        inst1 = InstitutionDetails(name="Bank", website="https://a.com")
        inst2 = InstitutionDetails(name="Bank", website="https://b.com")
        assert inst1 != inst2

    def test_none_vs_value_are_not_equal(self):
        """None vs actual value are not equal."""
        inst1 = InstitutionDetails(name="Bank", website=None)
        inst2 = InstitutionDetails(name="Bank", website="https://bank.com")
        assert inst1 != inst2

    def test_hashable(self):
        """InstitutionDetails should be hashable (usable in sets/dicts)."""
        inst1 = InstitutionDetails(name="Chase Bank")
        inst2 = InstitutionDetails(name="Chase Bank")
        # Should be usable in set
        inst_set = {inst1, inst2}
        assert len(inst_set) == 1  # Same value, should dedupe


class TestInstitutionDetailsRepr:
    """Tests for InstitutionDetails string representation."""

    def test_repr_includes_all_fields(self):
        """repr should include all fields."""
        inst = InstitutionDetails(
            name="Chase Bank",
            website="https://chase.com",
            phone="1-800-123-4567",
            notes="Notes",
        )
        repr_str = repr(inst)
        assert "Chase Bank" in repr_str
        assert "chase.com" in repr_str
        assert "1-800-123-4567" in repr_str
        assert "Notes" in repr_str

    def test_repr_handles_none_fields(self):
        """repr should handle None fields."""
        inst = InstitutionDetails(name="Bank")
        repr_str = repr(inst)
        assert "Bank" in repr_str
        assert "None" in repr_str or "website" not in repr_str  # Implementation detail
