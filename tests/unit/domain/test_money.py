"""Property-based tests for Money value object.

Uses hypothesis to verify Money arithmetic properties:
- Commutative: m1 + m2 == m2 + m1
- Associative: (m1 + m2) + m3 == m1 + (m2 + m3)
- Identity: m + Money(0) == m
- Inverse: m + (-m) == Money(0)
- Precision: No floating-point errors after operations
"""

from decimal import Decimal

import pytest
from hypothesis import given, strategies as st

from src.domain.model.money import Money

# Strategy for valid decimal amounts with 4 decimal places
money_amounts = st.decimals(
    min_value=Decimal("-1000000"),
    max_value=Decimal("1000000"),
    places=4,
    allow_nan=False,
    allow_infinity=False,
)


class TestMoneyProperties:
    """Property-based tests verifying Money arithmetic laws."""

    @given(a=money_amounts, b=money_amounts)
    def test_addition_is_commutative(self, a: Decimal, b: Decimal):
        """m1 + m2 == m2 + m1"""
        m1 = Money(a, "USD")
        m2 = Money(b, "USD")
        assert m1 + m2 == m2 + m1

    @given(a=money_amounts, b=money_amounts, c=money_amounts)
    def test_addition_is_associative(self, a: Decimal, b: Decimal, c: Decimal):
        """(m1 + m2) + m3 == m1 + (m2 + m3)"""
        m1 = Money(a, "USD")
        m2 = Money(b, "USD")
        m3 = Money(c, "USD")
        assert (m1 + m2) + m3 == m1 + (m2 + m3)

    @given(amount=money_amounts)
    def test_zero_is_additive_identity(self, amount: Decimal):
        """m + 0 == m"""
        m = Money(amount, "USD")
        zero = Money(Decimal("0"), "USD")
        assert m + zero == m
        assert zero + m == m

    @given(amount=money_amounts)
    def test_negation_gives_additive_inverse(self, amount: Decimal):
        """m + (-m) == 0"""
        m = Money(amount, "USD")
        zero = Money(Decimal("0"), "USD")
        assert m + (-m) == zero
        assert m - m == zero

    @given(amount=money_amounts)
    def test_subtraction_is_addition_of_negation(self, amount: Decimal):
        """m1 - m2 == m1 + (-m2)"""
        m1 = Money(amount, "USD")
        m2 = Money(Decimal("50"), "USD")
        assert m1 - m2 == m1 + (-m2)

    @given(amount=money_amounts, factor=st.integers(min_value=-1000, max_value=1000))
    def test_multiplication_by_integer(self, amount: Decimal, factor: int):
        """Money can be multiplied by integers."""
        m = Money(amount, "USD")
        result = m * factor
        assert result.currency == "USD"
        # Verify precision preserved
        expected = Money(amount * factor, "USD")
        assert result == expected

    @given(amount=money_amounts)
    def test_precision_preserved_through_operations(self, amount: Decimal):
        """Operations should not introduce floating-point errors."""
        m = Money(amount, "USD")
        # Double then halve should return original
        doubled = m + m
        halved = Money(doubled.amount / 2, "USD")
        assert m == halved


class TestMoneyValidation:
    """Tests for Money validation rules."""

    def test_rejects_different_currencies_on_add(self):
        """Cannot add USD to EUR."""
        usd = Money(Decimal("100"), "USD")
        eur = Money(Decimal("100"), "EUR")
        with pytest.raises(ValueError, match="currency"):
            _ = usd + eur

    def test_rejects_different_currencies_on_subtract(self):
        """Cannot subtract EUR from USD."""
        usd = Money(Decimal("100"), "USD")
        eur = Money(Decimal("100"), "EUR")
        with pytest.raises(ValueError, match="currency"):
            _ = usd - eur

    def test_rejects_invalid_currency_code_too_short(self):
        """Currency must be 3 letters."""
        with pytest.raises(ValueError, match="currency"):
            Money(Decimal("100"), "US")

    def test_rejects_invalid_currency_code_too_long(self):
        """Currency must be 3 letters."""
        with pytest.raises(ValueError, match="currency"):
            Money(Decimal("100"), "USDD")

    def test_rejects_currency_with_numbers(self):
        """Currency must be alphabetic."""
        with pytest.raises(ValueError, match="currency"):
            Money(Decimal("100"), "US1")

    def test_normalizes_precision_to_four_decimals(self):
        """Money should normalize to 4 decimal places."""
        m = Money(Decimal("100.123456789"), "USD")
        # Should be rounded to 4 places using ROUND_HALF_UP
        assert str(m.amount) == "100.1235"

    def test_normalizes_currency_to_uppercase(self):
        """Currency codes should be normalized to uppercase."""
        m = Money(Decimal("100"), "usd")
        assert m.currency == "USD"


class TestMoneyComparison:
    """Tests for Money comparison operations."""

    def test_equal_amounts_are_equal(self):
        """Same amount and currency are equal."""
        m1 = Money(Decimal("100.00"), "USD")
        m2 = Money(Decimal("100.00"), "USD")
        assert m1 == m2

    def test_different_amounts_are_not_equal(self):
        """Different amounts are not equal."""
        m1 = Money(Decimal("100.00"), "USD")
        m2 = Money(Decimal("100.01"), "USD")
        assert m1 != m2

    def test_different_currencies_are_not_equal(self):
        """Same amount but different currency are not equal."""
        m1 = Money(Decimal("100.00"), "USD")
        m2 = Money(Decimal("100.00"), "EUR")
        assert m1 != m2

    def test_less_than(self):
        """Less than comparison works for same currency."""
        m1 = Money(Decimal("50.00"), "USD")
        m2 = Money(Decimal("100.00"), "USD")
        assert m1 < m2
        assert not m2 < m1

    def test_less_than_or_equal(self):
        """Less than or equal comparison works."""
        m1 = Money(Decimal("50.00"), "USD")
        m2 = Money(Decimal("100.00"), "USD")
        m3 = Money(Decimal("100.00"), "USD")
        assert m1 <= m2
        assert m2 <= m3
        assert not m2 <= m1

    def test_greater_than(self):
        """Greater than comparison works for same currency."""
        m1 = Money(Decimal("100.00"), "USD")
        m2 = Money(Decimal("50.00"), "USD")
        assert m1 > m2
        assert not m2 > m1

    def test_greater_than_or_equal(self):
        """Greater than or equal comparison works."""
        m1 = Money(Decimal("100.00"), "USD")
        m2 = Money(Decimal("50.00"), "USD")
        m3 = Money(Decimal("100.00"), "USD")
        assert m1 >= m2
        assert m1 >= m3
        assert not m2 >= m1

    def test_comparison_requires_same_currency(self):
        """Cannot compare different currencies."""
        usd = Money(Decimal("100"), "USD")
        eur = Money(Decimal("50"), "EUR")
        with pytest.raises(ValueError):
            _ = usd < eur
        with pytest.raises(ValueError):
            _ = usd <= eur
        with pytest.raises(ValueError):
            _ = usd > eur
        with pytest.raises(ValueError):
            _ = usd >= eur


class TestMoneyHelpers:
    """Tests for Money helper methods."""

    def test_is_positive(self):
        """is_positive returns True only for positive amounts."""
        assert Money(Decimal("100"), "USD").is_positive()
        assert not Money(Decimal("-100"), "USD").is_positive()
        assert not Money(Decimal("0"), "USD").is_positive()

    def test_is_negative(self):
        """is_negative returns True only for negative amounts."""
        assert Money(Decimal("-100"), "USD").is_negative()
        assert not Money(Decimal("100"), "USD").is_negative()
        assert not Money(Decimal("0"), "USD").is_negative()

    def test_is_zero(self):
        """is_zero returns True only for zero amounts."""
        assert Money(Decimal("0"), "USD").is_zero()
        assert not Money(Decimal("100"), "USD").is_zero()
        assert not Money(Decimal("-100"), "USD").is_zero()

    def test_abs(self):
        """abs returns absolute value."""
        neg = Money(Decimal("-100.50"), "USD")
        pos = Money(Decimal("100.50"), "USD")
        assert neg.abs() == pos
        assert pos.abs() == pos


class TestMoneyArithmetic:
    """Additional arithmetic tests for edge cases."""

    def test_multiplication_by_decimal(self):
        """Money can be multiplied by Decimal for percentage."""
        m = Money(Decimal("100"), "USD")
        # 10% of $100
        result = m * Decimal("0.10")
        assert result == Money(Decimal("10"), "USD")

    def test_reverse_multiplication(self):
        """factor * money works same as money * factor."""
        m = Money(Decimal("100"), "USD")
        assert 2 * m == m * 2
        assert Decimal("0.5") * m == m * Decimal("0.5")

    def test_chained_operations(self):
        """Multiple operations can be chained."""
        m1 = Money(Decimal("100"), "USD")
        m2 = Money(Decimal("50"), "USD")
        m3 = Money(Decimal("25"), "USD")
        result = m1 + m2 - m3
        assert result == Money(Decimal("125"), "USD")

    def test_negation(self):
        """Negation creates money with opposite sign."""
        pos = Money(Decimal("100"), "USD")
        neg = -pos
        assert neg.amount == Decimal("-100.0000")
        assert neg.currency == "USD"
        # Double negation returns original
        assert -neg == pos
