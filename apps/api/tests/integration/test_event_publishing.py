"""Integration tests for event publishing.

Tests the flow from UoW commit through event bus to handlers.
Verifies that:
1. UoW publishes events after commit
2. Registered handlers are called
3. Multiple handlers for same event type all get called
4. Handler registration works correctly
"""

import asyncio
import os
from typing import Any

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from domain.events.user_events import EmailVerified, UserRegistered
from domain.model.household import Household
from domain.model.user import User
from src.adapters.persistence.orm.base import metadata
from src.adapters.persistence.orm.mappers import clear_mappers, start_mappers
from src.adapters.persistence.unit_of_work import SqlAlchemyUnitOfWork
from src.application import event_bus


@pytest.fixture(scope="module")
def database_url():
    """Get test database URL."""
    return os.getenv(
        "TEST_DATABASE_URL",
        "postgresql://postgres:postgres@postgres:5432/finance_test",
    )


@pytest.fixture(scope="module")
def engine(database_url):
    """Create database engine for tests."""
    return create_engine(database_url, echo=False)


@pytest.fixture(scope="module")
def setup_database(engine, database_url):
    """Set up test database with fresh tables."""
    os.environ["DATABASE_URL"] = database_url

    clear_mappers()
    start_mappers()

    metadata.drop_all(engine)
    metadata.create_all(engine)

    yield

    clear_mappers()


@pytest.fixture
def session_factory(engine, setup_database):
    """Create session factory for UoW."""
    return sessionmaker(bind=engine)


@pytest.fixture(autouse=True)
def clear_event_handlers():
    """Clear event handlers before and after each test."""
    event_bus.clear_handlers()
    yield
    event_bus.clear_handlers()


class TestEventBusRegistration:
    """Tests for event handler registration."""

    def test_register_handler_for_event_type(self) -> None:
        """Handler can be registered for specific event type."""
        received: list[Any] = []

        def handler(event: UserRegistered) -> None:
            received.append(event)

        event_bus.register(UserRegistered, handler)

        event = UserRegistered(
            user_id="user_123",
            email="test@example.com",
            household_id="hh_123",
        )
        asyncio.run(event_bus.publish(event))

        assert len(received) == 1
        assert received[0] is event

    def test_multiple_handlers_for_same_event_type(self) -> None:
        """Multiple handlers can be registered for same event type."""
        handler1_called = []
        handler2_called = []

        def handler1(event: UserRegistered) -> None:
            handler1_called.append(event)

        def handler2(event: UserRegistered) -> None:
            handler2_called.append(event)

        event_bus.register(UserRegistered, handler1)
        event_bus.register(UserRegistered, handler2)

        event = UserRegistered(
            user_id="user_123",
            email="test@example.com",
            household_id="hh_123",
        )
        asyncio.run(event_bus.publish(event))

        assert len(handler1_called) == 1
        assert len(handler2_called) == 1

    def test_handler_only_receives_registered_event_type(self) -> None:
        """Handler only receives events of its registered type."""
        user_registered_events: list[Any] = []
        email_verified_events: list[Any] = []

        def on_user_registered(event: UserRegistered) -> None:
            user_registered_events.append(event)

        def on_email_verified(event: EmailVerified) -> None:
            email_verified_events.append(event)

        event_bus.register(UserRegistered, on_user_registered)
        event_bus.register(EmailVerified, on_email_verified)

        asyncio.run(
            event_bus.publish(
                UserRegistered(
                    user_id="user_123",
                    email="test@example.com",
                    household_id="hh_123",
                )
            )
        )

        assert len(user_registered_events) == 1
        assert len(email_verified_events) == 0

    def test_no_handler_registered_does_not_error(self) -> None:
        """Publishing event with no handlers does not raise."""
        event = UserRegistered(
            user_id="user_123",
            email="test@example.com",
            household_id="hh_123",
        )
        # Should not raise
        asyncio.run(event_bus.publish(event))

    def test_clear_handlers_removes_all(self) -> None:
        """clear_handlers removes all registered handlers."""
        received: list[Any] = []

        def handler(event: UserRegistered) -> None:
            received.append(event)

        event_bus.register(UserRegistered, handler)
        event_bus.clear_handlers()

        event = UserRegistered(
            user_id="user_123",
            email="test@example.com",
            household_id="hh_123",
        )
        asyncio.run(event_bus.publish(event))

        assert len(received) == 0


class TestUnitOfWorkEventPublishing:
    """Tests for UoW publishing events after commit."""

    def test_uow_commit_publishes_events(self, session_factory: sessionmaker) -> None:
        """Events collected by UoW are published after commit."""
        received_events: list[Any] = []

        def test_handler(event: UserRegistered) -> None:
            received_events.append(event)

        event_bus.register(UserRegistered, test_handler)

        uow = SqlAlchemyUnitOfWork(session_factory)
        with uow:
            # Create user and household to generate event
            household = Household.create(name="Test Household")
            user = User.create(
                email="test@example.com",
                password_hash="hash",
                display_name="Test User",
                household_id=household.id,
            )

            # Collect events from user
            events = user.collect_events()
            uow.collect_events(events)

            # Add entities
            uow.households.add(household)
            uow.users.add(user)

            # Commit - should publish events
            asyncio.run(uow.commit())

        assert len(received_events) == 1
        assert isinstance(received_events[0], UserRegistered)
        assert received_events[0].email == "test@example.com"

    def test_events_not_published_on_rollback(
        self, session_factory: sessionmaker
    ) -> None:
        """Events are NOT published if transaction is rolled back."""
        received_events: list[Any] = []

        def test_handler(event: UserRegistered) -> None:
            received_events.append(event)

        event_bus.register(UserRegistered, test_handler)

        uow = SqlAlchemyUnitOfWork(session_factory)
        try:
            with uow:
                household = Household.create(name="Test Household")
                user = User.create(
                    email="rollback@example.com",
                    password_hash="hash",
                    display_name="Rollback User",
                    household_id=household.id,
                )

                events = user.collect_events()
                uow.collect_events(events)

                # Force rollback by raising exception
                raise ValueError("Test rollback")
        except ValueError:
            pass

        # Events should NOT have been published
        assert len(received_events) == 0

    def test_handler_receives_event_after_commit(
        self, session_factory: sessionmaker
    ) -> None:
        """Handler is called AFTER commit (can see committed data)."""
        commit_order: list[str] = []

        def test_handler(event: UserRegistered) -> None:
            commit_order.append("handler_called")

        event_bus.register(UserRegistered, test_handler)

        uow = SqlAlchemyUnitOfWork(session_factory)
        with uow:
            household = Household.create(name="Order Test Household")
            user = User.create(
                email="order@example.com",
                password_hash="hash",
                display_name="Order User",
                household_id=household.id,
            )

            events = user.collect_events()
            uow.collect_events(events)

            uow.households.add(household)
            uow.users.add(user)

            commit_order.append("before_commit")
            asyncio.run(uow.commit())
            commit_order.append("after_commit")

        # Handler called during commit, before "after_commit"
        assert commit_order == ["before_commit", "handler_called", "after_commit"]


class TestHandlerRegistration:
    """Tests for the register_all_handlers function."""

    def test_register_all_handlers_registers_user_handlers(self) -> None:
        """register_all_handlers sets up user event handlers."""
        from src.application.handlers import register_all_handlers

        register_all_handlers()

        # Check that handlers are registered by publishing an event
        # The handlers just log, so we verify no exception is raised
        event = UserRegistered(
            user_id="user_123",
            email="test@example.com",
            household_id="hh_123",
        )
        # Should not raise
        asyncio.run(event_bus.publish(event))

        verified_event = EmailVerified(
            user_id="user_123",
            email="test@example.com",
        )
        # Should not raise
        asyncio.run(event_bus.publish(verified_event))
