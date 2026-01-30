"""Money value object with precision arithmetic.

Money is an immutable value object that handles monetary amounts with proper
decimal precision. It supports basic arithmetic operations while ensuring
currency consistency.

Key design decisions:
- Uses Python's Decimal for precision (never floats)
- 4 decimal places for precision (handles exchange rate calculations)
- Immutable via frozen dataclass
- Rejects operations between different currencies
- Always initialize Decimal from string to avoid float precision issues
"""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Self


@dataclass(frozen=True, slots=True)
class Money:
    """Immutable value object for monetary amounts with precision arithmetic.

    Args:
        amount: The monetary amount as Decimal. Initialize from string for precision.
        currency: ISO 4217 3-letter currency code (default: USD).

    Examples:
        >>> m = Money(Decimal("100.50"), "USD")
        >>> m2 = Money(Decimal("25.25"), "USD")
        >>> total = m + m2
        >>> total.amount
        Decimal('125.7500')
    """

    amount: Decimal
    currency: str = "USD"

    def __post_init__(self) -> None:
        """Normalize amount to 4 decimal places and validate currency."""
        # Normalize to 4 decimal places for consistent precision
        # Use object.__setattr__ because frozen=True blocks normal assignment
        normalized = Decimal(str(self.amount)).quantize(
            Decimal("0.0001"), rounding=ROUND_HALF_UP
        )
        object.__setattr__(self, "amount", normalized)

        # Validate currency is 3-letter ISO code
        if len(self.currency) != 3 or not self.currency.isalpha():
            raise ValueError(
                f"Currency must be 3-letter ISO code, got: {self.currency}"
            )

        # Normalize currency to uppercase
        object.__setattr__(self, "currency", self.currency.upper())

    def _check_same_currency(self, other: Self) -> None:
        """Raise ValueError if currencies don't match."""
        if self.currency != other.currency:
            raise ValueError(
                f"Cannot perform operation between {self.currency} and {other.currency}"
            )

    def __add__(self, other: Self) -> Self:
        """Add two Money of same currency.

        Args:
            other: Another Money instance with same currency.

        Returns:
            New Money with sum of amounts.

        Raises:
            ValueError: If currencies don't match.
        """
        self._check_same_currency(other)
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: Self) -> Self:
        """Subtract other from self (same currency).

        Args:
            other: Another Money instance with same currency.

        Returns:
            New Money with difference of amounts.

        Raises:
            ValueError: If currencies don't match.
        """
        self._check_same_currency(other)
        return Money(self.amount - other.amount, self.currency)

    def __mul__(self, factor: Decimal | int) -> Self:
        """Multiply by a factor (for percentage calculations, etc.).

        Args:
            factor: Decimal or int multiplier.

        Returns:
            New Money with multiplied amount.
        """
        return Money(self.amount * Decimal(str(factor)), self.currency)

    def __rmul__(self, factor: Decimal | int) -> Self:
        """Support factor * money syntax."""
        return self.__mul__(factor)

    def __neg__(self) -> Self:
        """Negate the amount.

        Returns:
            New Money with negated amount.
        """
        return Money(-self.amount, self.currency)

    def __lt__(self, other: Self) -> bool:
        """Compare if self is less than other (same currency only).

        Raises:
            ValueError: If currencies don't match.
        """
        self._check_same_currency(other)
        return self.amount < other.amount

    def __le__(self, other: Self) -> bool:
        """Compare if self is less than or equal to other (same currency only).

        Raises:
            ValueError: If currencies don't match.
        """
        self._check_same_currency(other)
        return self.amount <= other.amount

    def __gt__(self, other: Self) -> bool:
        """Compare if self is greater than other (same currency only).

        Raises:
            ValueError: If currencies don't match.
        """
        self._check_same_currency(other)
        return self.amount > other.amount

    def __ge__(self, other: Self) -> bool:
        """Compare if self is greater than or equal to other (same currency only).

        Raises:
            ValueError: If currencies don't match.
        """
        self._check_same_currency(other)
        return self.amount >= other.amount

    def is_positive(self) -> bool:
        """Check if amount is positive (greater than zero)."""
        return self.amount > 0

    def is_negative(self) -> bool:
        """Check if amount is negative (less than zero)."""
        return self.amount < 0

    def is_zero(self) -> bool:
        """Check if amount is zero."""
        return self.amount == 0

    def abs(self) -> Self:
        """Return absolute value.

        Returns:
            New Money with absolute amount.
        """
        return Money(abs(self.amount), self.currency)
