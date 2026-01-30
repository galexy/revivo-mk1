"""Alembic environment configuration.

This module configures Alembic for database migrations. Key features:
- Reads DATABASE_URL from environment (with local default)
- Imports our SQLAlchemy metadata for autogenerate support
- Supports both offline (SQL generation) and online (direct execution) modes
"""

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Import metadata for autogenerate support
# This enables `alembic revision --autogenerate` to detect changes
from src.adapters.persistence.orm.base import metadata

# Alembic Config object for access to .ini values
config = context.config

# Set database URL from environment (with default for local development)
# Note: For Docker Compose, postgres is the service name
# Use DATABASE_URL_SYNC if available (for migrations), otherwise DATABASE_URL
database_url = os.getenv(
    "DATABASE_URL_SYNC",
    os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/finance",
    ),
)
config.set_main_option("sqlalchemy.url", database_url)

# Set up Python logging from config file
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate support
# Alembic will compare the database against this metadata
target_metadata = metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This generates SQL without connecting to the database.
    Useful for generating migration SQL for review or for
    environments where direct database access isn't available.

    Usage: alembic upgrade head --sql
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    This connects to the database and applies migrations directly.
    Standard mode for development and production deployment.

    Usage: alembic upgrade head
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


# Entry point - choose mode based on context
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
