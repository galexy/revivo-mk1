"""Unit tests for Transaction aggregate root.

Tests cover:
- Factory methods (create, create_mirror)
- Status transitions (PENDING -> CLEARED -> RECONCILED)
- Update methods (amount, memo, payee, dates, splits)
- Delete operation
- Event emission on state changes
- Split validation invariants
"""

from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from domain.events.transaction_events import (
    TransactionCreated,
    TransactionDeleted,
    TransactionStatusChanged,
    TransactionUpdated,
)
from domain.model.entity_id import (
    AccountId,
    CategoryId,
    HouseholdId,
    PayeeId,
    UserId,
)
from domain.model.money import Money
from domain.model.split_line import SplitLine
from domain.model.transaction import Transaction
from domain.model.transaction_types import TransactionSource, TransactionStatus

# --- Fixtures ---


@pytest.fixture
def user_id() -> UserId:
    """Generate test UserId."""
    return UserId.generate()


@pytest.fixture
def account_id() -> AccountId:
    """Generate test AccountId."""
    return AccountId.generate()


@pytest.fixture
def category_id() -> CategoryId:
    """Generate test CategoryId."""
    return CategoryId.generate()


@pytest.fixture
def payee_id() -> PayeeId:
    """Generate test PayeeId."""
    return PayeeId.generate()


@pytest.fixture
def usd_amount() -> Money:
    """Standard USD amount for testing."""
    return Money(Decimal("-50.00"), "USD")


@pytest.fixture
def effective_date() -> date:
    """Standard effective date for testing."""
    return date(2024, 1, 15)


@pytest.fixture
def single_split(category_id: CategoryId, usd_amount: Money) -> list[SplitLine]:
    """Single split matching the usd_amount fixture."""
    return [SplitLine.create(amount=usd_amount, category_id=category_id)]


# --- TestTransactionCreate ---


class TestTransactionCreate:
    """Test Transaction.create() factory method."""

    def test_create_with_required_fields(
        self,
        user_id: UserId,
        account_id: AccountId,
        usd_amount: Money,
        effective_date: date,
        single_split: list[SplitLine],
    ):
        """Creates transaction with required fields and default values."""
        txn = Transaction.create(
            user_id=user_id,
            account_id=account_id,
            effective_date=effective_date,
            amount=usd_amount,
            splits=single_split,
        )

        assert txn.id is not None
        assert str(txn.id).startswith("txn_")
        assert txn.user_id == user_id
        assert txn.account_id == account_id
        assert txn.effective_date == effective_date
        assert txn.amount == usd_amount
        assert txn.splits == single_split
        assert txn.status == TransactionStatus.PENDING
        assert txn.source == TransactionSource.MANUAL
        assert txn.posted_date == effective_date  # Default per CONTEXT
        assert txn.is_mirror is False

    def test_create_generates_unique_transaction_id(
        self,
        user_id: UserId,
        account_id: AccountId,
        usd_amount: Money,
        effective_date: date,
        single_split: list[SplitLine],
    ):
        """Each create generates a unique TransactionId."""
        txn1 = Transaction.create(
            user_id=user_id,
            account_id=account_id,
            effective_date=effective_date,
            amount=usd_amount,
            splits=single_split,
        )
        txn2 = Transaction.create(
            user_id=user_id,
            account_id=account_id,
            effective_date=effective_date,
            amount=usd_amount,
            splits=single_split,
        )

        assert txn1.id != txn2.id

    def test_create_sets_timestamps(
        self,
        user_id: UserId,
        account_id: AccountId,
        usd_amount: Money,
        effective_date: date,
        single_split: list[SplitLine],
    ):
        """Sets created_at and updated_at timestamps."""
        before = datetime.now(UTC)
        txn = Transaction.create(
            user_id=user_id,
            account_id=account_id,
            effective_date=effective_date,
            amount=usd_amount,
            splits=single_split,
        )
        after = datetime.now(UTC)

        assert before <= txn.created_at <= after
        assert before <= txn.updated_at <= after

    def test_create_emits_transaction_created_event(
        self,
        user_id: UserId,
        account_id: AccountId,
        usd_amount: Money,
        effective_date: date,
        single_split: list[SplitLine],
    ):
        """Emits TransactionCreated event."""
        txn = Transaction.create(
            user_id=user_id,
            account_id=account_id,
            effective_date=effective_date,
            amount=usd_amount,
            splits=single_split,
        )

        assert len(txn.events) == 1
        event = txn.events[0]
        assert isinstance(event, TransactionCreated)
        assert event.aggregate_id == str(txn.id)
        assert event.aggregate_type == "Transaction"
        assert event.account_id == str(account_id)
        assert event.amount == str(usd_amount.amount)
        assert event.currency == usd_amount.currency
        assert event.is_mirror is False

    def test_create_with_optional_fields(
        self,
        user_id: UserId,
        account_id: AccountId,
        usd_amount: Money,
        effective_date: date,
        single_split: list[SplitLine],
        payee_id: PayeeId,
    ):
        """Creates transaction with optional payee, memo, check_number."""
        posted = date(2024, 1, 16)
        txn = Transaction.create(
            user_id=user_id,
            account_id=account_id,
            effective_date=effective_date,
            amount=usd_amount,
            splits=single_split,
            payee_id=payee_id,
            payee_name="Test Payee",
            memo="Test memo",
            check_number="1234",
            posted_date=posted,
            source=TransactionSource.DOWNLOADED,
        )

        assert txn.payee_id == payee_id
        assert txn.payee_name == "Test Payee"
        assert txn.memo == "Test memo"
        assert txn.check_number == "1234"
        assert txn.posted_date == posted
        assert txn.source == TransactionSource.DOWNLOADED

    def test_create_validates_splits_sum_equals_amount(
        self,
        user_id: UserId,
        account_id: AccountId,
        effective_date: date,
        category_id: CategoryId,
    ):
        """Raises ValueError when splits sum does not equal amount."""
        amount = Money(Decimal("-100.00"), "USD")
        splits = [
            SplitLine.create(
                amount=Money(Decimal("-50.00"), "USD"), category_id=category_id
            )
        ]  # Only half the amount

        with pytest.raises(ValueError, match="Splits sum .* must equal"):
            Transaction.create(
                user_id=user_id,
                account_id=account_id,
                effective_date=effective_date,
                amount=amount,
                splits=splits,
            )

    def test_create_validates_no_self_transfer(
        self,
        user_id: UserId,
        account_id: AccountId,
        effective_date: date,
    ):
        """Raises ValueError when transfer split targets own account."""
        amount = Money(Decimal("-50.00"), "USD")
        splits = [
            SplitLine.create(
                amount=amount, transfer_account_id=account_id
            )  # Self-transfer
        ]

        with pytest.raises(ValueError, match="Cannot transfer to same account"):
            Transaction.create(
                user_id=user_id,
                account_id=account_id,
                effective_date=effective_date,
                amount=amount,
                splits=splits,
            )

    def test_create_uses_default_household_id(
        self,
        user_id: UserId,
        account_id: AccountId,
        usd_amount: Money,
        effective_date: date,
        single_split: list[SplitLine],
    ):
        """Uses default household ID when not provided."""
        txn = Transaction.create(
            user_id=user_id,
            account_id=account_id,
            effective_date=effective_date,
            amount=usd_amount,
            splits=single_split,
        )

        assert txn.household_id == HouseholdId.from_string(
            "hh_00000000000000000000000000"
        )


# --- TestTransactionCreateMirror ---


class TestTransactionCreateMirror:
    """Test Transaction.create_mirror() factory method."""

    def test_create_mirror_for_transfer(
        self,
        user_id: UserId,
        account_id: AccountId,
        effective_date: date,
    ):
        """Creates mirror transaction for transfer with correct attributes."""
        target_account_id = AccountId.generate()
        transfer_amount = Money(Decimal("-100.00"), "USD")
        source_split = SplitLine.create(
            amount=transfer_amount, transfer_account_id=target_account_id
        )

        source_txn = Transaction.create(
            user_id=user_id,
            account_id=account_id,
            effective_date=effective_date,
            amount=transfer_amount,
            splits=[source_split],
            memo="Transfer to savings",
        )

        mirror = Transaction.create_mirror(
            source_transaction=source_txn,
            source_split=source_split,
            target_account_id=target_account_id,
            amount=transfer_amount,
            effective_date=effective_date,
        )

        assert mirror.id != source_txn.id
        assert str(mirror.id).startswith("txn_")
        assert mirror.account_id == target_account_id
        assert mirror.user_id == source_txn.user_id
        assert mirror.household_id == source_txn.household_id
        assert mirror.effective_date == effective_date
        assert mirror.is_mirror is True
        assert mirror.source_transaction_id == source_txn.id
        assert mirror.source_split_id == source_split.id

    def test_create_mirror_has_positive_amount(
        self,
        user_id: UserId,
        account_id: AccountId,
        effective_date: date,
    ):
        """Mirror has positive amount (incoming to target account)."""
        target_account_id = AccountId.generate()
        transfer_amount = Money(Decimal("-100.00"), "USD")  # Negative (outgoing)
        source_split = SplitLine.create(
            amount=transfer_amount, transfer_account_id=target_account_id
        )

        source_txn = Transaction.create(
            user_id=user_id,
            account_id=account_id,
            effective_date=effective_date,
            amount=transfer_amount,
            splits=[source_split],
        )

        mirror = Transaction.create_mirror(
            source_transaction=source_txn,
            source_split=source_split,
            target_account_id=target_account_id,
            amount=transfer_amount,
            effective_date=effective_date,
        )

        # Mirror amount is positive (incoming)
        assert mirror.amount == Money(Decimal("100.00"), "USD")
        assert mirror.amount.is_positive()

    def test_create_mirror_emits_transaction_created_event(
        self,
        user_id: UserId,
        account_id: AccountId,
        effective_date: date,
    ):
        """Mirror emits TransactionCreated event with is_mirror=True."""
        target_account_id = AccountId.generate()
        transfer_amount = Money(Decimal("-100.00"), "USD")
        source_split = SplitLine.create(
            amount=transfer_amount, transfer_account_id=target_account_id
        )

        source_txn = Transaction.create(
            user_id=user_id,
            account_id=account_id,
            effective_date=effective_date,
            amount=transfer_amount,
            splits=[source_split],
        )

        mirror = Transaction.create_mirror(
            source_transaction=source_txn,
            source_split=source_split,
            target_account_id=target_account_id,
            amount=transfer_amount,
            effective_date=effective_date,
        )

        assert len(mirror.events) == 1
        event = mirror.events[0]
        assert isinstance(event, TransactionCreated)
        assert event.is_mirror is True
        assert event.aggregate_id == str(mirror.id)

    def test_create_mirror_inherits_memo_from_source(
        self,
        user_id: UserId,
        account_id: AccountId,
        effective_date: date,
    ):
        """Mirror inherits memo from source transaction."""
        target_account_id = AccountId.generate()
        transfer_amount = Money(Decimal("-100.00"), "USD")
        source_split = SplitLine.create(
            amount=transfer_amount, transfer_account_id=target_account_id
        )

        source_txn = Transaction.create(
            user_id=user_id,
            account_id=account_id,
            effective_date=effective_date,
            amount=transfer_amount,
            splits=[source_split],
            memo="Transfer to savings",
        )

        mirror = Transaction.create_mirror(
            source_transaction=source_txn,
            source_split=source_split,
            target_account_id=target_account_id,
            amount=transfer_amount,
            effective_date=effective_date,
        )

        assert mirror.memo == "Transfer to savings"


# --- TestTransactionStatusChanges ---


class TestTransactionStatusChanges:
    """Test transaction status transitions."""

    def test_mark_cleared_from_pending(
        self,
        user_id: UserId,
        account_id: AccountId,
        usd_amount: Money,
        effective_date: date,
        single_split: list[SplitLine],
    ):
        """PENDING -> CLEARED via mark_cleared()."""
        txn = Transaction.create(
            user_id=user_id,
            account_id=account_id,
            effective_date=effective_date,
            amount=usd_amount,
            splits=single_split,
        )
        txn.clear_events()

        posted = date(2024, 1, 20)
        txn.mark_cleared(posted_date=posted)

        assert txn.status == TransactionStatus.CLEARED
        assert txn.posted_date == posted
        assert len(txn.events) == 1
        event = txn.events[0]
        assert isinstance(event, TransactionStatusChanged)
        assert event.old_status == TransactionStatus.PENDING.value
        assert event.new_status == TransactionStatus.CLEARED.value

    def test_mark_cleared_already_cleared_raises_error(
        self,
        user_id: UserId,
        account_id: AccountId,
        usd_amount: Money,
        effective_date: date,
        single_split: list[SplitLine],
    ):
        """Raises ValueError when marking already cleared transaction."""
        txn = Transaction.create(
            user_id=user_id,
            account_id=account_id,
            effective_date=effective_date,
            amount=usd_amount,
            splits=single_split,
        )
        txn.mark_cleared()

        with pytest.raises(ValueError, match="already cleared"):
            txn.mark_cleared()

    def test_mark_reconciled_from_cleared(
        self,
        user_id: UserId,
        account_id: AccountId,
        usd_amount: Money,
        effective_date: date,
        single_split: list[SplitLine],
    ):
        """CLEARED -> RECONCILED via mark_reconciled()."""
        txn = Transaction.create(
            user_id=user_id,
            account_id=account_id,
            effective_date=effective_date,
            amount=usd_amount,
            splits=single_split,
        )
        txn.mark_cleared()
        txn.clear_events()

        txn.mark_reconciled()

        assert txn.status == TransactionStatus.RECONCILED
        assert len(txn.events) == 1
        event = txn.events[0]
        assert isinstance(event, TransactionStatusChanged)
        assert event.old_status == TransactionStatus.CLEARED.value
        assert event.new_status == TransactionStatus.RECONCILED.value

    def test_mark_reconciled_from_pending_raises_error(
        self,
        user_id: UserId,
        account_id: AccountId,
        usd_amount: Money,
        effective_date: date,
        single_split: list[SplitLine],
    ):
        """Raises ValueError when reconciling non-cleared transaction."""
        txn = Transaction.create(
            user_id=user_id,
            account_id=account_id,
            effective_date=effective_date,
            amount=usd_amount,
            splits=single_split,
        )

        with pytest.raises(ValueError, match="must be cleared before reconciling"):
            txn.mark_reconciled()

    def test_mark_reconciled_already_reconciled_raises_error(
        self,
        user_id: UserId,
        account_id: AccountId,
        usd_amount: Money,
        effective_date: date,
        single_split: list[SplitLine],
    ):
        """Raises ValueError when marking already reconciled transaction."""
        txn = Transaction.create(
            user_id=user_id,
            account_id=account_id,
            effective_date=effective_date,
            amount=usd_amount,
            splits=single_split,
        )
        txn.mark_cleared()
        txn.mark_reconciled()

        with pytest.raises(ValueError, match="already reconciled"):
            txn.mark_reconciled()


# --- TestTransactionUpdate ---


class TestTransactionUpdate:
    """Test transaction update methods."""

    def test_update_memo(
        self,
        user_id: UserId,
        account_id: AccountId,
        usd_amount: Money,
        effective_date: date,
        single_split: list[SplitLine],
    ):
        """update_memo() changes memo and emits event."""
        txn = Transaction.create(
            user_id=user_id,
            account_id=account_id,
            effective_date=effective_date,
            amount=usd_amount,
            splits=single_split,
            memo="Old memo",
        )
        txn.clear_events()

        txn.update_memo("New memo")

        assert txn.memo == "New memo"
        assert len(txn.events) == 1
        event = txn.events[0]
        assert isinstance(event, TransactionUpdated)
        assert event.field == "memo"
        assert event.old_value == "Old memo"
        assert event.new_value == "New memo"

    def test_update_payee(
        self,
        user_id: UserId,
        account_id: AccountId,
        usd_amount: Money,
        effective_date: date,
        single_split: list[SplitLine],
        payee_id: PayeeId,
    ):
        """update_payee() changes payee_id and payee_name."""
        txn = Transaction.create(
            user_id=user_id,
            account_id=account_id,
            effective_date=effective_date,
            amount=usd_amount,
            splits=single_split,
        )
        txn.clear_events()

        new_payee_id = PayeeId.generate()
        txn.update_payee(new_payee_id, "New Payee")

        assert txn.payee_id == new_payee_id
        assert txn.payee_name == "New Payee"
        assert len(txn.events) == 1
        event = txn.events[0]
        assert isinstance(event, TransactionUpdated)
        assert event.field == "payee"
        assert event.new_value == "New Payee"

    def test_update_effective_date(
        self,
        user_id: UserId,
        account_id: AccountId,
        usd_amount: Money,
        effective_date: date,
        single_split: list[SplitLine],
    ):
        """update_effective_date() changes date and emits event."""
        txn = Transaction.create(
            user_id=user_id,
            account_id=account_id,
            effective_date=effective_date,
            amount=usd_amount,
            splits=single_split,
        )
        txn.clear_events()

        new_date = date(2024, 2, 1)
        txn.update_effective_date(new_date)

        assert txn.effective_date == new_date
        assert len(txn.events) == 1
        event = txn.events[0]
        assert isinstance(event, TransactionUpdated)
        assert event.field == "effective_date"
        assert event.old_value == effective_date.isoformat()
        assert event.new_value == new_date.isoformat()

    def test_update_posted_date(
        self,
        user_id: UserId,
        account_id: AccountId,
        usd_amount: Money,
        effective_date: date,
        single_split: list[SplitLine],
    ):
        """update_posted_date() changes posted date."""
        txn = Transaction.create(
            user_id=user_id,
            account_id=account_id,
            effective_date=effective_date,
            amount=usd_amount,
            splits=single_split,
        )
        txn.clear_events()

        new_posted = date(2024, 1, 18)
        txn.update_posted_date(new_posted)

        assert txn.posted_date == new_posted
        assert len(txn.events) == 1

    def test_update_check_number(
        self,
        user_id: UserId,
        account_id: AccountId,
        usd_amount: Money,
        effective_date: date,
        single_split: list[SplitLine],
    ):
        """update_check_number() changes check number."""
        txn = Transaction.create(
            user_id=user_id,
            account_id=account_id,
            effective_date=effective_date,
            amount=usd_amount,
            splits=single_split,
            check_number="100",
        )
        txn.clear_events()

        txn.update_check_number("101")

        assert txn.check_number == "101"
        assert len(txn.events) == 1
        event = txn.events[0]
        assert isinstance(event, TransactionUpdated)
        assert event.field == "check_number"

    def test_update_splits(
        self,
        user_id: UserId,
        account_id: AccountId,
        effective_date: date,
        category_id: CategoryId,
    ):
        """update_splits() replaces splits list and validates sum."""
        amount = Money(Decimal("-100.00"), "USD")
        old_splits = [SplitLine.create(amount=amount, category_id=category_id)]

        txn = Transaction.create(
            user_id=user_id,
            account_id=account_id,
            effective_date=effective_date,
            amount=amount,
            splits=old_splits,
        )
        txn.clear_events()

        # New split-transaction with two categories
        new_amount = Money(Decimal("-120.00"), "USD")
        new_splits = [
            SplitLine.create(
                amount=Money(Decimal("-80.00"), "USD"), category_id=category_id
            ),
            SplitLine.create(
                amount=Money(Decimal("-40.00"), "USD"), category_id=CategoryId.generate()
            ),
        ]

        txn.update_splits(new_splits, new_amount)

        assert txn.splits == new_splits
        assert txn.amount == new_amount
        assert len(txn.events) == 1
        event = txn.events[0]
        assert isinstance(event, TransactionUpdated)
        assert event.field == "splits"

    def test_update_amount_for_mirror(
        self,
        user_id: UserId,
        account_id: AccountId,
        effective_date: date,
    ):
        """update_amount() updates mirror amount and single split."""
        target_account_id = AccountId.generate()
        transfer_amount = Money(Decimal("-100.00"), "USD")
        source_split = SplitLine.create(
            amount=transfer_amount, transfer_account_id=target_account_id
        )

        source_txn = Transaction.create(
            user_id=user_id,
            account_id=account_id,
            effective_date=effective_date,
            amount=transfer_amount,
            splits=[source_split],
        )

        mirror = Transaction.create_mirror(
            source_transaction=source_txn,
            source_split=source_split,
            target_account_id=target_account_id,
            amount=transfer_amount,
            effective_date=effective_date,
        )
        mirror.clear_events()

        new_amount = Money(Decimal("150.00"), "USD")
        mirror.update_amount(new_amount)

        assert mirror.amount == new_amount
        assert len(mirror.splits) == 1
        assert mirror.splits[0].amount == new_amount
        assert len(mirror.events) == 1

    def test_mutation_updates_timestamp(
        self,
        user_id: UserId,
        account_id: AccountId,
        usd_amount: Money,
        effective_date: date,
        single_split: list[SplitLine],
    ):
        """All mutation methods update updated_at timestamp."""
        txn = Transaction.create(
            user_id=user_id,
            account_id=account_id,
            effective_date=effective_date,
            amount=usd_amount,
            splits=single_split,
        )
        original_updated_at = txn.updated_at

        txn.update_memo("New memo")

        assert txn.updated_at >= original_updated_at


# --- TestTransactionDelete ---


class TestTransactionDelete:
    """Test transaction delete operation."""

    def test_delete_emits_transaction_deleted_event(
        self,
        user_id: UserId,
        account_id: AccountId,
        usd_amount: Money,
        effective_date: date,
        single_split: list[SplitLine],
    ):
        """delete() emits TransactionDeleted event."""
        txn = Transaction.create(
            user_id=user_id,
            account_id=account_id,
            effective_date=effective_date,
            amount=usd_amount,
            splits=single_split,
        )
        txn.clear_events()

        txn.delete()

        assert len(txn.events) == 1
        event = txn.events[0]
        assert isinstance(event, TransactionDeleted)
        assert event.aggregate_id == str(txn.id)
        assert event.was_mirror is False

    def test_delete_mirror_sets_was_mirror_flag(
        self,
        user_id: UserId,
        account_id: AccountId,
        effective_date: date,
    ):
        """delete() on mirror sets was_mirror=True in event."""
        target_account_id = AccountId.generate()
        transfer_amount = Money(Decimal("-100.00"), "USD")
        source_split = SplitLine.create(
            amount=transfer_amount, transfer_account_id=target_account_id
        )

        source_txn = Transaction.create(
            user_id=user_id,
            account_id=account_id,
            effective_date=effective_date,
            amount=transfer_amount,
            splits=[source_split],
        )

        mirror = Transaction.create_mirror(
            source_transaction=source_txn,
            source_split=source_split,
            target_account_id=target_account_id,
            amount=transfer_amount,
            effective_date=effective_date,
        )
        mirror.clear_events()

        mirror.delete()

        event = mirror.events[0]
        assert isinstance(event, TransactionDeleted)
        assert event.was_mirror is True


# --- TestTransactionEvents ---


class TestTransactionEvents:
    """Test event collection."""

    def test_events_property_returns_copy(
        self,
        user_id: UserId,
        account_id: AccountId,
        usd_amount: Money,
        effective_date: date,
        single_split: list[SplitLine],
    ):
        """events property returns list of domain events."""
        txn = Transaction.create(
            user_id=user_id,
            account_id=account_id,
            effective_date=effective_date,
            amount=usd_amount,
            splits=single_split,
        )

        events = txn.events
        assert len(events) == 1
        assert isinstance(events[0], TransactionCreated)

    def test_clear_events_empties_list(
        self,
        user_id: UserId,
        account_id: AccountId,
        usd_amount: Money,
        effective_date: date,
        single_split: list[SplitLine],
    ):
        """clear_events() empties the events list."""
        txn = Transaction.create(
            user_id=user_id,
            account_id=account_id,
            effective_date=effective_date,
            amount=usd_amount,
            splits=single_split,
        )

        assert len(txn.events) == 1
        txn.clear_events()
        assert len(txn.events) == 0

    def test_multiple_mutations_accumulate_events(
        self,
        user_id: UserId,
        account_id: AccountId,
        usd_amount: Money,
        effective_date: date,
        single_split: list[SplitLine],
    ):
        """Multiple mutations accumulate events."""
        txn = Transaction.create(
            user_id=user_id,
            account_id=account_id,
            effective_date=effective_date,
            amount=usd_amount,
            splits=single_split,
        )
        txn.clear_events()

        txn.update_memo("New memo")
        txn.mark_cleared()
        txn.mark_reconciled()

        assert len(txn.events) == 3
        assert isinstance(txn.events[0], TransactionUpdated)
        assert isinstance(txn.events[1], TransactionStatusChanged)
        assert isinstance(txn.events[2], TransactionStatusChanged)
