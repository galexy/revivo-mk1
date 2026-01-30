# Phase 3: Transaction Domain - Research

**Researched:** 2026-01-30
**Domain:** Double-Entry Accounting, Transaction Modeling, File Attachments, DDD Aggregate Design
**Confidence:** HIGH

## Summary

This research covers the design patterns and implementation strategies for building the Transaction domain in a personal finance application. Phase 3 implements double-entry accounting with transaction splits, transfers between accounts, receipt attachments, and comprehensive search/filter capabilities. The phase builds directly on Phase 2's Account aggregate and Phase 1's foundation patterns.

The standard approach for transaction modeling in a double-entry system uses:
- **Transaction aggregate** as the root containing multiple Entry/Leg records
- **Entry pattern** where each Entry links to an account with a signed amount (debits and credits)
- **Split support** via multiple Entries per Transaction allowing category allocation
- **Transfer modeling** as a Transaction with two Entries affecting source and destination accounts
- **Attachment entity** storing file metadata with local filesystem storage (cloud storage deferred)
- **PostgreSQL full-text search** via tsvector for payee/notes search

The codebase already establishes Money value object, EntityId pattern (TransactionId, CategoryId already defined), DomainEvent base, UnitOfWork, and Account aggregate - Phase 3 builds on all these foundations.

**Primary recommendation:** Model transactions using Entry pattern where each Transaction contains 1+ Entries (debits/credits), with entries summing to zero for balanced accounting. Use separate Attachment table with local file storage initially.

## Standard Stack

The established libraries/tools are already in place from Phase 1 and Phase 2:

### Core (Already Installed)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| SQLAlchemy | 2.0.36+ | ORM with imperative mapping | Already configured with Data Mapper pattern |
| Pydantic | 2.10+ | API schema validation | Already in use for DTOs |
| typeid-python | 0.3+ | Prefixed IDs | TransactionId, CategoryId already defined in entity_id.py |
| PostgreSQL | 16+ | Primary database | tsvector for full-text search, ACID for financial data |

### New for Phase 3
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| python-multipart | 0.0.9+ | FastAPI file upload | Required for UploadFile handling |
| aiofiles | 23.2+ | Async file I/O | Writing uploaded files without blocking |

### No Major Dependencies Required
Phase 3 uses existing stack. Only python-multipart and aiofiles needed for file upload support.

**Installation:**
```bash
uv add python-multipart aiofiles
```

## Architecture Patterns

### Recommended Project Structure (Additions to Phase 2)

```
src/
    domain/
        model/
            transaction.py      # Transaction aggregate root
            entry.py            # Entry value object (debit/credit line)
            category.py         # Category entity
            attachment.py       # Attachment entity
            transaction_types.py # TransactionType, EntryType enums
        events/
            transaction_events.py  # TransactionCreated, TransactionUpdated, etc.
        ports/
            transaction_repository.py  # TransactionRepository protocol
            category_repository.py     # CategoryRepository protocol
            attachment_repository.py   # AttachmentRepository protocol
    adapters/
        persistence/
            orm/
                tables.py       # Add transactions, entries, categories, attachments tables
                mappers.py      # Add Transaction, Category, Attachment mappings
            repositories/
                transaction.py  # SqlAlchemyTransactionRepository
                category.py     # SqlAlchemyCategoryRepository
                attachment.py   # SqlAlchemyAttachmentRepository
        api/
            schemas/
                transaction.py  # Transaction request/response schemas
                category.py     # Category schemas
                attachment.py   # Attachment schemas
            routes/
                transactions.py # Transaction CRUD + search/filter endpoints
                categories.py   # Category CRUD endpoints
        storage/
            __init__.py
            file_storage.py     # Local filesystem storage for attachments
    application/
        services/
            transaction_service.py  # Transaction use case orchestration
tests/
    unit/
        domain/
            test_transaction.py
            test_entry.py
            test_category.py
    integration/
        test_transaction_repository.py
        test_transaction_search.py
```

### Pattern 1: Transaction Aggregate with Entry Pattern (Double-Entry)

**What:** Transaction as aggregate root containing multiple Entry records, where entries must sum to zero
**When to use:** All financial transactions - ensures accounting equation balance
**Why this pattern:** Matches double-entry accounting semantics, allows splits and transfers naturally

**Example:**
```python
# src/domain/model/entry.py
from dataclasses import dataclass
from decimal import Decimal

from src.domain.model.entity_id import AccountId, CategoryId
from src.domain.model.money import Money


@dataclass(frozen=True, slots=True)
class Entry:
    """A single debit or credit line within a transaction.

    In double-entry accounting:
    - Positive amount = money INCREASES account's reporting balance
      (debit for assets/expenses, credit for liabilities/equity/income)
    - Negative amount = money DECREASES account's reporting balance

    For a personal finance app simplified model:
    - Positive = money going INTO account (deposit, income)
    - Negative = money going OUT of account (withdrawal, expense)

    All entries in a transaction must sum to zero.
    """
    account_id: AccountId
    amount: Money  # Positive = inflow, Negative = outflow
    category_id: CategoryId | None = None  # Optional category for expense/income
    memo: str | None = None  # Entry-level note

    @property
    def is_debit(self) -> bool:
        """Check if this is a debit (outflow from account)."""
        return self.amount.is_negative()

    @property
    def is_credit(self) -> bool:
        """Check if this is a credit (inflow to account)."""
        return self.amount.is_positive()


# src/domain/model/transaction.py
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from typing import Self

from src.domain.events.base import DomainEvent
from src.domain.events.transaction_events import (
    TransactionCreated,
    TransactionDeleted,
    TransactionUpdated,
)
from src.domain.model.entity_id import AccountId, CategoryId, TransactionId, UserId
from src.domain.model.entry import Entry
from src.domain.model.money import Money
from src.domain.model.transaction_types import TransactionStatus, TransactionType


@dataclass(eq=False)
class Transaction:
    """Transaction aggregate root.

    Represents a financial transaction with one or more entries.
    All entries must sum to zero (double-entry balance).

    Transaction types:
    - EXPENSE: Single entry (outflow from one account, implicit category inflow)
    - INCOME: Single entry (inflow to one account, implicit source outflow)
    - TRANSFER: Two entries (outflow from source, inflow to destination)
    - SPLIT: Multiple entries (outflow from one account, multiple category allocations)
    """
    id: TransactionId
    user_id: UserId
    transaction_type: TransactionType
    status: TransactionStatus

    # Transaction metadata
    date: datetime  # When transaction occurred (user-specified)
    payee: str | None = None  # Who received/sent money
    description: str | None = None  # User notes
    reference_number: str | None = None  # Check number, confirmation code, etc.

    # Entries (the actual debits/credits)
    entries: list[Entry] = field(default_factory=list)

    # Lifecycle
    cleared_at: datetime | None = None  # When transaction cleared/reconciled

    # Audit
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    # Domain events (not persisted directly)
    _events: list[DomainEvent] = field(default_factory=list, repr=False)

    def __post_init__(self) -> None:
        """Validate entries sum to zero on creation."""
        if self.entries:
            self._validate_balance()

    def _validate_balance(self) -> None:
        """Ensure all entries sum to zero (balanced transaction)."""
        if not self.entries:
            return

        # Group by currency
        totals: dict[str, Decimal] = {}
        for entry in self.entries:
            currency = entry.amount.currency
            totals[currency] = totals.get(currency, Decimal("0")) + entry.amount.amount

        for currency, total in totals.items():
            if total != Decimal("0"):
                raise ValueError(
                    f"Transaction is unbalanced: {currency} entries sum to {total}, must be 0"
                )

    @property
    def events(self) -> list[DomainEvent]:
        """Get collected domain events as a copy."""
        return list(self._events)

    def clear_events(self) -> None:
        """Clear collected events after processing."""
        self._events.clear()

    @property
    def primary_account_id(self) -> AccountId | None:
        """Get the primary account (first entry's account)."""
        if self.entries:
            return self.entries[0].account_id
        return None

    @property
    def total_amount(self) -> Money | None:
        """Get the absolute amount of the transaction (outflow side)."""
        for entry in self.entries:
            if entry.amount.is_negative():
                return entry.amount.abs()
        return None

    # --- Factory Methods ---

    @classmethod
    def create_expense(
        cls,
        user_id: UserId,
        account_id: AccountId,
        amount: Money,
        date: datetime,
        category_id: CategoryId | None = None,
        payee: str | None = None,
        description: str | None = None,
    ) -> Self:
        """Create a simple expense transaction.

        Single entry: negative amount (money leaving account).
        For double-entry balance, we conceptually have an implicit
        inflow to the expense category, but for simplicity in
        personal finance we track only the account side.
        """
        if amount.is_negative():
            raise ValueError("Expense amount must be positive (will be stored as negative outflow)")

        # In personal finance app, we simplify: expense is single-entry
        # representing outflow. Category tracks what the expense was for.
        entries = [
            Entry(
                account_id=account_id,
                amount=-amount,  # Negative = outflow
                category_id=category_id,
            )
        ]

        txn = cls(
            id=TransactionId.generate(),
            user_id=user_id,
            transaction_type=TransactionType.EXPENSE,
            status=TransactionStatus.PENDING,
            date=date,
            payee=payee,
            description=description,
            entries=entries,
        )

        txn._events.append(
            TransactionCreated(
                aggregate_id=str(txn.id),
                aggregate_type="Transaction",
                transaction_type=TransactionType.EXPENSE.value,
                amount=str(amount.amount),
                currency=amount.currency,
            )
        )
        return txn

    @classmethod
    def create_income(
        cls,
        user_id: UserId,
        account_id: AccountId,
        amount: Money,
        date: datetime,
        category_id: CategoryId | None = None,
        payee: str | None = None,
        description: str | None = None,
    ) -> Self:
        """Create an income transaction.

        Single entry: positive amount (money entering account).
        """
        if amount.is_negative():
            raise ValueError("Income amount must be positive")

        entries = [
            Entry(
                account_id=account_id,
                amount=amount,  # Positive = inflow
                category_id=category_id,
            )
        ]

        txn = cls(
            id=TransactionId.generate(),
            user_id=user_id,
            transaction_type=TransactionType.INCOME,
            status=TransactionStatus.PENDING,
            date=date,
            payee=payee,
            description=description,
            entries=entries,
        )

        txn._events.append(
            TransactionCreated(
                aggregate_id=str(txn.id),
                aggregate_type="Transaction",
                transaction_type=TransactionType.INCOME.value,
                amount=str(amount.amount),
                currency=amount.currency,
            )
        )
        return txn

    @classmethod
    def create_transfer(
        cls,
        user_id: UserId,
        from_account_id: AccountId,
        to_account_id: AccountId,
        amount: Money,
        date: datetime,
        description: str | None = None,
    ) -> Self:
        """Create a transfer between two accounts.

        Two entries: negative from source, positive to destination.
        Entries sum to zero (balanced).
        """
        if amount.is_negative() or amount.is_zero():
            raise ValueError("Transfer amount must be positive")

        if from_account_id == to_account_id:
            raise ValueError("Cannot transfer to same account")

        entries = [
            Entry(account_id=from_account_id, amount=-amount),  # Outflow
            Entry(account_id=to_account_id, amount=amount),    # Inflow
        ]

        txn = cls(
            id=TransactionId.generate(),
            user_id=user_id,
            transaction_type=TransactionType.TRANSFER,
            status=TransactionStatus.PENDING,
            date=date,
            description=description,
            entries=entries,
        )

        txn._events.append(
            TransactionCreated(
                aggregate_id=str(txn.id),
                aggregate_type="Transaction",
                transaction_type=TransactionType.TRANSFER.value,
                amount=str(amount.amount),
                currency=amount.currency,
            )
        )
        return txn

    @classmethod
    def create_split(
        cls,
        user_id: UserId,
        account_id: AccountId,
        splits: list[tuple[Money, CategoryId | None, str | None]],
        date: datetime,
        payee: str | None = None,
        description: str | None = None,
    ) -> Self:
        """Create a split transaction across multiple categories.

        Args:
            splits: List of (amount, category_id, memo) tuples.
                    All amounts should be positive; they represent outflows.

        Each split becomes a separate Entry with the same account but
        different category. Total represents a single payment split
        across categories (e.g., grocery receipt with food and household items).
        """
        if not splits:
            raise ValueError("Split transaction requires at least one split")

        entries = []
        for amount, category_id, memo in splits:
            if amount.is_negative() or amount.is_zero():
                raise ValueError("Split amounts must be positive")
            entries.append(
                Entry(
                    account_id=account_id,
                    amount=-amount,  # Outflow
                    category_id=category_id,
                    memo=memo,
                )
            )

        txn = cls(
            id=TransactionId.generate(),
            user_id=user_id,
            transaction_type=TransactionType.SPLIT,
            status=TransactionStatus.PENDING,
            date=date,
            payee=payee,
            description=description,
            entries=entries,
        )

        total = sum((s[0].amount for s in splits), Decimal("0"))
        txn._events.append(
            TransactionCreated(
                aggregate_id=str(txn.id),
                aggregate_type="Transaction",
                transaction_type=TransactionType.SPLIT.value,
                amount=str(total),
                currency=splits[0][0].currency,
            )
        )
        return txn

    # --- Mutation Methods ---

    def update_payee(self, new_payee: str | None) -> None:
        """Update transaction payee."""
        old_payee = self.payee
        self.payee = new_payee
        self.updated_at = datetime.now(UTC)
        self._events.append(
            TransactionUpdated(
                aggregate_id=str(self.id),
                aggregate_type="Transaction",
                field="payee",
                old_value=old_payee,
                new_value=new_payee,
            )
        )

    def update_date(self, new_date: datetime) -> None:
        """Update transaction date."""
        old_date = self.date
        self.date = new_date
        self.updated_at = datetime.now(UTC)
        self._events.append(
            TransactionUpdated(
                aggregate_id=str(self.id),
                aggregate_type="Transaction",
                field="date",
                old_value=old_date.isoformat() if old_date else None,
                new_value=new_date.isoformat(),
            )
        )

    def mark_cleared(self) -> None:
        """Mark transaction as cleared/reconciled."""
        if self.status == TransactionStatus.CLEARED:
            raise ValueError("Transaction is already cleared")
        self.status = TransactionStatus.CLEARED
        self.cleared_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)
```

### Pattern 2: Transaction Type Enumerations

**What:** Type-safe string enums for transaction type and status
**When to use:** All transaction classification fields

**Example:**
```python
# src/domain/model/transaction_types.py
from enum import StrEnum, auto


class TransactionType(StrEnum):
    """Types of financial transactions."""
    EXPENSE = auto()    # Money out of account
    INCOME = auto()     # Money into account
    TRANSFER = auto()   # Between two accounts
    SPLIT = auto()      # Single payment split across categories


class TransactionStatus(StrEnum):
    """Transaction lifecycle status."""
    PENDING = auto()    # Not yet cleared
    CLEARED = auto()    # Reconciled with bank
    VOID = auto()       # Cancelled/reversed
```

### Pattern 3: Category Entity

**What:** Simple entity for organizing transactions by type
**When to use:** Expense and income categorization

**Example:**
```python
# src/domain/model/category.py
from dataclasses import dataclass, field
from datetime import UTC, datetime

from src.domain.model.entity_id import CategoryId, UserId


@dataclass(eq=False)
class Category:
    """Category for organizing transactions.

    Categories are user-owned and support hierarchy (parent_id).
    System categories (is_system=True) cannot be deleted.
    """
    id: CategoryId
    user_id: UserId
    name: str
    parent_id: CategoryId | None = None  # For hierarchical categories
    is_system: bool = False  # System-defined categories (Transfer, etc.)
    sort_order: int = 0
    icon: str | None = None  # Optional emoji or icon name

    # Audit
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def update_name(self, new_name: str) -> None:
        """Update category name."""
        if not new_name or not new_name.strip():
            raise ValueError("Category name cannot be empty")
        self.name = new_name.strip()
        self.updated_at = datetime.now(UTC)
```

### Pattern 4: Attachment Entity with File Storage

**What:** Separate entity for file attachments with metadata
**When to use:** Receipt images, documents attached to transactions

**Example:**
```python
# src/domain/model/attachment.py
from dataclasses import dataclass, field
from datetime import UTC, datetime

from src.domain.model.entity_id import TransactionId, UserId


@dataclass(frozen=True, slots=True)
class AttachmentId:
    """Identifier for Attachment entity."""
    value: str

    @classmethod
    def generate(cls) -> "AttachmentId":
        from typeid import TypeID
        tid = TypeID(prefix="att")
        return cls(value=str(tid))

    @classmethod
    def from_string(cls, value: str) -> "AttachmentId":
        from typeid import TypeID
        tid = TypeID.from_string(value)
        if tid.prefix != "att":
            raise ValueError(f"Expected 'att' prefix, got '{tid.prefix}'")
        return cls(value=value)

    def __str__(self) -> str:
        return self.value


@dataclass(eq=False)
class Attachment:
    """File attachment for a transaction.

    Stores metadata about uploaded files (receipts, documents).
    Actual files stored on filesystem; path is relative to upload directory.
    """
    id: AttachmentId
    transaction_id: TransactionId
    user_id: UserId

    # File metadata
    filename: str  # Original filename from upload
    storage_path: str  # Path relative to upload directory
    content_type: str  # MIME type
    size_bytes: int

    # Audit
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @classmethod
    def create(
        cls,
        transaction_id: TransactionId,
        user_id: UserId,
        filename: str,
        storage_path: str,
        content_type: str,
        size_bytes: int,
    ) -> "Attachment":
        """Create a new attachment."""
        return cls(
            id=AttachmentId.generate(),
            transaction_id=transaction_id,
            user_id=user_id,
            filename=filename,
            storage_path=storage_path,
            content_type=content_type,
            size_bytes=size_bytes,
        )
```

### Pattern 5: File Storage Adapter

**What:** Simple local filesystem storage for attachments
**When to use:** All file upload operations

**Example:**
```python
# src/adapters/storage/file_storage.py
import os
import uuid
from pathlib import Path
from typing import BinaryIO

import aiofiles


class LocalFileStorage:
    """Local filesystem storage for attachments.

    Files stored as: {upload_dir}/{user_id}/{uuid}.{extension}
    """

    def __init__(self, upload_dir: str):
        self._upload_dir = Path(upload_dir)
        self._upload_dir.mkdir(parents=True, exist_ok=True)

    async def save(
        self,
        file: BinaryIO,
        user_id: str,
        original_filename: str,
    ) -> str:
        """Save file and return storage path (relative to upload_dir).

        Args:
            file: File-like object to save
            user_id: User who owns the file
            original_filename: Original filename for extension

        Returns:
            Relative path where file was saved
        """
        # Create user directory
        user_dir = self._upload_dir / user_id
        user_dir.mkdir(exist_ok=True)

        # Generate unique filename preserving extension
        ext = Path(original_filename).suffix.lower()
        unique_name = f"{uuid.uuid4()}{ext}"

        # Save file
        file_path = user_dir / unique_name
        async with aiofiles.open(file_path, "wb") as f:
            content = file.read()
            await f.write(content)

        # Return relative path
        return f"{user_id}/{unique_name}"

    def get_full_path(self, storage_path: str) -> Path:
        """Get full filesystem path for a storage path."""
        return self._upload_dir / storage_path

    def delete(self, storage_path: str) -> None:
        """Delete a file by storage path."""
        full_path = self.get_full_path(storage_path)
        if full_path.exists():
            full_path.unlink()
```

### Pattern 6: PostgreSQL Full-Text Search for Transactions

**What:** Use PostgreSQL tsvector for searching transactions by payee/description
**When to use:** Transaction search functionality (TRAN-09)

**Example:**
```python
# In tables.py - Add search vector column
from sqlalchemy import Column, Index, func
from sqlalchemy.dialects.postgresql import TSVECTOR

transactions = Table(
    "transactions",
    metadata,
    # ... other columns ...
    Column("search_vector", TSVECTOR),  # Full-text search vector

    # GIN index for fast full-text search
    Index(
        "ix_transactions_search",
        "search_vector",
        postgresql_using="gin",
    ),
)

# In repository - Search implementation
class SqlAlchemyTransactionRepository:
    def search(
        self,
        user_id: UserId,
        query: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Transaction]:
        """Full-text search on payee and description."""
        from sqlalchemy import func

        # plainto_tsquery handles user input safely
        ts_query = func.plainto_tsquery("english", query)

        stmt = (
            select(Transaction)
            .where(Transaction.user_id == str(user_id))
            .where(
                func.to_tsvector("english",
                    func.coalesce(Transaction.payee, "") + " " +
                    func.coalesce(Transaction.description, "")
                ).op("@@")(ts_query)
            )
            .order_by(Transaction.date.desc())
            .limit(limit)
            .offset(offset)
        )

        result = self._session.execute(stmt)
        return list(result.scalars().all())
```

### Pattern 7: Transaction Filtering

**What:** Repository methods for filtering transactions by multiple criteria
**When to use:** Transaction list views (TRAN-09, TRAN-10, TRAN-11)

**Example:**
```python
# src/adapters/persistence/repositories/transaction.py
from datetime import datetime
from decimal import Decimal

class SqlAlchemyTransactionRepository:
    def get_filtered(
        self,
        user_id: UserId,
        account_id: AccountId | None = None,
        category_id: CategoryId | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        amount_min: Decimal | None = None,
        amount_max: Decimal | None = None,
        payee_contains: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Transaction]:
        """Get transactions with multiple filter criteria."""
        from sqlalchemy import and_, or_

        stmt = select(Transaction).where(Transaction.user_id == str(user_id))

        # Filter by account (check entries)
        if account_id:
            # Join with entries and filter
            stmt = stmt.join(entries_table).where(
                entries_table.c.account_id == str(account_id)
            )

        # Filter by category (check entries)
        if category_id:
            stmt = stmt.join(entries_table).where(
                entries_table.c.category_id == str(category_id)
            )

        # Date range filter
        if date_from:
            stmt = stmt.where(Transaction.date >= date_from)
        if date_to:
            stmt = stmt.where(Transaction.date <= date_to)

        # Payee contains (case-insensitive)
        if payee_contains:
            stmt = stmt.where(
                Transaction.payee.ilike(f"%{payee_contains}%")
            )

        # Order by date descending (newest first)
        stmt = stmt.order_by(Transaction.date.desc())
        stmt = stmt.limit(limit).offset(offset)

        result = self._session.execute(stmt)
        transactions = list(result.scalars().unique().all())

        for txn in transactions:
            self._reconstruct_value_objects(txn)

        return transactions
```

### Anti-Patterns to Avoid

- **Storing balance on Account:** Balance should be calculated from transaction entries. Cached balance leads to inconsistency.
- **Single-entry transactions:** Even simple expenses should fit the Entry pattern for consistency.
- **Floating-point amounts:** Always use Decimal via Money value object.
- **Storing full file paths:** Store relative paths, construct full paths at runtime.
- **Generic category ID (no validation):** Validate category belongs to user.
- **Transactions without user_id:** All transactions must be scoped to a user.
- **Direct SQL for search:** Use PostgreSQL tsvector, not LIKE '%query%' patterns.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Transaction amounts | Custom amount class | Money from money.py | Already handles precision, currency |
| Transaction IDs | String concatenation | TransactionId from entity_id.py | Already implemented |
| Category IDs | String concatenation | CategoryId from entity_id.py | Already implemented |
| Full-text search | SQL LIKE queries | PostgreSQL tsvector | Proper tokenization, stemming, ranking |
| File upload handling | Manual multipart parsing | FastAPI UploadFile | Built-in validation, streaming |
| Date range queries | String parsing | datetime objects | Type safety, timezone handling |
| Event collection | Manual list management | _events pattern + UoW | Already established in Phase 1-2 |

**Key insight:** Phase 1 and Phase 2 established all foundation patterns. Phase 3 should compose existing building blocks (Money, EntityId, UoW, Events) and add transaction-specific domain logic.

## Common Pitfalls

### Pitfall 1: Unbalanced Double-Entry Transactions

**What goes wrong:** Entries don't sum to zero, accounting equation violated
**Why it happens:** Forgetting to validate in factory methods or allowing direct entry manipulation
**How to avoid:** Validate in __post_init__ and all mutation methods; entries list should be immutable after creation
**Warning signs:** Account balances don't match expected values, reports don't reconcile

### Pitfall 2: Transfer Modeling as Two Separate Transactions

**What goes wrong:** Transfer appears as two unrelated transactions, hard to track
**Why it happens:** Simpler initial implementation
**How to avoid:** Model transfer as single Transaction with two entries (source outflow, destination inflow)
**Warning signs:** Difficulty matching transfer pairs, doubled transaction counts

### Pitfall 3: Missing Category Validation

**What goes wrong:** Category from another user assigned to transaction
**Why it happens:** No ownership check when creating/updating transaction
**How to avoid:** Application service validates category.user_id == transaction.user_id
**Warning signs:** Security bugs, users seeing other users' categories

### Pitfall 4: Large File Uploads Blocking Event Loop

**What goes wrong:** Synchronous file writes block async FastAPI
**Why it happens:** Using regular file.write() instead of async
**How to avoid:** Use aiofiles for async file operations
**Warning signs:** High latency during uploads, timeout errors

### Pitfall 5: Full-Text Search Without Index

**What goes wrong:** Search becomes slow as transactions grow
**Why it happens:** Using LIKE '%query%' instead of tsvector
**How to avoid:** Create GIN index on tsvector column, use to_tsquery
**Warning signs:** Slow search, queries scanning full table

### Pitfall 6: Not Handling Negative Balance Prevention

**What goes wrong:** Account goes negative when it shouldn't (TRAN-14)
**Why it happens:** No balance check before committing transaction
**How to avoid:** Application service calculates projected balance before allowing expense/withdrawal
**Warning signs:** Negative balances on checking accounts without overdraft

### Pitfall 7: Attachment Orphans After Transaction Delete

**What goes wrong:** Files remain on disk after transaction deleted
**Why it happens:** No cascade delete, no cleanup job
**How to avoid:** Delete attachments in same unit of work as transaction; or background cleanup job
**Warning signs:** Storage usage growing, orphan files on disk

### Pitfall 8: Split Transaction with Inconsistent Totals

**What goes wrong:** Split amounts don't match receipt total
**Why it happens:** No validation that splits sum to expected total
**How to avoid:** Optionally accept expected_total parameter and validate sum matches
**Warning signs:** Discrepancies in category spending reports

## Code Examples

### Transaction Domain Events

```python
# src/domain/events/transaction_events.py
from dataclasses import dataclass

from src.domain.events.base import DomainEvent


@dataclass(frozen=True)
class TransactionCreated(DomainEvent):
    """Emitted when a new transaction is created."""
    transaction_type: str
    amount: str
    currency: str


@dataclass(frozen=True)
class TransactionUpdated(DomainEvent):
    """Emitted when transaction properties change."""
    field: str
    old_value: str | None
    new_value: str | None


@dataclass(frozen=True)
class TransactionDeleted(DomainEvent):
    """Emitted when a transaction is deleted."""
    pass


@dataclass(frozen=True)
class AttachmentAdded(DomainEvent):
    """Emitted when an attachment is added to a transaction."""
    attachment_id: str
    filename: str


@dataclass(frozen=True)
class AttachmentRemoved(DomainEvent):
    """Emitted when an attachment is removed from a transaction."""
    attachment_id: str
```

### Transaction Service (Application Layer)

```python
# src/application/services/transaction_service.py
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import BinaryIO

from src.domain.model.entity_id import AccountId, CategoryId, TransactionId, UserId
from src.domain.model.money import Money
from src.domain.model.transaction import Transaction


@dataclass(frozen=True, slots=True)
class TransactionError:
    """Error result for transaction operations."""
    code: str
    message: str


class TransactionService:
    """Application service for transaction use cases."""

    def __init__(self, uow, file_storage):
        self._uow = uow
        self._file_storage = file_storage

    def create_expense(
        self,
        user_id: UserId,
        account_id: AccountId,
        amount: Money,
        date: datetime,
        category_id: CategoryId | None = None,
        payee: str | None = None,
        description: str | None = None,
    ) -> Transaction | TransactionError:
        """Create an expense transaction."""
        with self._uow:
            # Validate account exists and belongs to user
            account = self._uow.accounts.get(account_id)
            if account is None:
                return TransactionError("ACCOUNT_NOT_FOUND", f"Account {account_id} not found")
            if account.user_id != user_id:
                return TransactionError("ACCOUNT_NOT_OWNED", "Account does not belong to user")

            # Validate category if provided
            if category_id:
                category = self._uow.categories.get(category_id)
                if category is None:
                    return TransactionError("CATEGORY_NOT_FOUND", f"Category {category_id} not found")
                if category.user_id != user_id:
                    return TransactionError("CATEGORY_NOT_OWNED", "Category does not belong to user")

            # Check if expense would cause negative balance (TRAN-14)
            # For accounts that don't allow negative balances
            if not self._can_account_go_negative(account):
                current_balance = self._calculate_account_balance(account_id)
                if current_balance - amount < Money(Decimal("0"), amount.currency):
                    return TransactionError(
                        "INSUFFICIENT_BALANCE",
                        f"Expense would result in negative balance"
                    )

            # Create transaction
            txn = Transaction.create_expense(
                user_id=user_id,
                account_id=account_id,
                amount=amount,
                date=date,
                category_id=category_id,
                payee=payee,
                description=description,
            )

            self._uow.transactions.add(txn)
            self._uow.collect_events(txn.events)
            txn.clear_events()
            self._uow.commit()

            return txn

    def create_transfer(
        self,
        user_id: UserId,
        from_account_id: AccountId,
        to_account_id: AccountId,
        amount: Money,
        date: datetime,
        description: str | None = None,
    ) -> Transaction | TransactionError:
        """Create a transfer between two accounts."""
        with self._uow:
            # Validate both accounts exist and belong to user
            from_account = self._uow.accounts.get(from_account_id)
            to_account = self._uow.accounts.get(to_account_id)

            if from_account is None:
                return TransactionError("ACCOUNT_NOT_FOUND", f"Source account {from_account_id} not found")
            if to_account is None:
                return TransactionError("ACCOUNT_NOT_FOUND", f"Destination account {to_account_id} not found")
            if from_account.user_id != user_id or to_account.user_id != user_id:
                return TransactionError("ACCOUNT_NOT_OWNED", "Accounts do not belong to user")

            # Check balance
            if not self._can_account_go_negative(from_account):
                current_balance = self._calculate_account_balance(from_account_id)
                if current_balance - amount < Money(Decimal("0"), amount.currency):
                    return TransactionError(
                        "INSUFFICIENT_BALANCE",
                        f"Transfer would result in negative balance in source account"
                    )

            txn = Transaction.create_transfer(
                user_id=user_id,
                from_account_id=from_account_id,
                to_account_id=to_account_id,
                amount=amount,
                date=date,
                description=description,
            )

            self._uow.transactions.add(txn)
            self._uow.collect_events(txn.events)
            txn.clear_events()
            self._uow.commit()

            return txn

    async def add_attachment(
        self,
        transaction_id: TransactionId,
        user_id: UserId,
        file: BinaryIO,
        filename: str,
        content_type: str,
        size_bytes: int,
    ) -> "Attachment | TransactionError":
        """Add an attachment to a transaction."""
        from src.domain.model.attachment import Attachment

        with self._uow:
            txn = self._uow.transactions.get(transaction_id)
            if txn is None:
                return TransactionError("TRANSACTION_NOT_FOUND", f"Transaction {transaction_id} not found")
            if txn.user_id != user_id:
                return TransactionError("TRANSACTION_NOT_OWNED", "Transaction does not belong to user")

            # Save file to storage
            storage_path = await self._file_storage.save(file, str(user_id), filename)

            # Create attachment record
            attachment = Attachment.create(
                transaction_id=transaction_id,
                user_id=user_id,
                filename=filename,
                storage_path=storage_path,
                content_type=content_type,
                size_bytes=size_bytes,
            )

            self._uow.attachments.add(attachment)
            self._uow.commit()

            return attachment

    def _can_account_go_negative(self, account) -> bool:
        """Check if account type allows negative balance."""
        from src.domain.model.account_types import AccountType

        # Credit cards and loans naturally have negative balances (owed money)
        # Checking/savings should not go negative
        return account.account_type in {
            AccountType.CREDIT_CARD,
            AccountType.LOAN,
        }

    def _calculate_account_balance(self, account_id: AccountId) -> Money:
        """Calculate current balance from opening balance + all entries."""
        account = self._uow.accounts.get_or_raise(account_id)
        opening = account.opening_balance

        # Sum all entries for this account
        entries_sum = self._uow.transactions.sum_entries_for_account(account_id)

        return opening + entries_sum
```

### Pydantic API Schemas

```python
# src/adapters/api/schemas/transaction.py
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field

from src.adapters.api.schemas.account import MoneySchema
from src.domain.model.transaction_types import TransactionStatus, TransactionType


class EntrySchema(BaseModel):
    """Schema for transaction entry."""
    account_id: str
    amount: MoneySchema
    category_id: str | None = None
    memo: str | None = None


class CreateExpenseRequest(BaseModel):
    """Request to create an expense transaction."""
    account_id: str = Field(..., description="Account ID for the expense")
    amount: MoneySchema = Field(..., description="Expense amount (positive)")
    date: datetime = Field(..., description="Transaction date")
    category_id: str | None = Field(default=None, description="Category for the expense")
    payee: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=2000)


class CreateTransferRequest(BaseModel):
    """Request to create a transfer between accounts."""
    from_account_id: str
    to_account_id: str
    amount: MoneySchema
    date: datetime
    description: str | None = Field(default=None, max_length=2000)


class SplitItem(BaseModel):
    """A single item in a split transaction."""
    amount: MoneySchema
    category_id: str | None = None
    memo: str | None = Field(default=None, max_length=500)


class CreateSplitRequest(BaseModel):
    """Request to create a split transaction."""
    account_id: str
    splits: list[SplitItem] = Field(..., min_length=1)
    date: datetime
    payee: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=2000)


class TransactionResponse(BaseModel):
    """Response schema for a single transaction."""
    id: str
    user_id: str
    transaction_type: TransactionType
    status: TransactionStatus
    date: datetime
    payee: str | None
    description: str | None
    entries: list[EntrySchema]
    total_amount: MoneySchema | None
    attachment_count: int = 0
    created_at: datetime
    updated_at: datetime


class TransactionListResponse(BaseModel):
    """Response for listing transactions."""
    transactions: list[TransactionResponse]
    total: int
    limit: int
    offset: int


class TransactionFilterParams(BaseModel):
    """Query parameters for filtering transactions."""
    account_id: str | None = None
    category_id: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    amount_min: Decimal | None = None
    amount_max: Decimal | None = None
    payee: str | None = None
    search: str | None = None  # Full-text search
    limit: int = Field(default=100, le=500)
    offset: int = Field(default=0, ge=0)
```

### SQLAlchemy Tables

```python
# Addition to src/adapters/persistence/orm/tables.py

from sqlalchemy import (
    Column, DateTime, ForeignKey, Index, Integer, Numeric, String, Table, Text,
)
from sqlalchemy.dialects.postgresql import TSVECTOR

# Transaction categories
categories = Table(
    "categories",
    metadata,
    Column("id", String(36), primary_key=True),  # cat_xxx
    Column("user_id", String(36), ForeignKey("users.id"), nullable=False),
    Column("name", String(255), nullable=False),
    Column("parent_id", String(36), ForeignKey("categories.id"), nullable=True),
    Column("is_system", Boolean, nullable=False, default=False),
    Column("sort_order", Integer, nullable=False, default=0),
    Column("icon", String(50), nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),

    Index("ix_categories_user_id", "user_id"),
    Index("ix_categories_parent", "parent_id"),
)

# Transactions (header)
transactions = Table(
    "transactions",
    metadata,
    Column("id", String(36), primary_key=True),  # txn_xxx
    Column("user_id", String(36), ForeignKey("users.id"), nullable=False),
    Column("transaction_type", String(20), nullable=False),
    Column("status", String(20), nullable=False),
    Column("date", DateTime(timezone=True), nullable=False),
    Column("payee", String(255), nullable=True),
    Column("description", Text, nullable=True),
    Column("reference_number", String(100), nullable=True),
    Column("cleared_at", DateTime(timezone=True), nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),

    # Full-text search vector (populated by trigger or app)
    Column("search_vector", TSVECTOR, nullable=True),

    Index("ix_transactions_user_id", "user_id"),
    Index("ix_transactions_user_date", "user_id", "date"),
    Index("ix_transactions_search", "search_vector", postgresql_using="gin"),
)

# Transaction entries (line items)
entries = Table(
    "entries",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("transaction_id", String(36), ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False),
    Column("account_id", String(36), ForeignKey("accounts.id"), nullable=False),
    Column("category_id", String(36), ForeignKey("categories.id"), nullable=True),
    Column("amount", Numeric(19, 4), nullable=False),
    Column("currency", String(3), nullable=False),
    Column("memo", String(500), nullable=True),

    Index("ix_entries_transaction", "transaction_id"),
    Index("ix_entries_account", "account_id"),
    Index("ix_entries_category", "category_id"),
)

# Attachments
attachments = Table(
    "attachments",
    metadata,
    Column("id", String(36), primary_key=True),  # att_xxx
    Column("transaction_id", String(36), ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False),
    Column("user_id", String(36), ForeignKey("users.id"), nullable=False),
    Column("filename", String(255), nullable=False),
    Column("storage_path", String(500), nullable=False),
    Column("content_type", String(100), nullable=False),
    Column("size_bytes", Integer, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),

    Index("ix_attachments_transaction", "transaction_id"),
    Index("ix_attachments_user", "user_id"),
)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Single-entry transactions | Entry pattern with balanced debits/credits | Best practice | Proper double-entry accounting |
| Two-transaction transfers | Single transaction with two entries | Best practice | Simpler tracking, atomic transfers |
| SQL LIKE for search | PostgreSQL tsvector + GIN index | Ongoing | Better performance, linguistic support |
| Sync file uploads | Async with aiofiles | FastAPI best practice | Non-blocking I/O |
| Cloud storage required | Local storage sufficient initially | Pragmatic | Simpler deployment, cloud deferred |

**Deprecated/outdated:**
- **Storing balance on account:** Calculate from transactions
- **Floating-point for money:** Always use Decimal
- **LIKE '%query%' for search:** Use full-text search

## Open Questions

Things that couldn't be fully resolved:

1. **Full-text search trigger vs application update**
   - What we know: tsvector can be updated via database trigger or application code
   - What's unclear: Which approach is more maintainable
   - Recommendation: Start with application code updating search_vector on save; add trigger if needed for performance

2. **Attachment storage: local vs cloud**
   - What we know: Local storage is simpler; cloud (S3) is scalable
   - What's unclear: When to migrate to cloud storage
   - Recommendation: Start with local storage, design interface to support future cloud migration

3. **Split transaction UI representation**
   - What we know: Multiple entries with same account, different categories
   - What's unclear: Best UX for displaying/editing splits
   - Recommendation: Domain model supports it; UI design is Phase 4 concern

4. **Negative balance prevention scope**
   - What we know: TRAN-14 requires preventing negative balances on some accounts
   - What's unclear: Should this apply to all account types or configurable per-account?
   - Recommendation: Apply to CHECKING and SAVINGS by default; credit cards and loans naturally have negative (owed) balances

## Sources

### Primary (HIGH confidence)
- Phase 1 RESEARCH.md - Established patterns for Money, EntityId, Events, UoW, imperative mapping
- Phase 2 RESEARCH.md - Account aggregate pattern, repository patterns
- [SQLAlchemy 2.0 Full-Text Search](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html) - tsvector, GIN index
- [FastAPI File Uploads](https://fastapi.tiangolo.com/tutorial/request-files/) - UploadFile handling
- [Django Hordak](https://github.com/adamcharnock/django-hordak) - Double-entry accounting model (Transaction + Leg pattern)

### Secondary (MEDIUM confidence)
- [SQLAlchemy-file](https://jowilf.github.io/sqlalchemy-file/) - File attachment patterns (adapted for simpler local storage)
- [Python Accounting](https://github.com/ekmungai/python-accounting) - Double-entry patterns
- Web searches on transaction split modeling - multiple sources agree on entry-based approach

### Tertiary (LOW confidence)
- Medium articles on double-entry accounting implementation - cross-referenced with official docs
- Financial Freedom wiki - transaction split concept (implementation details not available)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Uses existing Phase 1/2 stack with minimal additions
- Architecture patterns: HIGH - Entry pattern well-established in accounting, matches existing aggregate patterns
- Pitfalls: MEDIUM - Some based on general best practices rather than specific documentation
- Code examples: MEDIUM - Adapted from established patterns, needs integration testing

**Research date:** 2026-01-30
**Valid until:** 2026-03-01 (30 days - stable patterns, existing codebase foundation)
