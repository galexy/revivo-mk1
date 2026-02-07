"""Application service for Transaction use cases.

Handles transaction CRUD, mirror transaction management, and business validations.
Per CONTEXT: auto-payee creation, mirror transactions for transfers, status progression.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from src.domain.events.transaction_events import (
    MirrorTransactionCreated,
    MirrorTransactionDeleted,
)
from src.domain.model.entity_id import AccountId, CategoryId, HouseholdId, PayeeId, TransactionId, UserId
from src.domain.model.money import Money
from src.domain.model.split_line import SplitLine
from src.domain.model.transaction import Transaction
from src.domain.model.transaction_types import TransactionSource, TransactionStatus

if TYPE_CHECKING:
    from src.domain.ports.unit_of_work import UnitOfWork


@dataclass(frozen=True, slots=True)
class TransactionError:
    """Error result for transaction operations."""

    code: str
    message: str


class TransactionService:
    """Application service for transaction management."""

    def __init__(self, uow: "UnitOfWork") -> None:
        self._uow = uow

    def _validate_account(
        self, user_id: UserId, account_id: AccountId
    ) -> tuple[bool, str | None]:
        """Validate account exists and belongs to user."""
        account = self._uow.accounts.get(account_id)
        if account is None:
            return False, "Account not found"
        if account.user_id != user_id:
            return False, "Account does not belong to user"
        if not account.is_active:
            return False, "Account is not active"
        return True, None

    def _validate_category(
        self, user_id: UserId, category_id: CategoryId
    ) -> tuple[bool, str | None]:
        """Validate category exists and belongs to user."""
        category = self._uow.categories.get(category_id)
        if category is None:
            return False, "Category not found"
        if category.user_id != user_id:
            return False, "Category does not belong to user"
        return True, None

    def _validate_splits(
        self,
        user_id: UserId,
        account_id: AccountId,
        splits: list[SplitLine],
        total_amount: Money,
    ) -> tuple[bool, str | None]:
        """Validate splits sum to total and all references are valid."""
        # Check sum
        split_sum = sum((s.amount.amount for s in splits), Decimal("0"))
        if split_sum != total_amount.amount:
            return (
                False,
                f"Splits sum ({split_sum}) must equal amount ({total_amount.amount})",
            )

        # Validate each split
        for split in splits:
            if split.category_id:
                valid, msg = self._validate_category(user_id, split.category_id)
                if not valid:
                    return False, msg
            if split.transfer_account_id:
                if split.transfer_account_id == account_id:
                    return False, "Cannot transfer to same account"
                valid, msg = self._validate_account(user_id, split.transfer_account_id)
                if not valid:
                    return False, f"Transfer target: {msg}"

        return True, None

    def _get_or_create_payee(
        self,
        user_id: UserId,
        payee_name: str | None,
        household_id: HouseholdId | None = None,
    ) -> tuple[PayeeId | None, str | None]:
        """Get or create payee by name, returning (payee_id, payee_name)."""
        if not payee_name:
            return None, None

        payee = self._uow.payees.get_or_create(
            user_id, payee_name, household_id=household_id
        )
        payee.record_usage()
        return payee.id, payee.name

    def _create_mirror_transactions(
        self,
        source_transaction: Transaction,
    ) -> list[Transaction]:
        """Create mirror transactions for transfer splits."""
        mirrors = []

        for split in source_transaction.splits:
            if split.is_transfer and split.transfer_account_id:
                # Create mirror (incoming to target account)
                mirror = Transaction.create_mirror(
                    source_transaction=source_transaction,
                    source_split=split,
                    target_account_id=split.transfer_account_id,
                    amount=split.amount,  # Will be negated to positive in create_mirror
                    effective_date=source_transaction.effective_date,
                )

                self._uow.transactions.add(mirror)
                mirrors.append(mirror)

                # Emit event
                self._uow.collect_events(
                    [
                        MirrorTransactionCreated(
                            aggregate_id=str(mirror.id),
                            aggregate_type="Transaction",
                            source_transaction_id=str(source_transaction.id),
                            mirror_transaction_id=str(mirror.id),
                            target_account_id=str(split.transfer_account_id),
                        )
                    ]
                )

        return mirrors

    def _sync_mirrors_for_split_update(
        self,
        source_transaction: Transaction,
        old_splits: list[SplitLine],
        new_splits: list[SplitLine],
    ) -> None:
        """Sync mirror transactions when splits are updated.

        Handles:
        - Deleted transfer splits: delete corresponding mirrors
        - New transfer splits: create new mirrors
        - Updated transfer splits: update mirror amounts
        """
        # Build maps of transfer splits by target account
        old_transfers = {
            str(s.transfer_account_id): s
            for s in old_splits
            if s.is_transfer and s.transfer_account_id
        }
        new_transfers = {
            str(s.transfer_account_id): s
            for s in new_splits
            if s.is_transfer and s.transfer_account_id
        }

        # Get existing mirrors
        existing_mirrors = self._uow.transactions.get_mirrors_for_source(
            source_transaction.id
        )
        mirrors_by_account = {str(m.account_id): m for m in existing_mirrors}

        # Delete mirrors for removed transfer splits
        for acct_id in old_transfers:
            if acct_id not in new_transfers:
                if acct_id in mirrors_by_account:
                    mirror = mirrors_by_account[acct_id]
                    self._uow.collect_events(
                        [
                            MirrorTransactionDeleted(
                                aggregate_id=str(mirror.id),
                                aggregate_type="Transaction",
                                source_transaction_id=str(source_transaction.id),
                                mirror_transaction_id=str(mirror.id),
                            )
                        ]
                    )
                    self._uow.transactions.delete(mirror.id)

        # Create/update mirrors for new/changed transfer splits
        for acct_id, split in new_transfers.items():
            if acct_id in mirrors_by_account:
                # Update existing mirror amount
                mirror = mirrors_by_account[acct_id]
                # Mirror amount is negated (positive for incoming)
                new_mirror_amount = Money(-split.amount.amount, split.amount.currency)
                mirror.update_amount(new_mirror_amount)
                self._uow.transactions.update(mirror)
            else:
                # Create new mirror
                mirror = Transaction.create_mirror(
                    source_transaction=source_transaction,
                    source_split=split,
                    target_account_id=AccountId.from_string(acct_id),
                    amount=split.amount,
                    effective_date=source_transaction.effective_date,
                )
                self._uow.transactions.add(mirror)
                self._uow.collect_events(
                    [
                        MirrorTransactionCreated(
                            aggregate_id=str(mirror.id),
                            aggregate_type="Transaction",
                            source_transaction_id=str(source_transaction.id),
                            mirror_transaction_id=str(mirror.id),
                            target_account_id=acct_id,
                        )
                    ]
                )

    async def create_transaction(
        self,
        user_id: UserId,
        account_id: AccountId,
        effective_date: date,
        amount: Money,
        splits: list[SplitLine],
        payee_name: str | None = None,
        memo: str | None = None,
        check_number: str | None = None,
        posted_date: date | None = None,
        source: TransactionSource = TransactionSource.MANUAL,
        household_id: HouseholdId | None = None,
    ) -> Transaction | TransactionError:
        """Create a transaction with splits.

        Per CONTEXT:
        - Every transaction has 1+ splits
        - Auto-creates payee if name provided
        - Auto-creates mirror transactions for transfer splits
        """
        with self._uow:
            # Validate account
            valid, msg = self._validate_account(user_id, account_id)
            if not valid:
                return TransactionError("INVALID_ACCOUNT", msg or "Invalid account")

            # Validate splits
            if not splits:
                return TransactionError(
                    "NO_SPLITS", "Transaction must have at least one split"
                )
            valid, msg = self._validate_splits(user_id, account_id, splits, amount)
            if not valid:
                return TransactionError("INVALID_SPLITS", msg or "Invalid splits")

            # Get or create payee
            payee_id, payee_display = self._get_or_create_payee(
                user_id, payee_name, household_id=household_id
            )

            # Flush to ensure payee exists in DB before transaction insert (FK constraint)
            if payee_id:
                self._uow.flush()

            # Create transaction
            try:
                txn = Transaction.create(
                    user_id=user_id,
                    account_id=account_id,
                    effective_date=effective_date,
                    amount=amount,
                    splits=splits,
                    household_id=household_id,
                    payee_id=payee_id,
                    payee_name=payee_display,
                    memo=memo,
                    check_number=check_number,
                    posted_date=posted_date,
                    source=source,
                )
            except ValueError as e:
                return TransactionError("VALIDATION_ERROR", str(e))

            self._uow.transactions.add(txn)
            self._uow.collect_events(txn.events)
            txn.clear_events()

            # Create mirror transactions for transfers
            self._create_mirror_transactions(txn)

            await self._uow.commit()

            return txn

    def get_transaction(
        self,
        user_id: UserId,
        transaction_id: TransactionId,
    ) -> Transaction | TransactionError:
        """Get a transaction by ID."""
        with self._uow:
            txn = self._uow.transactions.get(transaction_id)
            if txn is None:
                return TransactionError("NOT_FOUND", "Transaction not found")
            if txn.user_id != user_id:
                return TransactionError(
                    "NOT_OWNED", "Transaction does not belong to user"
                )
            return txn

    def get_account_transactions(
        self,
        user_id: UserId,
        account_id: AccountId,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Transaction] | TransactionError:
        """Get transactions for an account."""
        with self._uow:
            # Validate account
            valid, msg = self._validate_account(user_id, account_id)
            if not valid:
                return TransactionError("INVALID_ACCOUNT", msg or "Invalid account")

            return self._uow.transactions.get_by_account(account_id, limit, offset)

    def search_transactions(
        self,
        user_id: UserId,
        query: str,
        limit: int = 50,
    ) -> list[Transaction]:
        """Full-text search on transactions."""
        with self._uow:
            return self._uow.transactions.search(user_id, query, limit)

    def filter_transactions(
        self,
        user_id: UserId,
        account_id: AccountId | None = None,
        category_id: CategoryId | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        amount_min: Decimal | None = None,
        amount_max: Decimal | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Transaction]:
        """Filter transactions by various criteria."""
        with self._uow:
            return self._uow.transactions.filter(
                user_id=user_id,
                account_id=account_id,
                category_id=category_id,
                date_from=date_from,
                date_to=date_to,
                amount_min=amount_min,
                amount_max=amount_max,
                limit=limit,
                offset=offset,
            )

    async def update_transaction_memo(
        self,
        user_id: UserId,
        transaction_id: TransactionId,
        memo: str | None,
    ) -> Transaction | TransactionError:
        """Update transaction memo."""
        with self._uow:
            txn = self._uow.transactions.get(transaction_id)
            if txn is None:
                return TransactionError("NOT_FOUND", "Transaction not found")
            if txn.user_id != user_id:
                return TransactionError(
                    "NOT_OWNED", "Transaction does not belong to user"
                )

            # Cannot modify mirror transactions - must modify source
            if txn.is_mirror:
                return TransactionError(
                    "CANNOT_MODIFY_MIRROR",
                    "Cannot modify mirror transaction. Update the source transaction instead.",
                )

            # Warn if reconciled (per CONTEXT)
            if txn.status == TransactionStatus.RECONCILED:
                # Still allow, but caller should show warning
                pass

            txn.update_memo(memo)
            self._uow.transactions.update(txn)
            self._uow.collect_events(txn.events)
            txn.clear_events()

            # Update mirrors if this is source transaction
            if not txn.is_mirror:
                mirrors = self._uow.transactions.get_mirrors_for_source(transaction_id)
                for mirror in mirrors:
                    mirror.update_memo(memo)
                    self._uow.transactions.update(mirror)

            await self._uow.commit()
            return txn

    async def update_transaction_dates(
        self,
        user_id: UserId,
        transaction_id: TransactionId,
        effective_date: date | None = None,
        posted_date: date | None = None,
    ) -> Transaction | TransactionError:
        """Update transaction dates."""
        with self._uow:
            txn = self._uow.transactions.get(transaction_id)
            if txn is None:
                return TransactionError("NOT_FOUND", "Transaction not found")
            if txn.user_id != user_id:
                return TransactionError(
                    "NOT_OWNED", "Transaction does not belong to user"
                )

            # Cannot modify mirror transactions - must modify source
            if txn.is_mirror:
                return TransactionError(
                    "CANNOT_MODIFY_MIRROR",
                    "Cannot modify mirror transaction. Update the source transaction instead.",
                )

            if effective_date:
                txn.update_effective_date(effective_date)
                # Sync effective date to mirrors (per CONTEXT)
                if not txn.is_mirror:
                    mirrors = self._uow.transactions.get_mirrors_for_source(
                        transaction_id
                    )
                    for mirror in mirrors:
                        mirror.update_effective_date(effective_date)
                        self._uow.transactions.update(mirror)

            if posted_date is not None:
                txn.update_posted_date(posted_date)
                # Posted date is independent on mirrors (per CONTEXT)

            self._uow.transactions.update(txn)
            self._uow.collect_events(txn.events)
            txn.clear_events()
            await self._uow.commit()

            return txn

    async def update_transaction_splits(
        self,
        user_id: UserId,
        transaction_id: TransactionId,
        new_splits: list[SplitLine],
        new_amount: Money,
    ) -> Transaction | TransactionError:
        """Update transaction splits and amount.

        This is the primary way to change the financial allocations of a transaction.
        Handles:
        - Validating new splits sum to new amount
        - Validating all category/account references
        - Updating mirror transactions for transfer splits (create/update/delete as needed)
        - Cannot update mirror transactions directly (must update source)

        Args:
            user_id: User making the request
            transaction_id: Transaction to update
            new_splits: New list of splits (replaces existing)
            new_amount: New transaction amount (must equal sum of splits)

        Returns:
            Updated Transaction or TransactionError
        """
        with self._uow:
            txn = self._uow.transactions.get(transaction_id)
            if txn is None:
                return TransactionError("NOT_FOUND", "Transaction not found")
            if txn.user_id != user_id:
                return TransactionError(
                    "NOT_OWNED", "Transaction does not belong to user"
                )

            # Cannot update mirror transactions - must update source
            if txn.is_mirror:
                return TransactionError(
                    "CANNOT_UPDATE_MIRROR",
                    "Cannot update splits on mirror transaction. Update the source transaction instead.",
                )

            # Warn if reconciled (per CONTEXT)
            if txn.status == TransactionStatus.RECONCILED:
                # Still allow, but caller should show warning
                pass

            # Validate new splits
            if not new_splits:
                return TransactionError(
                    "NO_SPLITS", "Transaction must have at least one split"
                )
            valid, msg = self._validate_splits(
                user_id, txn.account_id, new_splits, new_amount
            )
            if not valid:
                return TransactionError("INVALID_SPLITS", msg or "Invalid splits")

            # Store old splits for mirror sync
            old_splits = list(txn.splits)

            # Update the transaction
            try:
                txn.update_splits(new_splits, new_amount)
            except ValueError as e:
                return TransactionError("VALIDATION_ERROR", str(e))

            self._uow.transactions.update(txn)
            self._uow.collect_events(txn.events)
            txn.clear_events()

            # Sync mirror transactions
            self._sync_mirrors_for_split_update(txn, old_splits, new_splits)

            await self._uow.commit()

            return txn

    async def mark_transaction_cleared(
        self,
        user_id: UserId,
        transaction_id: TransactionId,
        posted_date: date | None = None,
    ) -> Transaction | TransactionError:
        """Mark transaction as cleared."""
        with self._uow:
            txn = self._uow.transactions.get(transaction_id)
            if txn is None:
                return TransactionError("NOT_FOUND", "Transaction not found")
            if txn.user_id != user_id:
                return TransactionError(
                    "NOT_OWNED", "Transaction does not belong to user"
                )

            try:
                txn.mark_cleared(posted_date)
            except ValueError as e:
                return TransactionError("STATUS_ERROR", str(e))

            self._uow.transactions.update(txn)
            self._uow.collect_events(txn.events)
            txn.clear_events()
            await self._uow.commit()

            return txn

    async def mark_transaction_reconciled(
        self,
        user_id: UserId,
        transaction_id: TransactionId,
    ) -> Transaction | TransactionError:
        """Mark transaction as reconciled."""
        with self._uow:
            txn = self._uow.transactions.get(transaction_id)
            if txn is None:
                return TransactionError("NOT_FOUND", "Transaction not found")
            if txn.user_id != user_id:
                return TransactionError(
                    "NOT_OWNED", "Transaction does not belong to user"
                )

            try:
                txn.mark_reconciled()
            except ValueError as e:
                return TransactionError("INVALID_STATUS_TRANSITION", str(e))

            self._uow.transactions.update(txn)
            self._uow.collect_events(txn.events)
            txn.clear_events()
            await self._uow.commit()

            return txn

    async def delete_transaction(
        self,
        user_id: UserId,
        transaction_id: TransactionId,
    ) -> bool | TransactionError:
        """Delete a transaction.

        Per CONTEXT: Deleting a source transaction deletes its mirrors.
        Deleting a mirror is not allowed (must delete source).
        """
        with self._uow:
            txn = self._uow.transactions.get(transaction_id)
            if txn is None:
                return TransactionError("NOT_FOUND", "Transaction not found")
            if txn.user_id != user_id:
                return TransactionError(
                    "NOT_OWNED", "Transaction does not belong to user"
                )

            if txn.is_mirror:
                return TransactionError(
                    "CANNOT_DELETE_MIRROR",
                    "Cannot delete mirror transaction. Delete the source transaction instead.",
                )

            # Delete mirrors first
            mirrors = self._uow.transactions.get_mirrors_for_source(transaction_id)
            for mirror in mirrors:
                self._uow.collect_events(
                    [
                        MirrorTransactionDeleted(
                            aggregate_id=str(mirror.id),
                            aggregate_type="Transaction",
                            source_transaction_id=str(transaction_id),
                            mirror_transaction_id=str(mirror.id),
                        )
                    ]
                )
                self._uow.transactions.delete(mirror.id)

            # Delete source transaction
            txn.delete()
            self._uow.collect_events(txn.events)
            self._uow.transactions.delete(transaction_id)
            await self._uow.commit()

            return True
