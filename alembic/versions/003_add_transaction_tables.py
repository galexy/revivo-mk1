"""Add transaction domain tables.

Phase 3: Transaction Domain - categories, payees, transactions, split_lines.

This migration creates:
- categories: Hierarchical category structure for transaction categorization
- payees: Managed payee list with usage tracking for autocomplete
- transactions: Always-split transaction model with dual dates
- split_lines: Category or transfer splits that sum to transaction amount

Key features:
- Full-text search via TSVECTOR with GIN index
- Self-referential FK on transactions for mirror links
- CASCADE delete on split_lines when transaction deleted
- Dual dates: effective_date (check/purchase) and posted_date (cleared)

Revision ID: 003
Revises: 002
Create Date: 2026-02-02
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Categories table (must be created before payees and transactions for FK)
    op.create_table(
        "categories",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("parent_id", sa.String(36), nullable=True),
        sa.Column("is_system", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("is_hidden", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default="0"),
        sa.Column("icon", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_categories")),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_categories_user_id_users"),
        ),
        sa.ForeignKeyConstraint(
            ["parent_id"],
            ["categories.id"],
            name=op.f("fk_categories_parent_id_categories"),
        ),
    )
    op.create_index("ix_categories_user_id", "categories", ["user_id"])
    op.create_index("ix_categories_parent_id", "categories", ["parent_id"])
    op.create_index("ix_categories_user_system", "categories", ["user_id", "is_system"])

    # Payees table (must be created before transactions for FK)
    op.create_table(
        "payees",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("normalized_name", sa.String(255), nullable=False),
        sa.Column("default_category_id", sa.String(36), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("usage_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_payees")),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_payees_user_id_users"),
        ),
        sa.ForeignKeyConstraint(
            ["default_category_id"],
            ["categories.id"],
            name=op.f("fk_payees_default_category_id_categories"),
        ),
    )
    op.create_index("ix_payees_user_id", "payees", ["user_id"])
    op.create_index("ix_payees_user_normalized", "payees", ["user_id", "normalized_name"])

    # Transactions table
    op.create_table(
        "transactions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("account_id", sa.String(36), nullable=False),
        sa.Column("effective_date", sa.Date, nullable=False),
        sa.Column("posted_date", sa.Date, nullable=True),
        sa.Column("amount", sa.Numeric(19, 4), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("source", sa.String(20), nullable=False, server_default="manual"),
        sa.Column("payee_id", sa.String(36), nullable=True),
        sa.Column("payee_name", sa.String(255), nullable=True),
        sa.Column("memo", sa.Text, nullable=True),
        sa.Column("check_number", sa.String(50), nullable=True),
        sa.Column("source_transaction_id", sa.String(36), nullable=True),
        sa.Column("is_mirror", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("search_vector", postgresql.TSVECTOR, nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_transactions")),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_transactions_user_id_users"),
        ),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["accounts.id"],
            name=op.f("fk_transactions_account_id_accounts"),
        ),
        sa.ForeignKeyConstraint(
            ["payee_id"],
            ["payees.id"],
            name=op.f("fk_transactions_payee_id_payees"),
        ),
    )

    # Add self-referential FK after table created
    op.create_foreign_key(
        op.f("fk_transactions_source_transaction_id_transactions"),
        "transactions",
        "transactions",
        ["source_transaction_id"],
        ["id"],
    )

    op.create_index("ix_transactions_user_id", "transactions", ["user_id"])
    op.create_index("ix_transactions_account_id", "transactions", ["account_id"])
    op.create_index(
        "ix_transactions_user_effective_date",
        "transactions",
        ["user_id", "effective_date"],
    )
    op.create_index(
        "ix_transactions_account_effective_date",
        "transactions",
        ["account_id", "effective_date"],
    )
    op.create_index(
        "ix_transactions_source_transaction",
        "transactions",
        ["source_transaction_id"],
    )
    op.create_index(
        "ix_transactions_search",
        "transactions",
        ["search_vector"],
        postgresql_using="gin",
    )

    # Split lines table
    op.create_table(
        "split_lines",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("transaction_id", sa.String(36), nullable=False),
        sa.Column("amount", sa.Numeric(19, 4), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("category_id", sa.String(36), nullable=True),
        sa.Column("transfer_account_id", sa.String(36), nullable=True),
        sa.Column("memo", sa.String(500), nullable=True),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_split_lines")),
        sa.ForeignKeyConstraint(
            ["transaction_id"],
            ["transactions.id"],
            name=op.f("fk_split_lines_transaction_id_transactions"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["categories.id"],
            name=op.f("fk_split_lines_category_id_categories"),
        ),
        sa.ForeignKeyConstraint(
            ["transfer_account_id"],
            ["accounts.id"],
            name=op.f("fk_split_lines_transfer_account_id_accounts"),
        ),
    )
    op.create_index("ix_split_lines_transaction_id", "split_lines", ["transaction_id"])
    op.create_index("ix_split_lines_category_id", "split_lines", ["category_id"])
    op.create_index(
        "ix_split_lines_transfer_account", "split_lines", ["transfer_account_id"]
    )


def downgrade() -> None:
    # Drop in reverse order of creation (respect FK dependencies)
    op.drop_index("ix_split_lines_transfer_account", table_name="split_lines")
    op.drop_index("ix_split_lines_category_id", table_name="split_lines")
    op.drop_index("ix_split_lines_transaction_id", table_name="split_lines")
    op.drop_table("split_lines")

    op.drop_index("ix_transactions_search", table_name="transactions")
    op.drop_index("ix_transactions_source_transaction", table_name="transactions")
    op.drop_index("ix_transactions_account_effective_date", table_name="transactions")
    op.drop_index("ix_transactions_user_effective_date", table_name="transactions")
    op.drop_index("ix_transactions_account_id", table_name="transactions")
    op.drop_index("ix_transactions_user_id", table_name="transactions")
    op.drop_constraint(
        op.f("fk_transactions_source_transaction_id_transactions"),
        "transactions",
        type_="foreignkey",
    )
    op.drop_table("transactions")

    op.drop_index("ix_payees_user_normalized", table_name="payees")
    op.drop_index("ix_payees_user_id", table_name="payees")
    op.drop_table("payees")

    op.drop_index("ix_categories_user_system", table_name="categories")
    op.drop_index("ix_categories_parent_id", table_name="categories")
    op.drop_index("ix_categories_user_id", table_name="categories")
    op.drop_table("categories")
