"""Schema parity test - verifies Alembic migrations match SQLAlchemy metadata.

This test ensures the Alembic migration chain produces the same schema as
the SQLAlchemy metadata defined in tables.py. This guards against drift
between the two (e.g., adding a column to tables.py but forgetting to
generate a migration).

This test is independent of other integration tests - it manages its own
database schema lifecycle (drops/creates public schema) and does NOT use
the session-scoped setup_database fixture.

Drift detection catches:
- Column added to tables.py but no migration generated
- Column removed from tables.py but no migration generated
- FK constraint in tables.py but missing from migration chain
- Index in tables.py but missing from migration chain
- Type mismatch between tables.py and migration chain
"""

import os

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, text

import src.adapters.persistence.orm.tables  # noqa: F401  # pyright: ignore[reportUnusedImport] -- registers tables with metadata
from src.adapters.persistence.orm.base import metadata


def get_test_database_url() -> str:
    """Get database URL for testing."""
    return os.getenv(
        "TEST_DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/finance_test",
    )


@pytest.fixture(scope="module")
def migration_engine():
    """Create engine and run Alembic migrations for drift detection.

    This fixture:
    1. Creates a clean database (drops/recreates public schema)
    2. Runs alembic upgrade head to apply all migrations
    3. Yields the engine for comparison
    4. Cleans up by dropping/recreating public schema

    Module-scoped to run migrations once per test file.
    """
    database_url = get_test_database_url()

    # Set DATABASE_URL_SYNC so alembic env.py uses the test database
    # (env.py reads from environment, not just config)
    original_db_url_sync = os.environ.get("DATABASE_URL_SYNC")
    os.environ["DATABASE_URL_SYNC"] = database_url

    engine = create_engine(database_url, echo=False)

    # Drop and recreate public schema for clean slate
    with engine.connect() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
        conn.commit()

    # Configure Alembic to use test database
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", database_url)

    # Run all migrations
    command.upgrade(alembic_cfg, "head")

    yield engine

    # Cleanup: drop and recreate public schema
    with engine.connect() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
        conn.commit()

    engine.dispose()

    # Restore original DATABASE_URL_SYNC
    if original_db_url_sync is not None:
        os.environ["DATABASE_URL_SYNC"] = original_db_url_sync
    elif "DATABASE_URL_SYNC" in os.environ:
        del os.environ["DATABASE_URL_SYNC"]


def format_diff(diff: tuple) -> str:
    """Format a single diff tuple into a human-readable message."""
    diff_type = diff[0]

    if diff_type == "add_table":
        return f"Table missing from migrations: {diff[1].name}"
    if diff_type == "remove_table":
        return f"Table in migrations but not in metadata: {diff[1].name}"
    if diff_type == "add_column":
        table_name = diff[2] if isinstance(diff[2], str) else diff[2].name
        column = diff[3]
        return f"Column missing from migrations: {table_name}.{column.name}"
    if diff_type == "remove_column":
        table_name = diff[2] if isinstance(diff[2], str) else diff[2].name
        column = diff[3]
        return f"Column in migrations but not in metadata: {table_name}.{column.name}"
    if diff_type == "modify_type":
        table_name = diff[2]
        column_name = diff[3]
        return f"Type mismatch for {table_name}.{column_name}: migrations have {diff[6]} but metadata has {diff[5]}"
    if diff_type == "modify_nullable":
        table_name = diff[2]
        column_name = diff[3]
        return f"Nullable mismatch for {table_name}.{column_name}: migrations have nullable={diff[6]} but metadata has nullable={diff[5]}"
    if diff_type == "add_constraint":
        return f"Constraint missing from migrations: {diff[1].name}"
    if diff_type == "remove_constraint":
        return f"Constraint in migrations but not in metadata: {diff[1].name}"
    if diff_type == "add_index":
        return f"Index missing from migrations: {diff[1].name}"
    if diff_type == "remove_index":
        return f"Index in migrations but not in metadata: {diff[1].name}"
    if diff_type == "add_fk":
        return f"FK constraint missing from migrations: {diff[1].name}"
    if diff_type == "remove_fk":
        return f"FK constraint in migrations but not in metadata: {diff[1].name}"
    return f"Schema difference: {diff}"


def test_migrations_match_metadata(migration_engine):
    """Verify Alembic migration chain produces schema matching SQLAlchemy metadata.

    This test:
    1. Uses the migration_engine fixture (which ran alembic upgrade head)
    2. Creates a MigrationContext with compare_type=True
    3. Calls compare_metadata() to get diffs between DB and metadata
    4. Asserts no diffs exist

    If this test fails, it means tables.py was modified without generating
    a corresponding Alembic migration. Run:
        alembic revision --autogenerate -m "description"
    """
    with migration_engine.connect() as connection:
        # Create migration context with type comparison enabled
        migration_context = MigrationContext.configure(
            connection, opts={"compare_type": True}
        )

        # Compare database schema (from migrations) against metadata (from tables.py)
        diffs = compare_metadata(migration_context, metadata)

        if diffs:
            # Format each diff into a readable message
            messages = [format_diff(diff) for diff in diffs]
            diff_report = "\n".join(f"  - {msg}" for msg in messages)

            pytest.fail(
                f"Schema drift detected between Alembic migrations and SQLAlchemy metadata!\n\n"
                f"Differences found:\n{diff_report}\n\n"
                f"To fix: Edit tables.py as needed, then run:\n"
                f"  alembic revision --autogenerate -m 'description of change'\n"
                f"  alembic check  # confirm no remaining drift\n"
                f"  alembic upgrade head  # apply to real database"
            )
