"""Unit tests for RewardsBalance value object.

Verifies that RewardsBalance:
- Validates unit is non-empty
- Normalizes value to integer
- Supports arithmetic with same-unit validation
- Produces correct string representation
- Is immutable
"""

from decimal import Decimal

import pytest

from domain.model.rewards_balance import RewardsBalance


class TestRewardsBalanceConstruction:
    """Tests for RewardsBalance construction and validation."""

    def test_creates_with_valid_value_and_unit(self):
        """Should create RewardsBalance with valid inputs."""
        balance = RewardsBalance(Decimal("50000"), "Alaska Miles")
        assert balance.value == Decimal("50000")
        assert balance.unit == "Alaska Miles"

    def test_normalizes_value_to_integer(self):
        """Should normalize decimal values to integer."""
        balance = RewardsBalance(Decimal("50000.75"), "Chase Points")
        assert balance.value == Decimal("50001")  # Rounded up

        balance2 = RewardsBalance(Decimal("50000.25"), "Chase Points")
        assert balance2.value == Decimal("50000")  # Rounded down

    def test_normalizes_unit_by_stripping_whitespace(self):
        """Should strip whitespace from unit."""
        balance = RewardsBalance(Decimal("1000"), "  Alaska Miles  ")
        assert balance.unit == "Alaska Miles"

    def test_rejects_empty_unit(self):
        """Should reject empty unit string."""
        with pytest.raises(ValueError, match=r"(?i)unit cannot be empty"):
            RewardsBalance(Decimal("1000"), "")

    def test_rejects_whitespace_only_unit(self):
        """Should reject whitespace-only unit string."""
        with pytest.raises(ValueError, match=r"(?i)unit cannot be empty"):
            RewardsBalance(Decimal("1000"), "   ")

    def test_accepts_integer_value(self):
        """Should accept integer value and store as Decimal."""
        balance = RewardsBalance(Decimal(1000), "Points")
        assert balance.value == Decimal("1000")

    def test_accepts_string_decimal(self):
        """Should accept Decimal created from string."""
        balance = RewardsBalance(Decimal("75000"), "United Miles")
        assert balance.value == Decimal("75000")


class TestRewardsBalanceArithmetic:
    """Tests for RewardsBalance arithmetic operations."""

    def test_addition_same_unit(self):
        """Should add balances with same unit."""
        b1 = RewardsBalance(Decimal("50000"), "Alaska Miles")
        b2 = RewardsBalance(Decimal("25000"), "Alaska Miles")
        result = b1 + b2
        assert result.value == Decimal("75000")
        assert result.unit == "Alaska Miles"

    def test_addition_rejects_different_units(self):
        """Should reject addition of different units."""
        b1 = RewardsBalance(Decimal("50000"), "Alaska Miles")
        b2 = RewardsBalance(Decimal("25000"), "Chase Points")
        with pytest.raises(ValueError, match="Cannot perform operation"):
            _ = b1 + b2

    def test_subtraction_same_unit(self):
        """Should subtract balances with same unit."""
        b1 = RewardsBalance(Decimal("50000"), "Alaska Miles")
        b2 = RewardsBalance(Decimal("20000"), "Alaska Miles")
        result = b1 - b2
        assert result.value == Decimal("30000")
        assert result.unit == "Alaska Miles"

    def test_subtraction_rejects_different_units(self):
        """Should reject subtraction of different units."""
        b1 = RewardsBalance(Decimal("50000"), "Alaska Miles")
        b2 = RewardsBalance(Decimal("25000"), "Chase Points")
        with pytest.raises(ValueError, match="Cannot perform operation"):
            _ = b1 - b2

    def test_subtraction_can_go_negative(self):
        """Should allow negative results from subtraction."""
        b1 = RewardsBalance(Decimal("10000"), "Points")
        b2 = RewardsBalance(Decimal("15000"), "Points")
        result = b1 - b2
        assert result.value == Decimal("-5000")

    def test_chained_operations(self):
        """Should support chained arithmetic."""
        b1 = RewardsBalance(Decimal("50000"), "Points")
        b2 = RewardsBalance(Decimal("20000"), "Points")
        b3 = RewardsBalance(Decimal("5000"), "Points")
        result = b1 + b2 - b3
        assert result.value == Decimal("65000")


class TestRewardsBalanceStringRepresentation:
    """Tests for RewardsBalance string representation."""

    def test_str_formats_with_thousands_separator(self):
        """Should format value with thousands separator."""
        balance = RewardsBalance(Decimal("50000"), "Alaska Miles")
        assert str(balance) == "50,000 Alaska Miles"

    def test_str_large_value(self):
        """Should format large values correctly."""
        balance = RewardsBalance(Decimal("1234567"), "Points")
        assert str(balance) == "1,234,567 Points"

    def test_str_small_value(self):
        """Should format small values without separator."""
        balance = RewardsBalance(Decimal("100"), "Points")
        assert str(balance) == "100 Points"

    def test_str_zero_value(self):
        """Should format zero value."""
        balance = RewardsBalance(Decimal("0"), "Miles")
        assert str(balance) == "0 Miles"

    def test_str_negative_value(self):
        """Should format negative value."""
        balance = RewardsBalance(Decimal("-5000"), "Points")
        assert str(balance) == "-5,000 Points"


class TestRewardsBalanceHelpers:
    """Tests for RewardsBalance helper methods."""

    def test_is_positive(self):
        """is_positive returns True only for positive values."""
        assert RewardsBalance(Decimal("100"), "Points").is_positive()
        assert not RewardsBalance(Decimal("-100"), "Points").is_positive()
        assert not RewardsBalance(Decimal("0"), "Points").is_positive()

    def test_is_negative(self):
        """is_negative returns True only for negative values."""
        assert RewardsBalance(Decimal("-100"), "Points").is_negative()
        assert not RewardsBalance(Decimal("100"), "Points").is_negative()
        assert not RewardsBalance(Decimal("0"), "Points").is_negative()

    def test_is_zero(self):
        """is_zero returns True only for zero values."""
        assert RewardsBalance(Decimal("0"), "Points").is_zero()
        assert not RewardsBalance(Decimal("100"), "Points").is_zero()
        assert not RewardsBalance(Decimal("-100"), "Points").is_zero()


class TestRewardsBalanceArithmeticBehavior:
    """Tests for RewardsBalance arithmetic behavior."""

    def test_arithmetic_returns_new_instance(self):
        """Arithmetic should return new instance, not modify existing."""
        b1 = RewardsBalance(Decimal("50000"), "Points")
        b2 = RewardsBalance(Decimal("10000"), "Points")
        result = b1 + b2
        assert result is not b1
        assert result is not b2
        assert b1.value == Decimal("50000")  # Original unchanged
        assert b2.value == Decimal("10000")  # Original unchanged


class TestRewardsBalanceEquality:
    """Tests for RewardsBalance equality."""

    def test_equal_balances_are_equal(self):
        """Same value and unit are equal."""
        b1 = RewardsBalance(Decimal("50000"), "Points")
        b2 = RewardsBalance(Decimal("50000"), "Points")
        assert b1 == b2

    def test_different_values_are_not_equal(self):
        """Different values are not equal."""
        b1 = RewardsBalance(Decimal("50000"), "Points")
        b2 = RewardsBalance(Decimal("50001"), "Points")
        assert b1 != b2

    def test_different_units_are_not_equal(self):
        """Same value but different unit are not equal."""
        b1 = RewardsBalance(Decimal("50000"), "Points")
        b2 = RewardsBalance(Decimal("50000"), "Miles")
        assert b1 != b2

    def test_hashable(self):
        """RewardsBalance should be hashable (usable in sets/dicts)."""
        b1 = RewardsBalance(Decimal("50000"), "Points")
        b2 = RewardsBalance(Decimal("50000"), "Points")
        # Should be usable in set
        balance_set = {b1, b2}
        assert len(balance_set) == 1  # Same value, should dedupe
