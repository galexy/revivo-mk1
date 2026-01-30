"""Integration tests for database and migrations."""

import json
from datetime import UTC, datetime

import pytest
from sqlalchemy import insert, select, text
from sqlalchemy.exc import IntegrityError

from src.adapters.persistence.orm.tables import encrypted_secrets, outbox, users
from src.domain.model.entity_id import UserId


class TestDatabaseTables:
    """Test that database tables exist and work correctly."""

    def test_outbox_table_exists(self, session):
        """Outbox table can be queried."""
        result = session.execute(select(outbox)).fetchall()
        assert result == []  # Empty but queryable

    def test_users_table_exists(self, session):
        """Users table can be queried."""
        result = session.execute(select(users)).fetchall()
        assert result == []

    def test_encrypted_secrets_table_exists(self, session):
        """Encrypted secrets table can be queried."""
        result = session.execute(select(encrypted_secrets)).fetchall()
        assert result == []


class TestOutboxPattern:
    """Test outbox pattern for domain events."""

    def test_can_insert_event_to_outbox(self, session):
        """Events can be inserted into outbox table."""
        session.execute(
            insert(outbox).values(
                event_type="TestEvent",
                aggregate_type="TestAggregate",
                aggregate_id="test_123",
                payload=json.dumps({"key": "value"}),
                created_at=datetime.now(UTC),
            )
        )
        session.commit()

        result = session.execute(
            select(outbox).where(outbox.c.aggregate_id == "test_123")
        ).fetchone()

        assert result is not None
        assert result.event_type == "TestEvent"
        assert result.processed_at is None

    def test_can_mark_event_as_processed(self, session):
        """Events can be marked as processed."""
        # Insert event
        session.execute(
            insert(outbox).values(
                event_type="TestEvent",
                aggregate_type="TestAggregate",
                aggregate_id="test_456",
                payload="{}",
                created_at=datetime.now(UTC),
            )
        )
        session.commit()

        # Mark as processed
        session.execute(
            text(
                "UPDATE outbox SET processed_at = :now WHERE aggregate_id = :id"
            ).bindparams(now=datetime.now(UTC), id="test_456")
        )
        session.commit()

        result = session.execute(
            select(outbox).where(outbox.c.aggregate_id == "test_456")
        ).fetchone()

        assert result.processed_at is not None

    def test_unprocessed_index_filters_correctly(self, session):
        """Partial index on processed_at = NULL works."""
        # Insert processed event
        session.execute(
            insert(outbox).values(
                event_type="ProcessedEvent",
                aggregate_type="Test",
                aggregate_id="processed_1",
                payload="{}",
                created_at=datetime.now(UTC),
                processed_at=datetime.now(UTC),
            )
        )
        # Insert unprocessed event
        session.execute(
            insert(outbox).values(
                event_type="UnprocessedEvent",
                aggregate_type="Test",
                aggregate_id="unprocessed_1",
                payload="{}",
                created_at=datetime.now(UTC),
                processed_at=None,
            )
        )
        session.commit()

        # Query for unprocessed events
        result = session.execute(
            select(outbox).where(outbox.c.processed_at.is_(None))
        ).fetchall()

        assert len(result) == 1
        assert result[0].aggregate_id == "unprocessed_1"


class TestUserTable:
    """Test users table operations."""

    def test_can_insert_user(self, session):
        """Users can be inserted."""
        user_id = UserId.generate()
        session.execute(
            insert(users).values(
                id=user_id.value,
                email="test@example.com",
                email_verified=False,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        )
        session.commit()

        result = session.execute(
            select(users).where(users.c.id == user_id.value)
        ).fetchone()

        assert result is not None
        assert result.email == "test@example.com"
        assert result.id.startswith("user_")

    def test_email_must_be_unique(self, session):
        """Email uniqueness constraint is enforced."""
        user_id_1 = UserId.generate()
        user_id_2 = UserId.generate()

        session.execute(
            insert(users).values(
                id=user_id_1.value,
                email="duplicate@example.com",
                email_verified=False,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        )
        session.commit()

        with pytest.raises(IntegrityError):
            session.execute(
                insert(users).values(
                    id=user_id_2.value,
                    email="duplicate@example.com",  # Same email
                    email_verified=False,
                    created_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC),
                )
            )
            session.commit()


class TestEncryptedSecretsTable:
    """Test encrypted secrets storage."""

    def test_can_store_encrypted_secret(self, session, field_encryption):
        """Encrypted secrets can be stored."""
        user_id = UserId.generate()

        # Create user first (FK constraint)
        session.execute(
            insert(users).values(
                id=user_id.value,
                email="secrets@example.com",
                email_verified=False,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        )

        encrypted_value = field_encryption.encrypt("plaid_access_token_xxx")

        session.execute(
            insert(encrypted_secrets).values(
                user_id=user_id.value,
                secret_type="plaid_access_token",
                encrypted_value=encrypted_value,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        )
        session.commit()

        result = session.execute(
            select(encrypted_secrets).where(
                encrypted_secrets.c.user_id == user_id.value
            )
        ).fetchone()

        assert result is not None
        assert result.secret_type == "plaid_access_token"
        # Verify we stored encrypted, not plaintext
        assert result.encrypted_value != "plaid_access_token_xxx"
        # Verify we can decrypt
        decrypted = field_encryption.decrypt(result.encrypted_value)
        assert decrypted == "plaid_access_token_xxx"

    def test_user_secret_type_unique_constraint(self, session, field_encryption):
        """Each user can have only one secret of each type."""
        user_id = UserId.generate()

        session.execute(
            insert(users).values(
                id=user_id.value,
                email="unique@example.com",
                email_verified=False,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        )

        # First secret
        session.execute(
            insert(encrypted_secrets).values(
                user_id=user_id.value,
                secret_type="plaid_access_token",
                encrypted_value=field_encryption.encrypt("token1"),
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        )
        session.commit()

        # Duplicate should fail
        with pytest.raises(IntegrityError):
            session.execute(
                insert(encrypted_secrets).values(
                    user_id=user_id.value,
                    secret_type="plaid_access_token",  # Same type
                    encrypted_value=field_encryption.encrypt("token2"),
                    created_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC),
                )
            )
            session.commit()
