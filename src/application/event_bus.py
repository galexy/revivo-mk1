"""In-process event bus for domain event publishing.

The event bus dispatches domain events to registered handlers after
UoW commit. Handlers are called asynchronously. Both sync and async
handlers are supported -- sync handlers are called directly, async
handlers are awaited.

For async or potentially-failing operations (email, external API),
handlers should enqueue jobs to the job queue.

Usage:
    from src.application import event_bus
    from src.domain.events.user_events import UserRegistered

    async def on_user_registered(event: UserRegistered) -> None:
        # Enqueue welcome email job
        await some_async_operation()

    event_bus.register(UserRegistered, on_user_registered)

    # Later, after UoW commit:
    await event_bus.publish_all(events)
"""

import inspect
from collections.abc import Callable
from typing import Any

from src.adapters.logging import get_logger

logger = get_logger(__name__)

# Handler registry: event_type -> list of handler functions
_handlers: dict[type, list[Callable[..., Any]]] = {}


def register(event_type: type, handler: Callable[..., Any]) -> None:
    """Register a handler for an event type.

    Multiple handlers can be registered for the same event type.
    Handlers are called in registration order. Both sync and async
    handlers are supported.

    Args:
        event_type: The type of event to handle (e.g., UserRegistered)
        handler: A callable (sync or async) that takes an event and handles it
    """
    _handlers.setdefault(event_type, []).append(handler)
    logger.debug(
        "handler_registered",
        event_type=event_type.__name__,
        handler=handler.__name__,
    )


async def publish(event: Any) -> None:
    """Publish event to all registered handlers.

    Supports both sync and async handlers. Async handlers are awaited,
    sync handlers are called directly. This allows handlers to use
    async operations like Procrastinate's defer_async().

    If a handler raises an exception, it is logged and re-raised
    to fail fast during development. No PII is logged - only
    event_type and handler name.

    Args:
        event: The domain event to publish
    """
    event_type = type(event)
    handlers = _handlers.get(event_type, [])

    for handler in handlers:
        try:
            logger.info(
                "handling_event",
                event_type=event_type.__name__,
                handler=handler.__name__,
            )
            if inspect.iscoroutinefunction(handler):
                await handler(event)
            else:
                handler(event)
        except Exception:
            logger.exception(
                "handler_failed",
                event_type=event_type.__name__,
                handler=handler.__name__,
            )
            raise


async def publish_all(events: list[Any]) -> None:
    """Publish multiple events in order.

    Events are published one at a time in the order provided.
    If any handler fails, subsequent events will not be published.
    Supports both sync and async handlers.

    Args:
        events: List of domain events to publish
    """
    for event in events:
        await publish(event)


def clear_handlers() -> None:
    """Clear all handlers.

    Used for testing to ensure test isolation.
    """
    _handlers.clear()
