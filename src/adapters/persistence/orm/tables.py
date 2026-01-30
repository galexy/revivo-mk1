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
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Table,
    Text,
)

from .base import metadata
from .types import (
    AccountIdType,
    AccountStatusEnum,
    AccountSubtypeEnum,
    AccountTypeEnum,
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
