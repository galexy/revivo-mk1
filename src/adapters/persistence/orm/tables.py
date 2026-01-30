"""SQLAlchemy table definitions.

Table definitions are separate from domain models following the Data Mapper pattern.
This ensures domain models remain pure (no SQLAlchemy imports).

Tables created:
- outbox: Domain event outbox for reliable delivery (Pattern 5 from RESEARCH.md)
- users: Foundation user table (expanded in later phases)
- encrypted_secrets: Storage for encrypted sensitive data (Plaid tokens, etc.)

Note: Account and Transaction tables will be added in Phases 2 and 3.
"""

from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    Text,
)

from .base import metadata

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
