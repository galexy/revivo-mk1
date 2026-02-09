"""RewardsBalance value object for non-monetary balances.

Rewards accounts (airline miles, credit card points, etc.) track value
in non-monetary units. Unlike Money, rewards have a unit name
(e.g., "Alaska Miles", "Chase Points") and no currency.

Value is stored as Decimal for consistency with Money but normalized
to integer (no decimals for points/miles).
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Self


@dataclass(frozen=True, slots=True)
class RewardsBalance:
    """Value object for rewards/points/miles balances.

    Immutable value object that tracks reward points with their unit.
    Supports arithmetic operations between balances of the same unit.

    Args:
        value: The number of points/miles as Decimal.
        unit: The reward program name (e.g., "Alaska Miles", "Chase Points").

    Raises:
        ValueError: If unit is empty or whitespace.

    Examples:
        >>> miles = RewardsBalance(Decimal("50000"), "Alaska Miles")
        >>> more_miles = RewardsBalance(Decimal("10000"), "Alaska Miles")
        >>> total = miles + more_miles
        >>> str(total)
        '60,000 Alaska Miles'
    """

    value: Decimal
    unit: str

    def __post_init__(self) -> None:
        """Validate and normalize fields."""
        if not self.unit or not self.unit.strip():
            raise ValueError("Rewards unit cannot be empty")

        # Normalize to integer value (no decimals for points/miles)
        normalized_value = Decimal(str(self.value)).quantize(Decimal("1"))
        object.__setattr__(self, "value", normalized_value)

        # Normalize unit string
        object.__setattr__(self, "unit", self.unit.strip())

    def _check_same_unit(self, other: Self) -> None:
        """Raise ValueError if units don't match."""
        if self.unit != other.unit:
            raise ValueError(
                f"Cannot perform operation between {self.unit} and {other.unit}"
            )

    def __add__(self, other: Self) -> Self:
        """Add two RewardsBalance of same unit.

        Args:
            other: Another RewardsBalance with same unit.

        Returns:
            New RewardsBalance with sum of values.

        Raises:
            ValueError: If units don't match.
        """
        self._check_same_unit(other)
        return RewardsBalance(self.value + other.value, self.unit)

    def __sub__(self, other: Self) -> Self:
        """Subtract other from self (same unit).

        Args:
            other: Another RewardsBalance with same unit.

        Returns:
            New RewardsBalance with difference of values.

        Raises:
            ValueError: If units don't match.
        """
        self._check_same_unit(other)
        return RewardsBalance(self.value - other.value, self.unit)

    def __str__(self) -> str:
        """Return formatted string representation.

        Returns:
            Formatted string like "50,000 Alaska Miles".
        """
        return f"{int(self.value):,} {self.unit}"

    def is_positive(self) -> bool:
        """Check if value is positive (greater than zero)."""
        return self.value > 0

    def is_negative(self) -> bool:
        """Check if value is negative (less than zero)."""
        return self.value < 0

    def is_zero(self) -> bool:
        """Check if value is zero."""
        return self.value == 0
