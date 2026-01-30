"""Initial schema with outbox, users, and encrypted_secrets.

This migration creates the foundation tables:
- outbox: Domain event outbox for reliable event delivery
- users: Foundation user table for user-owned data
- encrypted_secrets: Storage for encrypted sensitive data (Plaid tokens, etc.)

These tables support the core infrastructure needs established in Phase 1.
Account and Transaction tables will be added in later phases.

Revision ID: 001
Revises:
Create Date: 2026-01-29
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Outbox table for domain events
    # Events are written here atomically with business data,
    # then processed by a background worker for delivery.
    op.create_table(
        "outbox",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("event_type", sa.String(length=255), nullable=False),
        sa.Column("aggregate_type", sa.String(length=255), nullable=False),
        sa.Column("aggregate_id", sa.String(length=36), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_outbox")),
    )
    # Partial index for efficient polling of unprocessed events
    # Only indexes rows where processed_at IS NULL
    op.create_index(
        op.f("ix_outbox_unprocessed"),
        "outbox",
        ["processed_at"],
        unique=False,
        postgresql_where=sa.text("processed_at IS NULL"),
    )

    # Users table - foundation for all user-owned data
    # ID is String(36) to accommodate prefixed TypeID format (user_xxx)
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column(
            "email_verified", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
    )

    # Encrypted secrets storage - for Plaid tokens, API keys, etc.
    # Values are AES-256-GCM encrypted (base64 encoded text)
    op.create_table(
        "encrypted_secrets",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("secret_type", sa.String(length=50), nullable=False),
        sa.Column("encrypted_value", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_encrypted_secrets_user_id_users"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_encrypted_secrets")),
    )
    # Unique constraint: one secret type per user
    op.create_index(
        op.f("ix_encrypted_secrets_user_type"),
        "encrypted_secrets",
        ["user_id", "secret_type"],
        unique=True,
    )


def downgrade() -> None:
    # Drop in reverse order of creation (respect foreign key constraints)
    op.drop_index(
        op.f("ix_encrypted_secrets_user_type"), table_name="encrypted_secrets"
    )
    op.drop_table("encrypted_secrets")
    op.drop_table("users")
    op.drop_index(op.f("ix_outbox_unprocessed"), table_name="outbox")
    op.drop_table("outbox")
