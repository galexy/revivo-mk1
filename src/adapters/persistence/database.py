"""Database connection management.

Provides factory functions for creating SQLAlchemy engines and sessions.
Supports both synchronous (for migrations, scripts) and asynchronous
(for API) database access.

Database URL is read from environment with a default suitable for
local Docker Compose development.
"""

import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session, sessionmaker


def get_database_url() -> str:
    """Get database URL from environment.

    Returns:
        PostgreSQL connection string. Defaults to Docker Compose postgres service.
    """
    return os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@postgres:5432/finance",
    )


def get_async_database_url() -> str:
    """Get async database URL (asyncpg driver).

    Converts standard PostgreSQL URL to use asyncpg driver.

    Returns:
        PostgreSQL+asyncpg connection string.
    """
    url = get_database_url()
    return url.replace("postgresql://", "postgresql+asyncpg://")


def create_sync_engine(echo: bool = False):
    """Create synchronous database engine.

    Used for:
    - Alembic migrations
    - Scripts and one-off commands
    - Tests that don't require async

    Args:
        echo: If True, log all SQL statements.

    Returns:
        SQLAlchemy sync Engine.
    """
    url = get_database_url()
    # Ensure we use psycopg2 (sync) driver, not asyncpg
    url = url.replace("postgresql+asyncpg://", "postgresql://")
    return create_engine(url, echo=echo)


def create_async_engine_instance(echo: bool = False):
    """Create asynchronous database engine.

    Used for:
    - FastAPI endpoints
    - Async application code

    Args:
        echo: If True, log all SQL statements.

    Returns:
        SQLAlchemy async Engine.
    """
    return create_async_engine(get_async_database_url(), echo=echo)


def create_sync_session_factory(echo: bool = False) -> sessionmaker[Session]:
    """Create session factory for synchronous sessions.

    Args:
        echo: If True, log all SQL statements.

    Returns:
        Sessionmaker that creates sync Session instances.
    """
    engine = create_sync_engine(echo=echo)
    return sessionmaker(bind=engine, expire_on_commit=False)


def create_async_session_factory(
    echo: bool = False,
) -> async_sessionmaker[AsyncSession]:
    """Create session factory for asynchronous sessions.

    Args:
        echo: If True, log all SQL statements.

    Returns:
        Async sessionmaker that creates AsyncSession instances.
    """
    engine = create_async_engine_instance(echo=echo)
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


def get_session(
    session_factory: sessionmaker[Session] | None = None,
) -> Generator[Session, None, None]:
    """Dependency for sync session (migrations, scripts).

    Args:
        session_factory: Optional session factory. If not provided,
            creates a new one with default settings.

    Yields:
        SQLAlchemy Session that is closed after use.
    """
    factory = session_factory or create_sync_session_factory()
    session = factory()
    try:
        yield session
    finally:
        session.close()
