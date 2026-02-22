"""Integration test fixtures.

Provides database and encryption fixtures for integration tests.
Database fixtures use transactional isolation - each test runs in a
transaction that is rolled back after the test completes.
"""

import base64
import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.adapters.persistence.orm.base import metadata
from src.adapters.persistence.orm.mappers import clear_mappers, start_mappers
from src.adapters.security.encryption import FieldEncryption


@pytest.fixture(scope="session")
def database_url():
    """
    Database URL for tests.
    Uses TEST_DATABASE_URL if set, otherwise defaults to test database.
    """
    return os.getenv(
        "TEST_DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/finance_test",
    )


@pytest.fixture(scope="session")
def engine(database_url):
    """Create SQLAlchemy engine for tests."""
    return create_engine(database_url, echo=False)


@pytest.fixture(scope="session")
def setup_database(engine):
    """
    Create all tables for tests.
    Runs once per test session.
    """
    # Start mappers before creating tables
    start_mappers()

    # Drop and recreate all tables
    metadata.drop_all(engine)
    metadata.create_all(engine)

    yield

    # Cleanup after all tests
    metadata.drop_all(engine)
    clear_mappers()


@pytest.fixture
def session(engine, setup_database):
    """
    Provide a transactional session for each test.
    Rolls back after each test for isolation.
    """
    connection = engine.connect()
    transaction = connection.begin()
    test_session_factory = sessionmaker(bind=connection)
    session = test_session_factory()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def encryption_key():
    """Generate encryption key for tests."""
    return FieldEncryption.generate_key()


@pytest.fixture
def field_encryption(encryption_key):
    """Provide encryption service for tests."""
    return FieldEncryption(encryption_key)


@pytest.fixture
def env_encryption_key(encryption_key, monkeypatch):
    """Set up encryption key in environment."""
    encoded = base64.b64encode(encryption_key).decode()
    monkeypatch.setenv("ENCRYPTION_KEY", encoded)
    return encoded
