"""SQLAlchemy table definitions.

Table definitions are separate from domain models following the Data Mapper pattern.
This ensures domain models remain pure (no SQLAlchemy imports).

Tables created:
- outbox: Domain event outbox for reliable delivery (Pattern 5 from RESEARCH.md)
- users: Foundation user table (expanded in later phases)
- encrypted_secrets: Storage for encrypted sensitive data (Plaid tokens, etc.)
- accounts: Account aggregate persistence with type-specific fields

Custom type decorators handle domain type conversion for EntityIds and Enums.
"""

from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
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

from .base import metadata
from .types import (
    AccountIdType,
    AccountStatusEnum,
    AccountSubtypeEnum,
    AccountTypeEnum,
    CategoryIdType,
    PayeeIdType,
    SplitIdType,
    TransactionIdType,
    TransactionSourceEnum,
    TransactionStatusEnum,
    UserIdType,
)

# Outbox table for domain events (RESEARCH.md Pattern 5)
# Events are written here in same transaction as business data,
# then processed asynchronously by a background worker.
outbox = Table(
    "outbox",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("event_type", String(255), nullable=False),
    Column("aggregate_type", String(255), nullable=False),
    Column("aggregate_id", String(36), nullable=False),
    Column("payload", Text, nullable=False),  # JSON serialized
    Column(
        "created_at",
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    ),
    Column("processed_at", DateTime(timezone=True), nullable=True),
    # Partial index for efficient polling of unprocessed events
    Index(
        "ix_outbox_unprocessed",
        "processed_at",
        postgresql_where=Column("processed_at").is_(None),
    ),
)

# Users table (foundation for all user-owned data)
# Using String(36) for ID to accommodate prefixed TypeID format (user_xxx)
users = Table(
    "users",
    metadata,
    Column("id", String(36), primary_key=True),  # user_xxx
    Column("email", String(255), nullable=False, unique=True),
    Column("email_verified", Boolean, nullable=False, default=False),
    Column(
        "created_at",
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    ),
    Column(
        "updated_at",
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    ),
)

# Encrypted secrets storage (for Plaid tokens, etc.)
# AES-256-GCM encrypted values stored as text (base64 encoded)
encrypted_secrets = Table(
    "encrypted_secrets",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", String(36), ForeignKey("users.id"), nullable=False),
    Column("secret_type", String(50), nullable=False),  # e.g., "plaid_access_token"
    Column("encrypted_value", Text, nullable=False),  # AES-256-GCM encrypted
    Column(
        "created_at",
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    ),
    Column(
        "updated_at",
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    ),
    # Unique constraint: one secret type per user
    Index("ix_encrypted_secrets_user_type", "user_id", "secret_type", unique=True),
)

# Accounts table with single table inheritance (type discriminator)
# Supports multiple account types (checking, savings, credit card, loan, etc.)
# with type-specific optional fields.
# Uses custom TypeDecorators for domain type conversion.
accounts = Table(
    "accounts",
    metadata,
    # Identity - uses custom type decorators for EntityId conversion
    Column("id", AccountIdType(36), primary_key=True),  # acct_xxx
    Column("user_id", UserIdType(36), ForeignKey("users.id"), nullable=False),

    # Core fields - uses custom type decorators for enum conversion
    Column("name", String(255), nullable=False),
    Column("account_type", AccountTypeEnum(50), nullable=False),  # Discriminator
    Column("status", AccountStatusEnum(20), nullable=False, default="active"),
    Column("subtype", AccountSubtypeEnum(50), nullable=True),

    # Balance tracking
    Column("opening_balance_amount", Numeric(19, 4), nullable=False),
    Column("opening_balance_currency", String(3), nullable=False),
    Column("opening_date", DateTime(timezone=True), nullable=False),

    # Type-specific fields (nullable for types that don't use them)
    Column("credit_limit_amount", Numeric(19, 4), nullable=True),
    Column("credit_limit_currency", String(3), nullable=True),
    Column("apr", Numeric(5, 4), nullable=True),  # e.g., 0.1999 for 19.99%
    Column("term_months", Integer, nullable=True),
    Column("due_date", DateTime(timezone=True), nullable=True),

    # Rewards-specific
    Column("rewards_value", Numeric(19, 0), nullable=True),
    Column("rewards_unit", String(100), nullable=True),

    # Institution
    Column("institution_name", String(255), nullable=True),
    Column("institution_website", String(500), nullable=True),
    Column("institution_phone", String(50), nullable=True),
    Column("institution_notes", Text, nullable=True),

    # Encrypted account number (AES-256-GCM via FieldEncryption)
    Column("encrypted_account_number", Text, nullable=True),

    # Lifecycle
    Column("closing_date", DateTime(timezone=True), nullable=True),
    Column("notes", Text, nullable=True),
    Column("sort_order", Integer, nullable=False, default=0),

    # Audit - uses UserIdType for nullable user references
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("created_by", UserIdType(36), nullable=True),
    Column("updated_by", UserIdType(36), nullable=True),

    # Indexes
    Index("ix_accounts_user_id", "user_id"),
    Index("ix_accounts_user_type", "user_id", "account_type"),
    Index("ix_accounts_user_status", "user_id", "status"),
)

# Categories table (hierarchical structure for transaction categorization)
# Parent/child relationships enable nested categories (e.g., Food > Groceries)
categories = Table(
    "categories",
    metadata,
    Column("id", CategoryIdType(36), primary_key=True),  # cat_xxx
    Column("user_id", UserIdType(36), ForeignKey("users.id"), nullable=False),
    Column("name", String(255), nullable=False),

    # Hierarchy - parent_id is None for top-level categories
    Column("parent_id", CategoryIdType(36), ForeignKey("categories.id"), nullable=True),

    # Type - income or expense (defaults to expense)
    Column("category_type", String(10), nullable=False, server_default="expense"),

    # Metadata
    Column("is_system", Boolean, nullable=False, default=False),
    Column("is_hidden", Boolean, nullable=False, default=False),
    Column("sort_order", Integer, nullable=False, default=0),
    Column("icon", String(50), nullable=True),

    # Audit
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),

    # Indexes
    Index("ix_categories_user_id", "user_id"),
    Index("ix_categories_parent_id", "parent_id"),
    Index("ix_categories_user_system", "user_id", "is_system"),
)

# Payees table (managed entity list for autocomplete and categorization)
# normalized_name enables case-insensitive matching
payees = Table(
    "payees",
    metadata,
    Column("id", PayeeIdType(36), primary_key=True),  # payee_xxx
    Column("user_id", UserIdType(36), ForeignKey("users.id"), nullable=False),
    Column("name", String(255), nullable=False),
    Column("normalized_name", String(255), nullable=False),  # Lowercase for matching

    # Default category for auto-fill when selecting this payee
    Column(
        "default_category_id",
        CategoryIdType(36),
        ForeignKey("categories.id"),
        nullable=True,
    ),

    # Usage tracking for autocomplete relevance
    Column("last_used_at", DateTime(timezone=True), nullable=True),
    Column("usage_count", Integer, nullable=False, default=0),

    # Audit
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),

    # Indexes
    Index("ix_payees_user_id", "user_id"),
    Index("ix_payees_user_normalized", "user_id", "normalized_name"),
)

# Transactions table (always-split model per CONTEXT)
# Every transaction has 1+ split lines, even single-category transactions
transactions = Table(
    "transactions",
    metadata,
    Column("id", TransactionIdType(36), primary_key=True),  # txn_xxx
    Column("user_id", UserIdType(36), ForeignKey("users.id"), nullable=False),
    Column("account_id", AccountIdType(36), ForeignKey("accounts.id"), nullable=False),

    # Dates per CONTEXT: effective_date and posted_date (Date type, not DateTime)
    Column("effective_date", Date, nullable=False),
    Column("posted_date", Date, nullable=True),  # None = pending

    # Amount: net flow to account (positive = inflow, negative = outflow)
    Column("amount", Numeric(19, 4), nullable=False),
    Column("currency", String(3), nullable=False, default="USD"),

    # Status and source
    Column("status", TransactionStatusEnum(20), nullable=False, default="pending"),
    Column("source", TransactionSourceEnum(20), nullable=False, default="manual"),

    # Payee (managed entity reference + denormalized name for display)
    Column("payee_id", PayeeIdType(36), ForeignKey("payees.id"), nullable=True),
    Column("payee_name", String(255), nullable=True),

    # Description
    Column("memo", Text, nullable=True),
    Column("check_number", String(50), nullable=True),

    # Mirror transaction link for transfers
    Column(
        "source_transaction_id",
        TransactionIdType(36),
        ForeignKey("transactions.id"),
        nullable=True,
    ),
    Column("source_split_id", SplitIdType(36), nullable=True),  # Links mirror to source split
    Column("is_mirror", Boolean, nullable=False, default=False),

    # Audit
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),

    # Full-text search vector (updated by application)
    Column("search_vector", TSVECTOR, nullable=True),

    # Indexes
    Index("ix_transactions_user_id", "user_id"),
    Index("ix_transactions_account_id", "account_id"),
    Index("ix_transactions_user_effective_date", "user_id", "effective_date"),
    Index("ix_transactions_account_effective_date", "account_id", "effective_date"),
    Index("ix_transactions_source_transaction", "source_transaction_id"),
    Index("ix_transactions_source_split_id", "source_split_id"),
    Index("ix_transactions_search", "search_vector", postgresql_using="gin"),
)

# Split lines table (always 1+ per transaction)
# Each split assigns a portion of the transaction to either:
# - A category (expense/income categorization)
# - A transfer account (money moving between accounts)
split_lines = Table(
    "split_lines",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("split_id", String(36), nullable=False),  # TypeID for split identity
    Column(
        "transaction_id",
        TransactionIdType(36),
        ForeignKey("transactions.id", ondelete="CASCADE"),
        nullable=False,
    ),

    # Amount: signed (positive = income/inflow, negative = expense/outflow)
    Column("amount", Numeric(19, 4), nullable=False),
    Column("currency", String(3), nullable=False, default="USD"),

    # Either category OR transfer account (not both, enforced by application)
    Column("category_id", CategoryIdType(36), ForeignKey("categories.id"), nullable=True),
    Column(
        "transfer_account_id",
        AccountIdType(36),
        ForeignKey("accounts.id"),
        nullable=True,
    ),

    # Per-split memo
    Column("memo", String(500), nullable=True),

    # Order within transaction
    Column("sort_order", Integer, nullable=False, default=0),

    # Indexes
    Index("ix_split_lines_transaction_id", "transaction_id"),
    Index("ix_split_lines_category_id", "category_id"),
    Index("ix_split_lines_transfer_account", "transfer_account_id"),
    Index("ix_split_lines_split_id", "split_id", unique=True),
)
