"""SplitLine value object for transaction split lines.

Each transaction has 1+ split lines (even single-category transactions
have one split). Split amounts are signed:
- Positive = inflow (income)
- Negative = outflow (expense)

Splits must sum exactly to the transaction amount.
"""

from dataclasses import dataclass

from src.domain.model.entity_id import AccountId, CategoryId
from src.domain.model.money import Money


@dataclass(frozen=True, slots=True)
class SplitLine:
    """A single line in a split transaction.

    Per CONTEXT: Split amounts are SIGNED (positive = inflow, negative = outflow).
    Each split targets either a category OR a transfer account (not both).
    Transfer splits must be negative (outgoing from source account).

    Attributes:
        amount: SIGNED amount (positive for inflow, negative for outflow).
        category_id: Category for expense/income splits (mutually exclusive with transfer_account_id).
        transfer_account_id: Target account for transfer splits (mutually exclusive with category_id).
        memo: Optional per-split memo.
    """

    amount: Money
    category_id: CategoryId | None = None
    transfer_account_id: AccountId | None = None
    memo: str | None = None

    def __post_init__(self) -> None:
        """Validate split line constraints.

        Raises:
            ValueError: If split has both category and transfer account.
            ValueError: If transfer split amount is not negative.
        """
        # Validate: must have either category OR transfer account (or neither for uncategorized)
        if self.category_id is not None and self.transfer_account_id is not None:
            raise ValueError("Split cannot have both category and transfer account")

        # Transfer splits must be negative (outgoing from source account)
        if self.transfer_account_id is not None and not self.amount.is_negative():
            raise ValueError("Transfer split amount must be negative (outgoing)")

    @property
    def is_transfer(self) -> bool:
        """Check if this is a transfer split targeting another account."""
        return self.transfer_account_id is not None

    @property
    def is_categorized(self) -> bool:
        """Check if this split has a category assigned."""
        return self.category_id is not None

    @property
    def is_uncategorized(self) -> bool:
        """Check if this split has no category and is not a transfer."""
        return self.category_id is None and self.transfer_account_id is None
