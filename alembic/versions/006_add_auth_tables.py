"""Add authentication tables and household scoping.

Phase 4: Authentication Infrastructure

This migration:
1. Creates households table (multi-user data ownership scope)
2. Expands users table with display_name, password_hash, household_id
3. Creates refresh_tokens table (JWT token rotation)
4. Adds household_id to accounts, transactions, categories, payees
5. Creates "Default" household and migrates existing data

Bootstrap problem: households.owner_id references users, users.household_id
references households. Solved by:
- Creating households without FK on owner_id first
- Adding columns as nullable
- Inserting default household
- Updating existing data
- Adding NOT NULL constraints and FKs last

Revision ID: 006
Revises: 005
Create Date: 2026-02-05
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Well-known default household ID for data migration
DEFAULT_HOUSEHOLD_ID = "hh_00000000000000000000000000"
DEFAULT_HOUSEHOLD_NAME = "Default"


def upgrade() -> None:
    # =========================================================================
    # 1. Create households table (owner_id FK deferred to avoid circular dep)
    # =========================================================================
    op.create_table(
        "households",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("owner_id", sa.String(36), nullable=True),  # Nullable initially
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # =========================================================================
    # 2. Add new columns to users table
    # =========================================================================
    op.add_column(
        "users",
        sa.Column("display_name", sa.String(255), nullable=True),  # Nullable initially
    )
    op.add_column(
        "users",
        sa.Column("password_hash", sa.String(255), nullable=True),  # Nullable initially
    )
    op.add_column(
        "users",
        sa.Column("household_id", sa.String(36), nullable=True),  # Nullable initially
    )
    op.add_column(
        "users",
        sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True),
    )

    # =========================================================================
    # 3. Create refresh_tokens table
    # =========================================================================
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("token_family", sa.String(36), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE"
        ),
        sa.Index("ix_refresh_tokens_user_id", "user_id"),
        sa.Index("ix_refresh_tokens_token_hash", "token_hash", unique=True),
        sa.Index("ix_refresh_tokens_family", "token_family"),
    )

    # =========================================================================
    # 4. Add household_id columns to existing tables (nullable initially)
    # =========================================================================
    for table_name in ("accounts", "transactions", "categories", "payees"):
        op.add_column(
            table_name,
            sa.Column("household_id", sa.String(36), nullable=True),
        )

    # =========================================================================
    # 5. Data migration: create default household, update existing records
    # =========================================================================
    conn = op.get_bind()

    # Insert the default household
    conn.execute(
        sa.text(
            """
            INSERT INTO households (id, name, owner_id, created_at, updated_at)
            VALUES (:id, :name, NULL, NOW(), NOW())
            """
        ),
        {"id": DEFAULT_HOUSEHOLD_ID, "name": DEFAULT_HOUSEHOLD_NAME},
    )

    # Set the first existing user as household owner (if any users exist)
    conn.execute(
        sa.text(
            """
            UPDATE households
            SET owner_id = (SELECT id FROM users ORDER BY created_at ASC LIMIT 1)
            WHERE id = :hh_id
            AND EXISTS (SELECT 1 FROM users)
            """
        ),
        {"hh_id": DEFAULT_HOUSEHOLD_ID},
    )

    # Assign all existing users to the default household and set defaults
    # for new required fields
    conn.execute(
        sa.text(
            """
            UPDATE users
            SET household_id = :hh_id,
                display_name = COALESCE(display_name, split_part(email, '@', 1)),
                password_hash = COALESCE(password_hash, '$placeholder$not-a-real-hash')
            WHERE household_id IS NULL
            """
        ),
        {"hh_id": DEFAULT_HOUSEHOLD_ID},
    )

    # Assign all existing data to the default household
    for table_name in ("accounts", "transactions", "categories", "payees"):
        conn.execute(
            sa.text(
                f"UPDATE {table_name} SET household_id = :hh_id WHERE household_id IS NULL"
            ),
            {"hh_id": DEFAULT_HOUSEHOLD_ID},
        )

    # =========================================================================
    # 6. Add NOT NULL constraints now that data is migrated
    # =========================================================================
    op.alter_column("users", "display_name", nullable=False)
    op.alter_column("users", "password_hash", nullable=False)
    op.alter_column("users", "household_id", nullable=False)
    # Only set NOT NULL if there are households with owner_id populated
    # On fresh databases, the default household has no owner (no users exist yet)
    has_owners = conn.execute(
        sa.text("SELECT EXISTS(SELECT 1 FROM households WHERE owner_id IS NOT NULL)")
    ).scalar()
    if has_owners:
        op.alter_column("households", "owner_id", nullable=False)

    for table_name in ("accounts", "transactions", "categories", "payees"):
        op.alter_column(table_name, "household_id", nullable=False)

    # =========================================================================
    # 7. Add foreign key constraints and indexes
    # =========================================================================

    # users.household_id -> households.id
    op.create_foreign_key(
        "fk_users_household_id",
        "users",
        "households",
        ["household_id"],
        ["id"],
    )
    op.create_index("ix_users_household_id", "users", ["household_id"])

    # households.owner_id -> users.id (deferred from creation)
    op.create_foreign_key(
        "fk_households_owner_id",
        "households",
        "users",
        ["owner_id"],
        ["id"],
    )

    # household_id FKs and indexes on existing tables
    for table_name in ("accounts", "transactions", "categories", "payees"):
        op.create_foreign_key(
            f"fk_{table_name}_household_id",
            table_name,
            "households",
            ["household_id"],
            ["id"],
        )
        op.create_index(
            f"ix_{table_name}_household_id",
            table_name,
            ["household_id"],
        )

    # =========================================================================
    # 8. Add unique email index (if not already present from initial migration)
    # =========================================================================
    # The initial migration created a UNIQUE constraint on email, but we add
    # an explicit named index for consistency with the table definition
    try:
        op.create_index("ix_users_email", "users", ["email"], unique=True)
    except Exception:
        pass  # Index may already exist from UNIQUE constraint


def downgrade() -> None:
    # =========================================================================
    # Remove in reverse order
    # =========================================================================

    # Drop email index (if we created it)
    try:
        op.drop_index("ix_users_email", table_name="users")
    except Exception:
        pass

    # Drop household_id FKs and indexes on existing tables
    for table_name in ("accounts", "transactions", "categories", "payees"):
        op.drop_index(f"ix_{table_name}_household_id", table_name=table_name)
        op.drop_constraint(f"fk_{table_name}_household_id", table_name, type_="foreignkey")

    # Drop households FK constraints
    op.drop_constraint("fk_households_owner_id", "households", type_="foreignkey")
    op.drop_index("ix_users_household_id", table_name="users")
    op.drop_constraint("fk_users_household_id", "users", type_="foreignkey")

    # Drop household_id columns from existing tables
    for table_name in ("accounts", "transactions", "categories", "payees"):
        op.drop_column(table_name, "household_id")

    # Drop refresh_tokens table
    op.drop_table("refresh_tokens")

    # Drop new columns from users
    op.drop_column("users", "email_verified_at")
    op.drop_column("users", "household_id")
    op.drop_column("users", "password_hash")
    op.drop_column("users", "display_name")

    # Drop households table
    op.drop_table("households")
