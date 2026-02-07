"""SQLAlchemy implementation of TransactionRepository.

Handles persistence of Transaction aggregate with SplitLine value objects.
Money value objects are stored as primitive columns and reconstructed on load.
"""

from datetime import date
from decimal import Decimal

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from src.adapters.persistence.orm.tables import split_lines, transactions
from domain.model.entity_id import (
    AccountId,
    CategoryId,
    HouseholdId,
    PayeeId,
    SplitId,
    TransactionId,
    UserId,
)
from domain.model.money import Money
from domain.model.split_line import SplitLine
from domain.model.transaction import Transaction
from domain.model.transaction_types import TransactionSource, TransactionStatus


class SqlAlchemyTransactionRepository:
    """SQLAlchemy implementation of TransactionRepository.

    Handles Transaction aggregate with manual SplitLine loading/saving.
    SplitLine is a frozen dataclass with Money value object, so it cannot
    be mapped directly by SQLAlchemy.
    """

    def __init__(self, session: Session) -> None:
        """Initialize repository with SQLAlchemy session.

        Args:
            session: Active SQLAlchemy session for database operations.
        """
        self._session = session

    def _load_splits(self, transaction_id: TransactionId) -> list[SplitLine]:
        """Load and reconstruct SplitLine entities for a transaction.

        Args:
            transaction_id: The transaction identifier.

        Returns:
            List of SplitLine entities ordered by sort_order.
        """
        stmt = (
            select(split_lines)
            .where(split_lines.c.transaction_id == str(transaction_id))
            .order_by(split_lines.c.sort_order)
        )
        rows = self._session.execute(stmt).fetchall()

        result = []
        for row in rows:
            amount = Money(row.amount, row.currency)
            category_id = (
                CategoryId.from_string(row.category_id) if row.category_id else None
            )
            transfer_account_id = (
                AccountId.from_string(row.transfer_account_id)
                if row.transfer_account_id
                else None
            )

            # Load SplitId from database
            split = SplitLine(
                id=SplitId.from_string(row.split_id),
                amount=amount,
                category_id=category_id,
                transfer_account_id=transfer_account_id,
                memo=row.memo,
            )
            result.append(split)
        return result

    def _save_splits(self, transaction: Transaction) -> None:
        """Save split lines for a transaction.

        Deletes existing splits and inserts new ones.

        Args:
            transaction: Transaction with splits to save.
        """
        # Delete existing splits
        delete_stmt = split_lines.delete().where(
            split_lines.c.transaction_id == str(transaction.id)
        )
        self._session.execute(delete_stmt)

        # Insert new splits
        for i, split in enumerate(transaction.splits):
            insert_stmt = split_lines.insert().values(
                split_id=str(split.id),
                transaction_id=str(transaction.id),
                amount=split.amount.amount,
                currency=split.amount.currency,
                category_id=str(split.category_id) if split.category_id else None,
                transfer_account_id=(
                    str(split.transfer_account_id)
                    if split.transfer_account_id
                    else None
                ),
                memo=split.memo,
                sort_order=i,
            )
            self._session.execute(insert_stmt)

    def _hydrate_transaction(self, txn: Transaction) -> Transaction:
        """Hydrate transaction with splits and Money amount.

        Args:
            txn: Transaction entity loaded from database.

        Returns:
            Fully hydrated Transaction with reconstructed value objects.
        """
        # Reconstruct entity IDs
        self._reconstruct_value_objects(txn)

        # Load splits
        object.__setattr__(txn, "splits", self._load_splits(txn.id))

        # Reconstruct amount from database
        stmt = select(transactions.c.amount, transactions.c.currency).where(
            transactions.c.id == str(txn.id)
        )
        row = self._session.execute(stmt).fetchone()
        if row:
            object.__setattr__(txn, "amount", Money(row.amount, row.currency))

        return txn

    def _reconstruct_value_objects(self, txn: Transaction) -> None:
        """Reconstruct value objects from database primitives.

        Args:
            txn: Transaction entity loaded from database.
        """
        # Reconstruct TransactionId from string
        if isinstance(txn.id, str):
            object.__setattr__(txn, "id", TransactionId.from_string(txn.id))

        # Reconstruct UserId from string
        if isinstance(txn.user_id, str):
            object.__setattr__(txn, "user_id", UserId.from_string(txn.user_id))

        # Reconstruct HouseholdId from string
        if hasattr(txn, "household_id") and isinstance(txn.household_id, str):
            object.__setattr__(
                txn, "household_id", HouseholdId.from_string(txn.household_id)
            )

        # Reconstruct AccountId from string
        if isinstance(txn.account_id, str):
            object.__setattr__(txn, "account_id", AccountId.from_string(txn.account_id))

        # Reconstruct PayeeId from string
        if txn.payee_id is not None and isinstance(txn.payee_id, str):
            object.__setattr__(txn, "payee_id", PayeeId.from_string(txn.payee_id))

        # Reconstruct source_transaction_id from string
        if txn.source_transaction_id is not None and isinstance(
            txn.source_transaction_id, str
        ):
            object.__setattr__(
                txn,
                "source_transaction_id",
                TransactionId.from_string(txn.source_transaction_id),
            )

        # Reconstruct source_split_id from string
        if txn.source_split_id is not None and isinstance(txn.source_split_id, str):
            object.__setattr__(
                txn, "source_split_id", SplitId.from_string(txn.source_split_id)
            )

        # Reconstruct enums from string values
        if isinstance(txn.status, str):
            object.__setattr__(txn, "status", TransactionStatus(txn.status))
        if isinstance(txn.source, str):
            object.__setattr__(txn, "source", TransactionSource(txn.source))

        # Ensure _events list exists (transient field, not loaded from DB)
        if not hasattr(txn, "_events") or getattr(txn, "_events", None) is None:
            object.__setattr__(txn, "_events", [])

    def _update_search_vector(self, transaction: Transaction) -> None:
        """Update full-text search vector.

        Args:
            transaction: Transaction with payee_name and memo.
        """
        searchable = " ".join(filter(None, [transaction.payee_name, transaction.memo]))
        if searchable:
            update_stmt = (
                transactions.update()
                .where(transactions.c.id == str(transaction.id))
                .values(search_vector=func.to_tsvector("english", searchable))
            )
            self._session.execute(update_stmt)

    def add(self, transaction: Transaction) -> None:
        """Add a new transaction with its splits.

        Args:
            transaction: Transaction aggregate to persist.
        """
        # Insert the transaction using raw SQL (to include amount)
        insert_stmt = transactions.insert().values(
            id=str(transaction.id),
            user_id=str(transaction.user_id),
            household_id=str(transaction.household_id),
            account_id=str(transaction.account_id),
            effective_date=transaction.effective_date,
            posted_date=transaction.posted_date,
            amount=transaction.amount.amount,
            currency=transaction.amount.currency,
            status=transaction.status.value,
            source=transaction.source.value,
            payee_id=str(transaction.payee_id) if transaction.payee_id else None,
            payee_name=transaction.payee_name,
            memo=transaction.memo,
            check_number=transaction.check_number,
            source_transaction_id=(
                str(transaction.source_transaction_id)
                if transaction.source_transaction_id
                else None
            ),
            source_split_id=(
                str(transaction.source_split_id)
                if transaction.source_split_id
                else None
            ),
            is_mirror=transaction.is_mirror,
            created_at=transaction.created_at,
            updated_at=transaction.updated_at,
        )
        self._session.execute(insert_stmt)

        # Save splits
        self._save_splits(transaction)

        # Update search vector
        self._update_search_vector(transaction)

    def get(self, transaction_id: TransactionId) -> Transaction | None:
        """Get transaction by ID with hydrated splits.

        Args:
            transaction_id: The transaction identifier.

        Returns:
            Transaction aggregate or None if not found.
        """
        txn = self._session.get(Transaction, str(transaction_id))
        if txn:
            return self._hydrate_transaction(txn)
        return None

    def get_by_account(
        self,
        account_id: AccountId,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Transaction]:
        """Get transactions for an account.

        Args:
            account_id: The account identifier.
            limit: Maximum number of results.
            offset: Number of results to skip.

        Returns:
            List of Transaction aggregates ordered by effective_date descending.
        """
        stmt = (
            select(Transaction)
            .where(Transaction.account_id == str(account_id))
            .order_by(Transaction.effective_date.desc())
            .limit(limit)
            .offset(offset)
        )
        result = self._session.execute(stmt)
        txns = list(result.scalars().all())
        return [self._hydrate_transaction(t) for t in txns]

    def get_by_user(
        self,
        user_id: UserId,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Transaction]:
        """Get all transactions for a user.

        Args:
            user_id: The user identifier.
            limit: Maximum number of results.
            offset: Number of results to skip.

        Returns:
            List of Transaction aggregates ordered by effective_date descending.
        """
        stmt = (
            select(Transaction)
            .where(Transaction.user_id == str(user_id))
            .order_by(Transaction.effective_date.desc())
            .limit(limit)
            .offset(offset)
        )
        result = self._session.execute(stmt)
        txns = list(result.scalars().all())
        return [self._hydrate_transaction(t) for t in txns]

    def get_mirrors_for_source(
        self,
        source_transaction_id: TransactionId,
    ) -> list[Transaction]:
        """Get mirror transactions for a source transaction.

        Args:
            source_transaction_id: The source transaction identifier.

        Returns:
            List of mirror Transaction aggregates.
        """
        stmt = select(Transaction).where(
            Transaction.source_transaction_id == str(source_transaction_id)
        )
        result = self._session.execute(stmt)
        txns = list(result.scalars().all())
        return [self._hydrate_transaction(t) for t in txns]

    def search(
        self,
        user_id: UserId,
        query: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Transaction]:
        """Full-text search on payee and memo.

        Args:
            user_id: The user identifier.
            query: Search query string.
            limit: Maximum number of results.
            offset: Number of results to skip.

        Returns:
            List of matching Transaction aggregates.
        """
        ts_query = func.plainto_tsquery("english", query)
        stmt = (
            select(Transaction)
            .where(Transaction.user_id == str(user_id))
            .where(transactions.c.search_vector.op("@@")(ts_query))
            .order_by(Transaction.effective_date.desc())
            .limit(limit)
            .offset(offset)
        )
        result = self._session.execute(stmt)
        txns = list(result.scalars().all())
        return [self._hydrate_transaction(t) for t in txns]

    def filter(
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
        """Filter transactions by various criteria.

        Args:
            user_id: The user identifier.
            account_id: Optional filter by account.
            category_id: Optional filter by category (via split lines).
            date_from: Optional minimum effective date.
            date_to: Optional maximum effective date.
            amount_min: Optional minimum amount.
            amount_max: Optional maximum amount.
            limit: Maximum number of results.
            offset: Number of results to skip.

        Returns:
            List of matching Transaction aggregates.
        """
        conditions = [Transaction.user_id == str(user_id)]

        if account_id:
            conditions.append(Transaction.account_id == str(account_id))
        if date_from:
            conditions.append(Transaction.effective_date >= date_from)
        if date_to:
            conditions.append(Transaction.effective_date <= date_to)
        if amount_min is not None:
            conditions.append(transactions.c.amount >= amount_min)
        if amount_max is not None:
            conditions.append(transactions.c.amount <= amount_max)

        # If filtering by category, need to join with split_lines
        if category_id:
            stmt = (
                select(Transaction)
                .join(split_lines, split_lines.c.transaction_id == transactions.c.id)
                .where(and_(*conditions))
                .where(split_lines.c.category_id == str(category_id))
                .distinct()
                .order_by(Transaction.effective_date.desc())
                .limit(limit)
                .offset(offset)
            )
        else:
            stmt = (
                select(Transaction)
                .where(and_(*conditions))
                .order_by(Transaction.effective_date.desc())
                .limit(limit)
                .offset(offset)
            )

        result = self._session.execute(stmt)
        txns = list(result.scalars().all())
        return [self._hydrate_transaction(t) for t in txns]

    def count_by_account(self, account_id: AccountId) -> int:
        """Count transactions for an account.

        Used for deletion validation - prevents deleting accounts with transactions.

        Args:
            account_id: The account identifier.

        Returns:
            Number of transactions for the account.
        """
        stmt = (
            select(func.count())
            .select_from(transactions)
            .where(transactions.c.account_id == str(account_id))
        )
        return self._session.scalar(stmt) or 0

    def update(self, transaction: Transaction) -> None:
        """Update transaction and its splits.

        Args:
            transaction: Transaction aggregate with updates.
        """
        update_stmt = (
            transactions.update()
            .where(transactions.c.id == str(transaction.id))
            .values(
                effective_date=transaction.effective_date,
                posted_date=transaction.posted_date,
                amount=transaction.amount.amount,
                currency=transaction.amount.currency,
                status=transaction.status.value,
                payee_id=str(transaction.payee_id) if transaction.payee_id else None,
                payee_name=transaction.payee_name,
                memo=transaction.memo,
                check_number=transaction.check_number,
                updated_at=transaction.updated_at,
            )
        )
        self._session.execute(update_stmt)

        # Update splits
        self._save_splits(transaction)

        # Update search vector
        self._update_search_vector(transaction)

    def delete(self, transaction_id: TransactionId) -> None:
        """Delete a transaction.

        Split lines are deleted automatically via CASCADE.

        Args:
            transaction_id: The transaction identifier to delete.
        """
        # Expunge any loaded transaction from session to prevent StaleDataError
        txn = self._session.get(Transaction, str(transaction_id))
        if txn:
            self._session.expunge(txn)

        delete_stmt = transactions.delete().where(
            transactions.c.id == str(transaction_id)
        )
        self._session.execute(delete_stmt)
