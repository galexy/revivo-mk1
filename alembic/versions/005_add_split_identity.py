"""Add split identity columns.

Phase 3.1: Split Identity & Validation Fixes

This migration adds:
- split_id column to split_lines (TypeID for split identity)
- source_split_id column to transactions (links mirrors to source splits)

Three-step approach for split_id:
1. Add column as nullable
2. Backfill existing splits with generated IDs
3. Alter to NOT NULL

Revision ID: 005
Revises: 004
Create Date: 2026-02-02
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from typeid import TypeID

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add split_id column to split_lines (nullable first)
    op.add_column(
        "split_lines",
        sa.Column("split_id", sa.String(36), nullable=True),
    )

    # 2. Backfill existing splits with generated IDs
    conn = op.get_bind()
    result = conn.execute(sa.text("SELECT id FROM split_lines WHERE split_id IS NULL"))
    for row in result:
        split_id = str(TypeID(prefix="split"))
        conn.execute(
            sa.text("UPDATE split_lines SET split_id = :split_id WHERE id = :id"),
            {"split_id": split_id, "id": row[0]},
        )

    # 3. Make split_id NOT NULL and add unique index
    op.alter_column("split_lines", "split_id", nullable=False)
    op.create_index("ix_split_lines_split_id", "split_lines", ["split_id"], unique=True)

    # 4. Add source_split_id to transactions (nullable - only for mirrors)
    op.add_column(
        "transactions",
        sa.Column("source_split_id", sa.String(36), nullable=True),
    )
    op.create_index(
        "ix_transactions_source_split_id",
        "transactions",
        ["source_split_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_transactions_source_split_id", table_name="transactions")
    op.drop_column("transactions", "source_split_id")

    op.drop_index("ix_split_lines_split_id", table_name="split_lines")
    op.drop_column("split_lines", "split_id")
