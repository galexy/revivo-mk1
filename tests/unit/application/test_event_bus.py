"""Unit tests for in-process event bus."""

import asyncio
from dataclasses import dataclass

import pytest

from src.application import event_bus


@dataclass(frozen=True)
class SampleEvent:
    """Simple test event for unit tests."""

    value: str


@dataclass(frozen=True)
class AnotherSampleEvent:
    """Another test event type for testing multiple handlers."""

    number: int


@pytest.fixture(autouse=True)
def clear_handlers_after_test():
    """Clear all handlers after each test for isolation."""
    yield
    event_bus.clear_handlers()


class TestRegister:
    """Tests for event_bus.register()."""

    def test_register_handler_for_event_type(self):
        """Handler is stored in registry after registration."""
        calls: list[SampleEvent] = []

        def handler(event: SampleEvent) -> None:
            calls.append(event)

        event_bus.register(SampleEvent, handler)

        # Verify handler is registered by publishing an event
        test_event = SampleEvent(value="test")
        asyncio.run(event_bus.publish(test_event))

        assert len(calls) == 1
        assert calls[0] == test_event

    def test_register_multiple_handlers_for_same_event_type(self):
        """Multiple handlers can be registered for the same event type."""
        calls: list[str] = []

        def handler_one(event: SampleEvent) -> None:
            calls.append("one")

        def handler_two(event: SampleEvent) -> None:
            calls.append("two")

        event_bus.register(SampleEvent, handler_one)
        event_bus.register(SampleEvent, handler_two)

        asyncio.run(event_bus.publish(SampleEvent(value="test")))

        assert calls == ["one", "two"]


class TestPublish:
    """Tests for event_bus.publish()."""

    def test_publish_calls_registered_handler(self):
        """Publish invokes handler with the event."""
        received_events: list[SampleEvent] = []

        def handler(event: SampleEvent) -> None:
            received_events.append(event)

        event_bus.register(SampleEvent, handler)

        test_event = SampleEvent(value="hello")
        asyncio.run(event_bus.publish(test_event))

        assert len(received_events) == 1
        assert received_events[0] == test_event
        assert received_events[0].value == "hello"

    def test_publish_to_multiple_handlers(self):
        """All handlers are called in registration order."""
        call_order: list[int] = []

        def handler_first(event: SampleEvent) -> None:
            call_order.append(1)

        def handler_second(event: SampleEvent) -> None:
            call_order.append(2)

        def handler_third(event: SampleEvent) -> None:
            call_order.append(3)

        event_bus.register(SampleEvent, handler_first)
        event_bus.register(SampleEvent, handler_second)
        event_bus.register(SampleEvent, handler_third)

        asyncio.run(event_bus.publish(SampleEvent(value="test")))

        assert call_order == [1, 2, 3]

    def test_publish_unregistered_event_type(self):
        """Publishing an event with no registered handlers does not error."""
        # Register handler for a different event type
        calls: list[SampleEvent] = []

        def handler(event: SampleEvent) -> None:
            calls.append(event)

        event_bus.register(SampleEvent, handler)

        # Publish a different event type - should not error
        asyncio.run(event_bus.publish(AnotherSampleEvent(number=42)))

        # Original handler should not have been called
        assert len(calls) == 0

    def test_handler_exception_propagates(self):
        """Exception from handler is re-raised after logging."""

        def failing_handler(event: SampleEvent) -> None:
            msg = "Handler failed intentionally"
            raise ValueError(msg)

        event_bus.register(SampleEvent, failing_handler)

        with pytest.raises(ValueError, match="Handler failed intentionally"):
            asyncio.run(event_bus.publish(SampleEvent(value="test")))


class TestPublishAll:
    """Tests for event_bus.publish_all()."""

    def test_publish_all_dispatches_multiple_events(self):
        """Each event goes to its registered handlers."""
        test_events: list[SampleEvent] = []
        other_events: list[AnotherSampleEvent] = []

        def test_handler(event: SampleEvent) -> None:
            test_events.append(event)

        def other_handler(event: AnotherSampleEvent) -> None:
            other_events.append(event)

        event_bus.register(SampleEvent, test_handler)
        event_bus.register(AnotherSampleEvent, other_handler)

        events = [
            SampleEvent(value="first"),
            AnotherSampleEvent(number=1),
            SampleEvent(value="second"),
            AnotherSampleEvent(number=2),
        ]
        asyncio.run(event_bus.publish_all(events))

        assert len(test_events) == 2
        assert test_events[0].value == "first"
        assert test_events[1].value == "second"

        assert len(other_events) == 2
        assert other_events[0].number == 1
        assert other_events[1].number == 2

    def test_publish_all_preserves_order(self):
        """Events are published in the order provided."""
        received: list[str] = []

        def handler(event: SampleEvent) -> None:
            received.append(event.value)

        event_bus.register(SampleEvent, handler)

        events = [
            SampleEvent(value="a"),
            SampleEvent(value="b"),
            SampleEvent(value="c"),
        ]
        asyncio.run(event_bus.publish_all(events))

        assert received == ["a", "b", "c"]


class TestClearHandlers:
    """Tests for event_bus.clear_handlers()."""

    def test_clear_handlers(self):
        """Registry is empty after clear."""
        calls: list[SampleEvent] = []

        def handler(event: SampleEvent) -> None:
            calls.append(event)

        event_bus.register(SampleEvent, handler)

        # Verify handler is registered
        asyncio.run(event_bus.publish(SampleEvent(value="before")))
        assert len(calls) == 1

        # Clear handlers
        event_bus.clear_handlers()

        # Verify handler is no longer registered
        asyncio.run(event_bus.publish(SampleEvent(value="after")))
        assert len(calls) == 1  # Still 1, no new calls
