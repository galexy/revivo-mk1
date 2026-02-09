"""Transaction aggregate root entity.

CONTEXT DECISIONS (override research):
1. Always-split model: Every transaction has 1+ split lines (even single-category)
2. Transaction amount = net flow to account (positive = inflow, negative = outflow)
3. Split amounts are SIGNED (positive = income, negative = expense)
4. All splits must sum exactly to transaction amount
5. Transfer splits create mirror transactions (mirrors are incoming, positive)
6. Dual dates: effective_date (logical) and posted_date (cleared)
7. Status: PENDING -> CLEARED -> RECONCILED
8. Check number for paper check tracking
"""

from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Self

from domain.events.base import DomainEvent
from domain.events.transaction_events import (
    TransactionCreated,
    TransactionDeleted,
    TransactionStatusChanged,
    TransactionUpdated,
)
from domain.model.entity_id import (
    AccountId,
    HouseholdId,
    PayeeId,
    SplitId,
    TransactionId,
    UserId,
)
from domain.model.money import Money
from domain.model.split_line import SplitLine
from domain.model.transaction_types import TransactionSource, TransactionStatus


@dataclass(eq=False)
class Transaction:
    """Transaction aggregate root - always-split model.

    Every transaction has 1+ split lines. Single-category transactions
    have one split. Transfer splits create mirror transactions automatically.

    Key invariants:
    - sum(split.amount) == self.amount (always)
    - Transfer splits must be negative (outgoing)
    - Mirror transactions are incoming (positive amount)
    """

    id: TransactionId
    user_id: UserId
    household_id: HouseholdId
    account_id: AccountId  # Primary account

    # Dates per CONTEXT
    effective_date: date  # When transaction logically occurred
    posted_date: date | None  # When cleared/posted (None = pending)

    # Amount: net flow to account (positive = inflow, negative = outflow)
    amount: Money

    # Status progression: PENDING -> CLEARED -> RECONCILED
    status: TransactionStatus

    # Source for Phase 6 foundation
    source: TransactionSource

    # Always-split model: 1+ split lines
    splits: list[SplitLine] = field(default_factory=lambda: list[SplitLine]())

    # Payee (managed entity)
    payee_id: PayeeId | None = None
    payee_name: str | None = None  # Denormalized for display

    # Description and reference
    memo: str | None = None  # Transaction-level memo
    check_number: str | None = None  # Paper check tracking

    # Mirror transaction link (for transfer targets)
    source_transaction_id: TransactionId | None = None  # If this is a mirror
    source_split_id: SplitId | None = None  # Which split created this mirror
    is_mirror: bool = False

    # Audit
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    # Domain events
    _events: list[DomainEvent] = field(
        default_factory=lambda: list[DomainEvent](), repr=False
    )

    @property
    def events(self) -> list[DomainEvent]:
        return list(self._events)

    def clear_events(self) -> None:
        self._events.clear()

    # --- Validation ---

    def _validate_splits_sum(self) -> None:
        """Validate that splits sum exactly to transaction amount."""
        if not self.splits:
            raise ValueError("Transaction must have at least one split")

        total = sum((s.amount.amount for s in self.splits), Decimal("0"))
        if total != self.amount.amount:
            raise ValueError(
                f"Splits sum ({total}) must equal transaction amount ({self.amount.amount})"
            )

    def _validate_no_self_transfer(self) -> None:
        """Validate no transfer split targets own account."""
        for split in self.splits:
            if split.transfer_account_id == self.account_id:
                raise ValueError("Cannot transfer to same account")

    def _validate_no_circular_transfers(self) -> None:
        """Validate no A->B->A circular transfers in same transaction."""
        target_accounts = [s.transfer_account_id for s in self.splits if s.is_transfer]
        if len(target_accounts) != len(set(target_accounts)):
            raise ValueError("Duplicate transfer targets not allowed")

    # --- Factory Methods ---

    @classmethod
    def create(
        cls,
        user_id: UserId,
        account_id: AccountId,
        effective_date: date,
        amount: Money,
        splits: list[SplitLine],
        household_id: HouseholdId | None = None,
        payee_id: PayeeId | None = None,
        payee_name: str | None = None,
        memo: str | None = None,
        check_number: str | None = None,
        posted_date: date | None = None,
        source: TransactionSource = TransactionSource.MANUAL,
    ) -> Self:
        """Create a transaction with split lines.

        Args:
            user_id: Owner of transaction
            account_id: Primary account affected
            effective_date: When transaction logically occurred
            amount: Net flow (positive = inflow, negative = outflow)
            splits: 1+ split lines that sum to amount
            payee_id: Optional managed payee reference
            payee_name: Payee display name
            memo: Transaction-level memo
            check_number: For paper check tracking
            posted_date: When cleared (defaults to effective_date for manual)
            source: MANUAL or DOWNLOADED
        """
        txn = cls(
            id=TransactionId.generate(),
            user_id=user_id,
            household_id=household_id
            or HouseholdId.from_string("hh_00000000000000000000000000"),
            account_id=account_id,
            effective_date=effective_date,
            posted_date=posted_date or effective_date,  # Default per CONTEXT
            amount=amount,
            status=TransactionStatus.PENDING,
            source=source,
            splits=splits,
            payee_id=payee_id,
            payee_name=payee_name,
            memo=memo,
            check_number=check_number,
        )

        # Validate invariants
        txn._validate_splits_sum()
        txn._validate_no_self_transfer()
        txn._validate_no_circular_transfers()

        txn._events.append(
            TransactionCreated(
                aggregate_id=str(txn.id),
                aggregate_type="Transaction",
                account_id=str(account_id),
                amount=str(amount.amount),
                currency=amount.currency,
                is_mirror=False,
            )
        )
        return txn

    @classmethod
    def create_mirror(
        cls,
        source_transaction: "Transaction",
        source_split: SplitLine,
        target_account_id: AccountId,
        amount: Money,
        effective_date: date,
    ) -> Self:
        """Create a mirror transaction for transfer target.

        Per CONTEXT:
        - Mirror is always incoming (positive amount)
        - Single split on mirrors for categorization
        - Inherits memo from source
        - Effective date syncs with source; posted_date independent
        - Links to source split via source_split_id for proper matching

        Args:
            source_transaction: The source transaction containing the transfer split.
            source_split: The specific transfer split that triggers this mirror.
            target_account_id: Account receiving the transfer.
            amount: Transfer amount (will be made positive for mirror).
            effective_date: When transfer logically occurred.
        """
        # Mirror amount is positive (incoming to target account)
        if amount.is_negative():
            amount = Money(-amount.amount, amount.currency)

        # Create single split for categorization (Uncategorized/Transfer)
        mirror_split = SplitLine.create(
            amount=amount,
            category_id=None,  # Will be "Uncategorized" or "Transfer" meta-category
            transfer_account_id=None,  # Mirrors don't have transfer splits
            memo=source_transaction.memo,
        )

        mirror = cls(
            id=TransactionId.generate(),
            user_id=source_transaction.user_id,
            household_id=source_transaction.household_id,
            account_id=target_account_id,
            effective_date=effective_date,
            posted_date=None,  # Independent from source per CONTEXT
            amount=amount,
            status=TransactionStatus.PENDING,
            source=source_transaction.source,
            splits=[mirror_split],
            payee_id=source_transaction.payee_id,
            payee_name=source_transaction.payee_name,
            memo=source_transaction.memo,
            source_transaction_id=source_transaction.id,
            source_split_id=source_split.id,
            is_mirror=True,
        )

        mirror._events.append(
            TransactionCreated(
                aggregate_id=str(mirror.id),
                aggregate_type="Transaction",
                account_id=str(target_account_id),
                amount=str(amount.amount),
                currency=amount.currency,
                is_mirror=True,
            )
        )
        return mirror

    # --- Query Properties ---

    @property
    def is_expense(self) -> bool:
        """Transaction is expense (negative net flow)."""
        return self.amount.is_negative()

    @property
    def is_income(self) -> bool:
        """Transaction is income (positive net flow)."""
        return not self.amount.is_negative() and not self.amount.is_zero()

    @property
    def has_transfer_splits(self) -> bool:
        """Transaction has at least one transfer split."""
        return any(s.is_transfer for s in self.splits)

    @property
    def transfer_account_ids(self) -> list[AccountId]:
        """Get all target account IDs from transfer splits."""
        return [
            s.transfer_account_id
            for s in self.splits
            if s.is_transfer and s.transfer_account_id
        ]

    # --- Mutation Methods ---

    def update_memo(self, new_memo: str | None) -> None:
        """Update transaction memo."""
        old_memo = self.memo
        self.memo = new_memo
        self.updated_at = datetime.now(UTC)
        self._events.append(
            TransactionUpdated(
                aggregate_id=str(self.id),
                aggregate_type="Transaction",
                field="memo",
                old_value=old_memo,
                new_value=new_memo,
            )
        )

    def update_payee(self, payee_id: PayeeId | None, payee_name: str | None) -> None:
        """Update transaction payee."""
        old_payee = self.payee_name
        self.payee_id = payee_id
        self.payee_name = payee_name
        self.updated_at = datetime.now(UTC)
        self._events.append(
            TransactionUpdated(
                aggregate_id=str(self.id),
                aggregate_type="Transaction",
                field="payee",
                old_value=old_payee,
                new_value=payee_name,
            )
        )

    def update_check_number(self, check_number: str | None) -> None:
        """Update check number."""
        old_check = self.check_number
        self.check_number = check_number
        self.updated_at = datetime.now(UTC)
        self._events.append(
            TransactionUpdated(
                aggregate_id=str(self.id),
                aggregate_type="Transaction",
                field="check_number",
                old_value=old_check,
                new_value=check_number,
            )
        )

    def update_effective_date(self, new_date: date) -> None:
        """Update effective date."""
        old_date = self.effective_date
        self.effective_date = new_date
        self.updated_at = datetime.now(UTC)
        self._events.append(
            TransactionUpdated(
                aggregate_id=str(self.id),
                aggregate_type="Transaction",
                field="effective_date",
                old_value=old_date.isoformat(),
                new_value=new_date.isoformat(),
            )
        )

    def update_posted_date(self, new_date: date | None) -> None:
        """Update posted date."""
        old_date = self.posted_date
        self.posted_date = new_date
        self.updated_at = datetime.now(UTC)
        self._events.append(
            TransactionUpdated(
                aggregate_id=str(self.id),
                aggregate_type="Transaction",
                field="posted_date",
                old_value=old_date.isoformat() if old_date else None,
                new_value=new_date.isoformat() if new_date else None,
            )
        )

    def mark_cleared(self, posted_date: date | None = None) -> None:
        """Mark transaction as cleared."""
        if self.status == TransactionStatus.CLEARED:
            raise ValueError("Transaction is already cleared")
        if self.status == TransactionStatus.RECONCILED:
            raise ValueError("Cannot change status from reconciled to cleared")

        old_status = self.status
        self.status = TransactionStatus.CLEARED
        if posted_date:
            self.posted_date = posted_date
        self.updated_at = datetime.now(UTC)

        self._events.append(
            TransactionStatusChanged(
                aggregate_id=str(self.id),
                aggregate_type="Transaction",
                old_status=old_status.value,
                new_status=TransactionStatus.CLEARED.value,
            )
        )

    def mark_reconciled(self) -> None:
        """Mark transaction as reconciled.

        Status progression: PENDING -> CLEARED -> RECONCILED
        Must be cleared before reconciling.
        """
        if self.status == TransactionStatus.RECONCILED:
            raise ValueError("Transaction is already reconciled")
        if self.status == TransactionStatus.PENDING:
            raise ValueError("Transaction must be cleared before reconciling")

        old_status = self.status
        self.status = TransactionStatus.RECONCILED
        self.updated_at = datetime.now(UTC)

        self._events.append(
            TransactionStatusChanged(
                aggregate_id=str(self.id),
                aggregate_type="Transaction",
                old_status=old_status.value,
                new_status=TransactionStatus.RECONCILED.value,
            )
        )

    def update_splits(self, new_splits: list[SplitLine], new_amount: Money) -> None:
        """Update splits and amount together (must remain balanced).

        For editing split allocations. Both splits and amount must change together
        to maintain the invariant: sum(splits) == amount.
        """
        old_amount = self.amount
        self.splits = new_splits
        self.amount = new_amount

        # Validate invariants
        self._validate_splits_sum()
        self._validate_no_self_transfer()
        self._validate_no_circular_transfers()

        self.updated_at = datetime.now(UTC)
        self._events.append(
            TransactionUpdated(
                aggregate_id=str(self.id),
                aggregate_type="Transaction",
                field="splits",
                old_value=str(old_amount.amount),
                new_value=str(new_amount.amount),
            )
        )

    def update_amount(self, new_amount: Money) -> None:
        """Update transaction amount (for mirror sync).

        Used by TransactionService to sync mirror amounts when source splits change.
        Mirror transactions have a single split that must also be updated.
        Split ID is preserved since SplitLine is immutable and recreated with same ID.
        """
        old_amount = self.amount
        self.amount = new_amount

        # Update single split for mirrors, preserving the split ID
        if self.is_mirror and len(self.splits) == 1:
            old_split = self.splits[0]
            self.splits = [
                SplitLine(
                    id=old_split.id,  # Preserve split ID across updates
                    amount=new_amount,
                    category_id=old_split.category_id,
                    transfer_account_id=old_split.transfer_account_id,
                    memo=old_split.memo,
                )
            ]

        self.updated_at = datetime.now(UTC)
        self._events.append(
            TransactionUpdated(
                aggregate_id=str(self.id),
                aggregate_type="Transaction",
                field="amount",
                old_value=str(old_amount.amount),
                new_value=str(new_amount.amount),
            )
        )

    def delete(self) -> None:
        """Mark transaction for deletion (emits event)."""
        self._events.append(
            TransactionDeleted(
                aggregate_id=str(self.id),
                aggregate_type="Transaction",
                was_mirror=self.is_mirror,
            )
        )
