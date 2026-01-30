# Phase 3: Transaction Domain - Research

**Researched:** 2026-01-30
**Domain:** Single-Entry Accounting, Transaction Modeling, File Attachments, Personal Finance Patterns
**Confidence:** HIGH

## Summary

This research covers the design patterns and implementation strategies for building the Transaction domain in a personal finance application using **SINGLE-ENTRY accounting**. This is a deliberate choice to keep the model simple and match how users think about transactions - each transaction is one record with an amount, not a debit/credit pair.

The standard approach for single-entry transaction modeling in personal finance apps uses:
- **Transaction as a single record** with date, amount, account, category, payee, type (expense/income/transfer)
- **Split support via SplitLine child records** where a transaction can have multiple category allocations
- **Transfer modeling as a special transaction type** that links from_account and to_account
- **Balance calculation** as opening_balance + sum(transactions for account)
- **Attachment entity** storing file metadata with local filesystem storage
- **PostgreSQL full-text search** via tsvector for payee/notes search

The codebase already establishes Money value object, EntityId pattern (TransactionId, CategoryId already defined), DomainEvent base, UnitOfWork, and Account aggregate - Phase 3 builds on all these foundations.

**Primary recommendation:** Model transactions as single records with type discriminator (EXPENSE, INCOME, TRANSFER). Use a separate SplitLine table for splits. Transfers are a single transaction with both from_account_id and to_account_id populated.

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
| aiofiles | 24.1+ | Async file I/O | Writing uploaded files without blocking |

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
            split_line.py       # SplitLine value object for splits
            category.py         # Category entity
            attachment.py       # Attachment entity
            transaction_types.py # TransactionType, TransactionStatus enums
        events/
            transaction_events.py  # TransactionCreated, TransactionUpdated, etc.
        ports/
            transaction_repository.py  # TransactionRepository protocol
            category_repository.py     # CategoryRepository protocol
            attachment_repository.py   # AttachmentRepository protocol
    adapters/
        persistence/
            orm/
                tables.py       # Add transactions, split_lines, categories, attachments tables
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
            test_split_line.py
            test_category.py
    integration/
        test_transaction_repository.py
        test_transaction_search.py
```

### Pattern 1: Single-Entry Transaction Model

**What:** Transaction as a single record representing one financial event
**When to use:** All financial transactions - simpler than double-entry, matches user mental model
**Why this pattern:** Personal finance apps don't need formal accounting; users think "I spent $50 at grocery store" not "debit expense, credit cash"

**Example:**
```python
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
from src.domain.model.money import Money
from src.domain.model.split_line import SplitLine
from src.domain.model.transaction_types import TransactionStatus, TransactionType


@dataclass(eq=False)
class Transaction:
    """Transaction aggregate root - single-entry accounting model.

    Each transaction is one record representing a financial event:
    - EXPENSE: Money going out (negative impact on account balance)
    - INCOME: Money coming in (positive impact on account balance)
    - TRANSFER: Money moving between two accounts (links both accounts)

    For simple transactions: amount, account_id, category_id
    For splits: amount is total, split_lines break down by category
    For transfers: from_account_id and to_account_id are both populated
    """
    id: TransactionId
    user_id: UserId
    transaction_type: TransactionType
    status: TransactionStatus

    # Transaction core data
    date: datetime  # When transaction occurred (user-specified)
    amount: Money   # Always positive - type determines direction

    # Account linkage (which account(s) affected)
    account_id: AccountId  # Primary account (or source for transfers)
    transfer_account_id: AccountId | None = None  # Destination for transfers only

    # Categorization (for expenses/income, not transfers)
    category_id: CategoryId | None = None

    # Split lines (for split transactions)
    split_lines: list[SplitLine] = field(default_factory=list)

    # Description
    payee: str | None = None  # Who received/sent money
    description: str | None = None  # User notes
    reference_number: str | None = None  # Check number, confirmation code, etc.

    # Reconciliation
    cleared_at: datetime | None = None

    # Audit
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    # Domain events (not persisted directly)
    _events: list[DomainEvent] = field(default_factory=list, repr=False)

    @property
    def events(self) -> list[DomainEvent]:
        """Get collected domain events as a copy."""
        return list(self._events)

    def clear_events(self) -> None:
        """Clear collected events after processing."""
        self._events.clear()

    @property
    def is_split(self) -> bool:
        """Check if this is a split transaction."""
        return len(self.split_lines) > 0

    @property
    def is_transfer(self) -> bool:
        """Check if this is a transfer."""
        return self.transaction_type == TransactionType.TRANSFER

    def _validate_split_total(self) -> None:
        """Validate split lines sum to transaction amount."""
        if not self.split_lines:
            return

        split_total = sum(
            (line.amount.amount for line in self.split_lines),
            Decimal("0")
        )
        if split_total != self.amount.amount:
            raise ValueError(
                f"Split lines sum ({split_total}) must equal transaction amount ({self.amount.amount})"
            )

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

        Expense = money leaving account, stored as positive amount.
        The sign is determined by transaction_type, not amount value.
        """
        if amount.is_negative() or amount.is_zero():
            raise ValueError("Expense amount must be positive")

        txn = cls(
            id=TransactionId.generate(),
            user_id=user_id,
            transaction_type=TransactionType.EXPENSE,
            status=TransactionStatus.PENDING,
            date=date,
            amount=amount,
            account_id=account_id,
            category_id=category_id,
            payee=payee,
            description=description,
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

        Income = money entering account, stored as positive amount.
        """
        if amount.is_negative() or amount.is_zero():
            raise ValueError("Income amount must be positive")

        txn = cls(
            id=TransactionId.generate(),
            user_id=user_id,
            transaction_type=TransactionType.INCOME,
            status=TransactionStatus.PENDING,
            date=date,
            amount=amount,
            account_id=account_id,
            category_id=category_id,
            payee=payee,
            description=description,
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

        Transfer = single transaction affecting two accounts:
        - Decreases from_account balance
        - Increases to_account balance

        Stored as ONE record, not two separate transactions.
        """
        if amount.is_negative() or amount.is_zero():
            raise ValueError("Transfer amount must be positive")

        if from_account_id == to_account_id:
            raise ValueError("Cannot transfer to same account")

        txn = cls(
            id=TransactionId.generate(),
            user_id=user_id,
            transaction_type=TransactionType.TRANSFER,
            status=TransactionStatus.PENDING,
            date=date,
            amount=amount,
            account_id=from_account_id,  # Source account
            transfer_account_id=to_account_id,  # Destination account
            description=description,
            # No category for transfers
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
    def create_split_expense(
        cls,
        user_id: UserId,
        account_id: AccountId,
        total_amount: Money,
        split_lines: list[SplitLine],
        date: datetime,
        payee: str | None = None,
        description: str | None = None,
    ) -> Self:
        """Create a split expense across multiple categories.

        Split = single transaction with total amount broken down
        into multiple category allocations (e.g., grocery receipt
        with food and household items).

        Split lines must sum to total_amount.
        """
        if total_amount.is_negative() or total_amount.is_zero():
            raise ValueError("Split expense amount must be positive")

        if not split_lines:
            raise ValueError("Split transaction requires at least one split line")

        txn = cls(
            id=TransactionId.generate(),
            user_id=user_id,
            transaction_type=TransactionType.EXPENSE,
            status=TransactionStatus.PENDING,
            date=date,
            amount=total_amount,
            account_id=account_id,
            split_lines=split_lines,
            payee=payee,
            description=description,
            # category_id is None for splits - categories are on split_lines
        )

        # Validate split total
        txn._validate_split_total()

        txn._events.append(
            TransactionCreated(
                aggregate_id=str(txn.id),
                aggregate_type="Transaction",
                transaction_type="SPLIT_EXPENSE",
                amount=str(total_amount.amount),
                currency=total_amount.currency,
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

    def update_category(self, new_category_id: CategoryId | None) -> None:
        """Update transaction category (not for splits or transfers)."""
        if self.is_split:
            raise ValueError("Cannot set category on split transaction - update split lines instead")
        if self.is_transfer:
            raise ValueError("Transfers do not have categories")

        old_category = str(self.category_id) if self.category_id else None
        self.category_id = new_category_id
        self.updated_at = datetime.now(UTC)
        self._events.append(
            TransactionUpdated(
                aggregate_id=str(self.id),
                aggregate_type="Transaction",
                field="category_id",
                old_value=old_category,
                new_value=str(new_category_id) if new_category_id else None,
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
                old_value=old_date.isoformat(),
                new_value=new_date.isoformat(),
            )
        )

    def update_amount(self, new_amount: Money) -> None:
        """Update transaction amount.

        Note: For split transactions, also need to update split lines.
        """
        if new_amount.is_negative() or new_amount.is_zero():
            raise ValueError("Amount must be positive")

        old_amount = self.amount
        self.amount = new_amount
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

    def mark_cleared(self) -> None:
        """Mark transaction as cleared/reconciled."""
        if self.status == TransactionStatus.CLEARED:
            raise ValueError("Transaction is already cleared")
        self.status = TransactionStatus.CLEARED
        self.cleared_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)
```

### Pattern 2: SplitLine Value Object

**What:** Value object representing one line of a split transaction
**When to use:** When a single payment needs to be allocated across multiple categories

**Example:**
```python
# src/domain/model/split_line.py
from dataclasses import dataclass

from src.domain.model.entity_id import CategoryId
from src.domain.model.money import Money


@dataclass(frozen=True, slots=True)
class SplitLine:
    """A single line item in a split transaction.

    Represents a portion of the transaction allocated to a specific category.
    Example: $100 grocery receipt split into $70 food + $30 household supplies.
    """
    amount: Money  # Portion of total (always positive)
    category_id: CategoryId | None = None  # Category for this portion
    memo: str | None = None  # Description for this split line

    def __post_init__(self) -> None:
        """Validate split line amount is positive."""
        if self.amount.is_negative() or self.amount.is_zero():
            raise ValueError("Split line amount must be positive")
```

### Pattern 3: Transaction Type Enumerations

**What:** Type-safe string enums for transaction type and status
**When to use:** All transaction classification fields

**Example:**
```python
# src/domain/model/transaction_types.py
from enum import StrEnum, auto


class TransactionType(StrEnum):
    """Types of financial transactions in single-entry system."""
    EXPENSE = auto()    # Money out of account
    INCOME = auto()     # Money into account
    TRANSFER = auto()   # Between two accounts (single record)


class TransactionStatus(StrEnum):
    """Transaction lifecycle status."""
    PENDING = auto()    # Not yet cleared/reconciled
    CLEARED = auto()    # Reconciled with bank statement
    VOID = auto()       # Cancelled/reversed
```

### Pattern 4: Category Entity

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
    category_type: str = "expense"  # "expense", "income", or "both"
    parent_id: CategoryId | None = None  # For hierarchical categories
    is_system: bool = False  # System-defined categories (Uncategorized, etc.)
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

### Pattern 5: Attachment Entity with File Storage

**What:** Separate entity for file attachments with metadata
**When to use:** Receipt images, documents attached to transactions

**Example:**
```python
# src/domain/model/attachment.py
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Self

from typeid import TypeID

from src.domain.model.entity_id import TransactionId, UserId


@dataclass(frozen=True, slots=True)
class AttachmentId:
    """Identifier for Attachment entity."""
    value: str

    @classmethod
    def generate(cls) -> "AttachmentId":
        tid = TypeID(prefix="att")
        return cls(value=str(tid))

    @classmethod
    def from_string(cls, value: str) -> "AttachmentId":
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
    ) -> Self:
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

### Pattern 6: File Storage Adapter

**What:** Simple local filesystem storage for attachments
**When to use:** All file upload operations

**Example:**
```python
# src/adapters/storage/file_storage.py
import uuid
from pathlib import Path
from typing import BinaryIO, Protocol

import aiofiles


class FileStorage(Protocol):
    """Protocol for file storage operations."""

    async def save(
        self,
        file: BinaryIO,
        user_id: str,
        original_filename: str,
    ) -> str:
        """Save file and return storage path."""
        ...

    def get_full_path(self, storage_path: str) -> Path:
        """Get full filesystem path for a storage path."""
        ...

    def delete(self, storage_path: str) -> None:
        """Delete a file by storage path."""
        ...


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
        allowed_extensions = {".jpg", ".jpeg", ".png", ".gif", ".pdf", ".webp"}
        if ext not in allowed_extensions:
            ext = ""  # Strip unknown extensions for security
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

### Pattern 7: PostgreSQL Full-Text Search for Transactions

**What:** Use PostgreSQL tsvector for searching transactions by payee/description
**When to use:** Transaction search functionality (TRAN-09)

**Example:**
```python
# In tables.py - Add search vector column
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
        from sqlalchemy import func, select

        # plainto_tsquery handles user input safely
        ts_query = func.plainto_tsquery("english", query)

        # Use @@ operator for full-text match
        stmt = (
            select(transactions)
            .where(transactions.c.user_id == str(user_id))
            .where(transactions.c.search_vector.op("@@")(ts_query))
            .order_by(transactions.c.date.desc())
            .limit(limit)
            .offset(offset)
        )

        result = self._session.execute(stmt)
        return [self._map_to_domain(row) for row in result]

    def _update_search_vector(self, txn: Transaction) -> None:
        """Update search vector when saving transaction."""
        # Combine searchable fields
        searchable = " ".join(filter(None, [txn.payee, txn.description]))

        # Update via SQL to use to_tsvector
        stmt = (
            transactions.update()
            .where(transactions.c.id == str(txn.id))
            .values(
                search_vector=func.to_tsvector("english", searchable)
            )
        )
        self._session.execute(stmt)
```

### Pattern 8: Balance Calculation

**What:** Calculate account balance from transactions (not stored on account)
**When to use:** Any balance display or validation

**Example:**
```python
# In transaction_repository.py
class SqlAlchemyTransactionRepository:
    def calculate_account_balance(self, account_id: AccountId) -> Money:
        """Calculate balance from opening balance + all transactions.

        Single-entry balance logic:
        - INCOME: +amount (money in)
        - EXPENSE: -amount (money out)
        - TRANSFER from this account: -amount
        - TRANSFER to this account: +amount
        """
        from sqlalchemy import case, func, select

        # Sum based on transaction type and account role
        balance_expr = func.sum(
            case(
                # Income to this account: +amount
                (
                    (transactions.c.transaction_type == "income") &
                    (transactions.c.account_id == str(account_id)),
                    transactions.c.amount
                ),
                # Expense from this account: -amount
                (
                    (transactions.c.transaction_type == "expense") &
                    (transactions.c.account_id == str(account_id)),
                    -transactions.c.amount
                ),
                # Transfer FROM this account: -amount
                (
                    (transactions.c.transaction_type == "transfer") &
                    (transactions.c.account_id == str(account_id)),
                    -transactions.c.amount
                ),
                # Transfer TO this account: +amount
                (
                    (transactions.c.transaction_type == "transfer") &
                    (transactions.c.transfer_account_id == str(account_id)),
                    transactions.c.amount
                ),
                else_=Decimal("0")
            )
        )

        stmt = (
            select(balance_expr)
            .where(
                (transactions.c.account_id == str(account_id)) |
                (transactions.c.transfer_account_id == str(account_id))
            )
            .where(transactions.c.status != "void")  # Exclude voided
        )

        result = self._session.execute(stmt).scalar()
        return Money(result or Decimal("0"), "USD")  # Default currency
```

### Anti-Patterns to Avoid

- **Storing balance on Account aggregate:** Balance should be calculated from transactions. Cached balance leads to inconsistency.
- **Two transactions for transfers:** Use single transaction with from/to accounts, not two linked transactions.
- **Floating-point amounts:** Always use Decimal via Money value object.
- **Negative amounts for expenses:** Store all amounts as positive; type determines direction.
- **Storing full file paths:** Store relative paths, construct full paths at runtime.
- **Generic category ID (no validation):** Validate category belongs to user.
- **Direct SQL LIKE for search:** Use PostgreSQL tsvector with GIN index.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Transaction amounts | Custom amount class | Money from money.py | Already handles precision, currency |
| Transaction IDs | String concatenation | TransactionId from entity_id.py | Already implemented |
| Category IDs | String concatenation | CategoryId from entity_id.py | Already implemented |
| Full-text search | SQL LIKE queries | PostgreSQL tsvector + GIN | Proper tokenization, stemming, ranking |
| File upload handling | Manual multipart parsing | FastAPI UploadFile | Built-in validation, streaming |
| Date range queries | String parsing | datetime objects | Type safety, timezone handling |
| Event collection | Manual list management | _events pattern + UoW | Already established in Phase 1-2 |
| Decimal precision | Python float | SQLAlchemy Numeric(19, 4) | Exact precision for financial data |

**Key insight:** Phase 1 and Phase 2 established all foundation patterns. Phase 3 should compose existing building blocks (Money, EntityId, UoW, Events) and add transaction-specific domain logic.

## Common Pitfalls

### Pitfall 1: Storing Amount Sign Based on Type

**What goes wrong:** Inconsistent handling of positive/negative amounts
**Why it happens:** Confusion about whether expense should be stored as negative
**How to avoid:** Always store amounts as positive; let transaction_type determine effect on balance
**Warning signs:** Negative amounts in database, confusing balance calculations

### Pitfall 2: Transfer Appears in Account History Twice

**What goes wrong:** When listing transactions for an account, transfer shows once as outflow and once as inflow
**Why it happens:** Query returns transaction when account matches either from or to
**How to avoid:** Query logic should identify the account's role and show appropriate view
**Warning signs:** Transfer appears twice in combined account view

### Pitfall 3: Split Transaction Total Mismatch

**What goes wrong:** Split line amounts don't sum to transaction total
**Why it happens:** No validation when creating/updating split lines
**How to avoid:** Validate in factory method and mutation methods; enforce in domain
**Warning signs:** Category reports don't match account totals

### Pitfall 4: Missing Category Validation

**What goes wrong:** Category from another user assigned to transaction
**Why it happens:** No ownership check when creating/updating transaction
**How to avoid:** Application service validates category.user_id == transaction.user_id
**Warning signs:** Security bugs, users seeing other users' categories

### Pitfall 5: Large File Uploads Blocking Event Loop

**What goes wrong:** Synchronous file writes block async FastAPI
**Why it happens:** Using regular file.write() instead of async
**How to avoid:** Use aiofiles for async file operations
**Warning signs:** High latency during uploads, timeout errors

### Pitfall 6: Full-Text Search Without Index

**What goes wrong:** Search becomes slow as transactions grow
**Why it happens:** Using LIKE '%query%' instead of tsvector
**How to avoid:** Create GIN index on tsvector column, use plainto_tsquery
**Warning signs:** Slow search, queries scanning full table

### Pitfall 7: Not Handling Negative Balance Prevention (TRAN-13)

**What goes wrong:** Account goes negative when it shouldn't
**Why it happens:** No balance check before committing expense/withdrawal
**How to avoid:** Application service calculates projected balance before allowing expense/transfer
**Warning signs:** Negative balances on checking accounts without overdraft

### Pitfall 8: Attachment Orphans After Transaction Delete

**What goes wrong:** Files remain on disk after transaction deleted
**Why it happens:** No cascade delete, no cleanup
**How to avoid:** Delete attachments in same unit of work; use ON DELETE CASCADE in DB
**Warning signs:** Storage usage growing, orphan files on disk

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

### SQLAlchemy Tables

```python
# Addition to src/adapters/persistence/orm/tables.py

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Table,
    Text,
)
from sqlalchemy.dialects.postgresql import TSVECTOR

# Transaction categories
categories = Table(
    "categories",
    metadata,
    Column("id", String(36), primary_key=True),  # cat_xxx
    Column("user_id", String(36), ForeignKey("users.id"), nullable=False),
    Column("name", String(255), nullable=False),
    Column("category_type", String(20), nullable=False, default="expense"),
    Column("parent_id", String(36), ForeignKey("categories.id"), nullable=True),
    Column("is_system", Boolean, nullable=False, default=False),
    Column("sort_order", Integer, nullable=False, default=0),
    Column("icon", String(50), nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),

    Index("ix_categories_user_id", "user_id"),
    Index("ix_categories_parent", "parent_id"),
)

# Transactions (single-entry model)
transactions = Table(
    "transactions",
    metadata,
    Column("id", String(36), primary_key=True),  # txn_xxx
    Column("user_id", String(36), ForeignKey("users.id"), nullable=False),
    Column("transaction_type", String(20), nullable=False),  # expense, income, transfer
    Column("status", String(20), nullable=False, default="pending"),
    Column("date", DateTime(timezone=True), nullable=False),

    # Amount (always positive, type determines direction)
    Column("amount", Numeric(19, 4), nullable=False),
    Column("currency", String(3), nullable=False, default="USD"),

    # Account linkage
    Column("account_id", String(36), ForeignKey("accounts.id"), nullable=False),
    Column("transfer_account_id", String(36), ForeignKey("accounts.id"), nullable=True),

    # Categorization (null for transfers and splits)
    Column("category_id", String(36), ForeignKey("categories.id"), nullable=True),

    # Description
    Column("payee", String(255), nullable=True),
    Column("description", Text, nullable=True),
    Column("reference_number", String(100), nullable=True),

    # Reconciliation
    Column("cleared_at", DateTime(timezone=True), nullable=True),

    # Audit
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),

    # Full-text search vector (updated by application)
    Column("search_vector", TSVECTOR, nullable=True),

    Index("ix_transactions_user_id", "user_id"),
    Index("ix_transactions_user_date", "user_id", "date"),
    Index("ix_transactions_account", "account_id"),
    Index("ix_transactions_transfer_account", "transfer_account_id"),
    Index("ix_transactions_category", "category_id"),
    Index("ix_transactions_search", "search_vector", postgresql_using="gin"),
)

# Split lines (for split transactions)
split_lines = Table(
    "split_lines",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("transaction_id", String(36), ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False),
    Column("amount", Numeric(19, 4), nullable=False),
    Column("currency", String(3), nullable=False, default="USD"),
    Column("category_id", String(36), ForeignKey("categories.id"), nullable=True),
    Column("memo", String(500), nullable=True),

    Index("ix_split_lines_transaction", "transaction_id"),
    Index("ix_split_lines_category", "category_id"),
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

### Pydantic API Schemas

```python
# src/adapters/api/schemas/transaction.py
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field

from src.domain.model.transaction_types import TransactionStatus, TransactionType


class MoneySchema(BaseModel):
    """Schema for money amounts."""
    amount: Decimal = Field(..., decimal_places=4)
    currency: str = Field(default="USD", min_length=3, max_length=3)


class SplitLineSchema(BaseModel):
    """Schema for a split line."""
    amount: MoneySchema
    category_id: str | None = None
    memo: str | None = Field(default=None, max_length=500)


class CreateExpenseRequest(BaseModel):
    """Request to create an expense transaction."""
    account_id: str = Field(..., description="Account ID for the expense")
    amount: MoneySchema = Field(..., description="Expense amount (positive)")
    date: datetime = Field(..., description="Transaction date")
    category_id: str | None = Field(default=None, description="Category for the expense")
    payee: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=2000)


class CreateIncomeRequest(BaseModel):
    """Request to create an income transaction."""
    account_id: str
    amount: MoneySchema
    date: datetime
    category_id: str | None = None
    payee: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=2000)


class CreateTransferRequest(BaseModel):
    """Request to create a transfer between accounts."""
    from_account_id: str
    to_account_id: str
    amount: MoneySchema
    date: datetime
    description: str | None = Field(default=None, max_length=2000)


class CreateSplitExpenseRequest(BaseModel):
    """Request to create a split expense transaction."""
    account_id: str
    total_amount: MoneySchema
    split_lines: list[SplitLineSchema] = Field(..., min_length=1)
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
    amount: MoneySchema
    account_id: str
    transfer_account_id: str | None = None
    category_id: str | None = None
    split_lines: list[SplitLineSchema] = []
    payee: str | None
    description: str | None
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
    transaction_type: TransactionType | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    amount_min: Decimal | None = None
    amount_max: Decimal | None = None
    payee: str | None = None
    search: str | None = None  # Full-text search
    limit: int = Field(default=100, le=500)
    offset: int = Field(default=0, ge=0)
```

### Transaction Service (Application Layer)

```python
# src/application/services/transaction_service.py
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, BinaryIO

from src.domain.model.account_types import AccountType
from src.domain.model.entity_id import AccountId, CategoryId, TransactionId, UserId
from src.domain.model.money import Money
from src.domain.model.split_line import SplitLine
from src.domain.model.transaction import Transaction

if TYPE_CHECKING:
    from src.adapters.storage.file_storage import FileStorage
    from src.domain.ports.unit_of_work import UnitOfWork


@dataclass(frozen=True, slots=True)
class TransactionError:
    """Error result for transaction operations."""
    code: str
    message: str


class TransactionService:
    """Application service for transaction use cases."""

    def __init__(self, uow: "UnitOfWork", file_storage: "FileStorage") -> None:
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

            # Check if expense would cause negative balance (TRAN-13)
            if not self._can_account_go_negative(account):
                current_balance = self._uow.transactions.calculate_account_balance(account_id)
                projected = current_balance - amount
                if projected.is_negative():
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
                return TransactionError("ACCOUNT_NOT_FOUND", f"Source account not found")
            if to_account is None:
                return TransactionError("ACCOUNT_NOT_FOUND", f"Destination account not found")
            if from_account.user_id != user_id or to_account.user_id != user_id:
                return TransactionError("ACCOUNT_NOT_OWNED", "Accounts do not belong to user")

            # Check balance on source
            if not self._can_account_go_negative(from_account):
                current_balance = self._uow.transactions.calculate_account_balance(from_account_id)
                projected = current_balance - amount
                if projected.is_negative():
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

    def _can_account_go_negative(self, account) -> bool:
        """Check if account type allows negative balance."""
        # Credit cards and loans naturally have negative balances (owed money)
        # Checking/savings should not go negative without overdraft
        return account.account_type in {
            AccountType.CREDIT_CARD,
            AccountType.LOAN,
        }
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Double-entry for personal finance | Single-entry with type discriminator | User preference | Simpler model, matches user thinking |
| Two transactions for transfers | Single transaction with from/to accounts | Best practice | Atomic transfers, simpler queries |
| Balance stored on Account | Balance calculated from transactions | Best practice | No stale data, always accurate |
| SQL LIKE for search | PostgreSQL tsvector + GIN index | PostgreSQL best practice | Performance at scale |
| Sync file uploads | Async with aiofiles | FastAPI best practice | Non-blocking I/O |

**Deprecated/outdated:**
- **Double-entry for personal finance apps:** Overkill for consumer apps; single-entry is simpler
- **Storing balance on account:** Calculate from transactions to avoid inconsistency
- **Floating-point for money:** Always use Decimal
- **LIKE '%query%' for search:** Use full-text search

## Open Questions

Things that couldn't be fully resolved:

1. **Full-text search trigger vs application update**
   - What we know: tsvector can be updated via database trigger or application code
   - What's unclear: Which approach is more maintainable for our stack
   - Recommendation: Start with application code updating search_vector on save; add trigger if needed

2. **Attachment storage: local vs cloud**
   - What we know: Local storage is simpler; cloud (S3) is scalable
   - What's unclear: When to migrate to cloud storage
   - Recommendation: Start with local storage, design interface (Protocol) to support future cloud migration

3. **Opening balance as a transaction vs account field**
   - What we know: Opening balance is currently on Account
   - What's unclear: Should it be an initial transaction for consistency?
   - Recommendation: Keep as account field for simplicity; it represents state before tracking began

4. **Negative balance prevention scope (TRAN-13)**
   - What we know: Requirement says "accounts that don't allow them"
   - What's unclear: Is this per-account configurable or by type?
   - Recommendation: Apply by account type (CHECKING, SAVINGS prevent negative; CREDIT_CARD, LOAN allow)

## Sources

### Primary (HIGH confidence)
- Existing codebase patterns from Phase 1 and Phase 2
- [SQLAlchemy 2.0 Numeric type documentation](https://docs.sqlalchemy.org/en/20/core/type_basics.html)
- [PostgreSQL Full-Text Search documentation](https://www.postgresql.org/docs/current/textsearch-intro.html)
- [FastAPI File Uploads tutorial](https://fastapi.tiangolo.com/tutorial/request-files/)

### Secondary (MEDIUM confidence)
- [FreshBooks Single Entry Bookkeeping](https://www.freshbooks.com/hub/accounting/single-entry-bookkeeping) - Single-entry concepts
- [Sling Academy FastAPI PostgreSQL Full-Text Search](https://www.slingacademy.com/article/how-to-use-postgresql-full-text-search-in-fastapi-applications/) - tsvector integration
- [Better Stack FastAPI File Uploads Guide](https://betterstack.com/community/guides/scaling-python/uploading-files-using-fastapi/) - aiofiles patterns

### Tertiary (LOW confidence)
- Personal finance app comparisons (YNAB, Mint, Money Pro) - feature patterns
- Medium articles on transaction split modeling - conceptual approaches

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Uses existing Phase 1/2 stack with minimal additions
- Architecture patterns: HIGH - Single-entry is simpler than double-entry, well-understood
- Database schema: HIGH - Follows existing patterns, standard PostgreSQL features
- Pitfalls: MEDIUM - Based on general best practices and experience
- Code examples: MEDIUM - Adapted from established patterns, needs integration testing

**Research date:** 2026-01-30
**Valid until:** 2026-03-01 (30 days - stable patterns, existing codebase foundation)
