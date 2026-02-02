"""Add category_type to categories.

Phase 3.1: Split Identity & Validation Fixes (CategoryType feature)

Revision ID: 004
Revises: 003
Create Date: 2026-02-02
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add category_type column with default 'expense'
    op.add_column(
        "categories",
        sa.Column(
            "category_type",
            sa.String(10),
            nullable=False,
            server_default="expense",
        ),
    )


def downgrade() -> None:
    op.drop_column("categories", "category_type")
