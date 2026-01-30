"""Create accounts table.

This migration creates the accounts table with:
- All columns for the Account aggregate
- Type-specific nullable fields for different account types
- Indexes for common query patterns (user_id, user+type, user+status)
- Foreign key to users table

Account types: checking, savings, credit_card, loan, brokerage, ira, rewards
Each type may use different optional fields (credit_limit for cards, apr for loans, etc.)

Revision ID: 002
Revises: 001
Create Date: 2026-01-30
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Accounts table with single table inheritance (type discriminator)
    op.create_table(
        "accounts",
        # Identity
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),

        # Core fields
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("account_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("subtype", sa.String(length=50), nullable=True),

        # Balance tracking
        sa.Column("opening_balance_amount", sa.Numeric(precision=19, scale=4), nullable=False),
        sa.Column("opening_balance_currency", sa.String(length=3), nullable=False),
        sa.Column("opening_date", sa.DateTime(timezone=True), nullable=False),

        # Type-specific fields (nullable for types that don't use them)
        sa.Column("credit_limit_amount", sa.Numeric(precision=19, scale=4), nullable=True),
        sa.Column("credit_limit_currency", sa.String(length=3), nullable=True),
        sa.Column("apr", sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column("term_months", sa.Integer(), nullable=True),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),

        # Rewards-specific
        sa.Column("rewards_value", sa.Numeric(precision=19, scale=0), nullable=True),
        sa.Column("rewards_unit", sa.String(length=100), nullable=True),

        # Institution
        sa.Column("institution_name", sa.String(length=255), nullable=True),
        sa.Column("institution_website", sa.String(length=500), nullable=True),
        sa.Column("institution_phone", sa.String(length=50), nullable=True),
        sa.Column("institution_notes", sa.Text(), nullable=True),

        # Encrypted account number
        sa.Column("encrypted_account_number", sa.Text(), nullable=True),

        # Lifecycle
        sa.Column("closing_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),

        # Audit
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),

        # Constraints
        sa.PrimaryKeyConstraint("id", name=op.f("pk_accounts")),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_accounts_user_id_users"),
        ),
    )

    # Indexes for common query patterns
    op.create_index(op.f("ix_accounts_user_id"), "accounts", ["user_id"], unique=False)
    op.create_index(op.f("ix_accounts_user_type"), "accounts", ["user_id", "account_type"], unique=False)
    op.create_index(op.f("ix_accounts_user_status"), "accounts", ["user_id", "status"], unique=False)


def downgrade() -> None:
    # Drop indexes first
    op.drop_index(op.f("ix_accounts_user_status"), table_name="accounts")
    op.drop_index(op.f("ix_accounts_user_type"), table_name="accounts")
    op.drop_index(op.f("ix_accounts_user_id"), table_name="accounts")
    # Drop table
    op.drop_table("accounts")
