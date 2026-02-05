"""Replace households.owner_id with users.role column.

Removes the circular FK (households.owner_id -> users, users.household_id -> households)
by tracking ownership via a role column on the users table instead.

Steps:
1. Add role column to users (nullable initially, default "member")
2. Migrate existing owners: set role='owner' where user matches households.owner_id
3. Set remaining users to role='member'
4. Make role NOT NULL
5. Drop FK constraint fk_households_owner_id
6. Drop owner_id column from households

Revision ID: 007
Revises: 006
Create Date: 2026-02-05
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add role column (nullable initially so we can backfill)
    op.add_column(
        "users",
        sa.Column("role", sa.String(20), nullable=True),
    )

    # 2. Backfill: set role='owner' for users who are household owners
    op.execute(
        """
        UPDATE users
        SET role = 'owner'
        FROM households
        WHERE users.id = households.owner_id
        """
    )

    # 3. Set remaining users (if any) to 'member'
    op.execute(
        """
        UPDATE users
        SET role = 'member'
        WHERE role IS NULL
        """
    )

    # 4. Make role NOT NULL
    op.alter_column("users", "role", nullable=False)

    # 5. Drop FK constraint on households.owner_id
    op.drop_constraint("fk_households_owner_id", "households", type_="foreignkey")

    # 6. Drop owner_id column
    op.drop_column("households", "owner_id")


def downgrade() -> None:
    # 1. Re-add owner_id column (nullable initially)
    op.add_column(
        "households",
        sa.Column("owner_id", sa.String(36), nullable=True),
    )

    # 2. Backfill: set owner_id from users with role='owner'
    op.execute(
        """
        UPDATE households
        SET owner_id = u.id
        FROM users u
        WHERE u.household_id = households.id
          AND u.role = 'owner'
        """
    )

    # 3. For households with no owner, pick the first user
    op.execute(
        """
        UPDATE households
        SET owner_id = (
            SELECT u.id FROM users u
            WHERE u.household_id = households.id
            ORDER BY u.created_at ASC
            LIMIT 1
        )
        WHERE owner_id IS NULL
        """
    )

    # 4. Make owner_id NOT NULL
    op.alter_column("households", "owner_id", nullable=False)

    # 5. Re-add FK constraint
    op.create_foreign_key(
        "fk_households_owner_id",
        "households",
        "users",
        ["owner_id"],
        ["id"],
    )

    # 6. Drop role column from users
    op.drop_column("users", "role")
