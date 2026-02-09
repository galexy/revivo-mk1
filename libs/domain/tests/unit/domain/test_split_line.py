"""Unit tests for SplitLine entity with identity."""

import pytest

from domain.model.entity_id import AccountId, CategoryId, SplitId
from domain.model.money import Money
from domain.model.split_line import SplitLine


class TestSplitLineIdentity:
    """Tests for SplitLine ID behavior."""

    def test_split_line_create_generates_id(self) -> None:
        """SplitLine.create() should generate a unique ID."""
        split = SplitLine.create(
            amount=Money("-100.00", "USD"),
            category_id=CategoryId.generate(),
        )
        assert split.id is not None
        assert split.id.prefix == "split"

    def test_split_line_create_multiple_have_unique_ids(self) -> None:
        """Multiple SplitLine.create() calls should generate unique IDs."""
        split1 = SplitLine.create(amount=Money("-50.00", "USD"))
        split2 = SplitLine.create(amount=Money("-50.00", "USD"))
        assert split1.id != split2.id

    def test_split_line_with_explicit_id(self) -> None:
        """SplitLine can be created with explicit ID (for loading from DB)."""
        explicit_id = SplitId.generate()
        split = SplitLine(
            id=explicit_id,
            amount=Money("-100.00", "USD"),
        )
        assert split.id == explicit_id

    def test_split_line_immutable_with_id(self) -> None:
        """SplitLine should remain immutable (frozen dataclass)."""
        split = SplitLine.create(amount=Money("-100.00", "USD"))
        with pytest.raises(AttributeError):
            split.amount = Money("-200.00", "USD")  # type: ignore


class TestSplitLineValidation:
    """Tests for SplitLine validation with ID."""

    def test_split_line_cannot_have_both_category_and_transfer(self) -> None:
        """Split cannot have both category_id and transfer_account_id."""
        with pytest.raises(ValueError, match="cannot have both"):
            SplitLine.create(
                amount=Money("-100.00", "USD"),
                category_id=CategoryId.generate(),
                transfer_account_id=AccountId.generate(),
            )

    def test_split_line_transfer_must_be_negative(self) -> None:
        """Transfer split must have negative amount."""
        with pytest.raises(ValueError, match="must be negative"):
            SplitLine.create(
                amount=Money("100.00", "USD"),  # Positive - invalid for transfer
                transfer_account_id=AccountId.generate(),
            )

    def test_split_line_uncategorized_allowed(self) -> None:
        """Split can have neither category nor transfer (uncategorized)."""
        split = SplitLine.create(
            amount=Money("-100.00", "USD"),
            memo="Uncategorized expense",
        )
        assert split.is_uncategorized
        assert not split.is_categorized
        assert not split.is_transfer


class TestSplitLineProperties:
    """Tests for SplitLine property methods."""

    def test_is_transfer_with_transfer_account(self) -> None:
        """is_transfer should be True when transfer_account_id is set."""
        split = SplitLine.create(
            amount=Money("-100.00", "USD"),
            transfer_account_id=AccountId.generate(),
        )
        assert split.is_transfer

    def test_is_categorized_with_category(self) -> None:
        """is_categorized should be True when category_id is set."""
        split = SplitLine.create(
            amount=Money("-100.00", "USD"),
            category_id=CategoryId.generate(),
        )
        assert split.is_categorized
