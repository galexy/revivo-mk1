# Phase 5: Domain Event Publishing - Research

**Researched:** 2026-02-06
**Domain:** Domain Events, Event Bus, PostgreSQL Job Queue
**Confidence:** HIGH

## Summary

This phase establishes infrastructure to publish and handle domain events that are already being collected via the Unit of Work pattern. The codebase has existing domain events (UserRegistered, EmailVerified, AccountCreated, TransactionCreated, etc.) that are written to an outbox table but not yet published to handlers.

The recommended approach is a **hybrid event architecture**: an in-process event bus dispatches events synchronously to handlers after transaction commit, and handlers can enqueue jobs to an async PostgreSQL-backed job queue for side effects (email, external calls). This maintains the existing UoW-managed event pattern while adding the ability to trigger behavior.

**Procrastinate** is the recommended job queue library. It is a mature, well-documented PostgreSQL-based task queue that integrates well with async Python/FastAPI, supports running workers in the same process as the API, provides retry strategies with exponential backoff, and has a Django admin integration that can serve as a model for job visibility (though we'll use CLI/shell for non-Django apps).

**Primary recommendation:** Use a simple in-process event bus (dict mapping event types to handlers) that dispatches after UoW commit, with Procrastinate for async job queue infrastructure in a separate PostgreSQL database.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| procrastinate | 3.5.x | PostgreSQL-based async job queue | Native async, PostgreSQL-only (no Redis), LISTEN/NOTIFY, mature |
| psycopg | 3.x | Async PostgreSQL driver for Procrastinate | Required by PsycopgConnector, already compatible with project |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| (none new) | - | Event bus is hand-rolled | Simple dict-based handler registry, no external dependency needed |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| procrastinate | PGQueuer | Newer library (Python 3.11+), less mature, no Django integration |
| procrastinate | Celery+Redis | Adds Redis dependency, more complex setup |
| procrastinate | APScheduler | Not distributed, runs in same process only |
| hand-rolled event bus | fastapi-events | ASGI middleware complexity, we need post-commit dispatch |

**Installation:**
```bash
pip install procrastinate psycopg[binary]
# or with uv:
uv add procrastinate psycopg[binary]
```

## Architecture Patterns

### Recommended Project Structure
```
src/
├── domain/
│   └── events/                    # Existing - domain events
│       ├── base.py
│       ├── user_events.py
│       ├── account_events.py
│       └── transaction_events.py
├── application/
│   ├── event_bus.py              # NEW - in-process event bus
│   └── handlers/                  # NEW - event handlers
│       ├── __init__.py
│       └── user_handlers.py
├── adapters/
│   └── jobs/                      # NEW - job queue infrastructure
│       ├── __init__.py
│       ├── app.py                 # Procrastinate app instance
│       ├── tasks.py               # Job definitions
│       └── config.py              # Job queue configuration
```

### Pattern 1: In-Process Event Bus with Handler Registry
**What:** A simple dictionary mapping event types to handler functions
**When to use:** After UoW commit, to dispatch events to registered handlers
**Example:**
```python
# Source: https://www.cosmicpython.com/book/chapter_08_events_and_message_bus.html
from typing import Callable, Type
from src.domain.events.base import DomainEvent

HANDLERS: dict[Type[DomainEvent], list[Callable]] = {}

def register(event_type: Type[DomainEvent], handler: Callable) -> None:
    """Register a handler for an event type."""
    HANDLERS.setdefault(event_type, []).append(handler)

def publish(event: DomainEvent) -> None:
    """Dispatch event to all registered handlers."""
    for handler in HANDLERS.get(type(event), []):
        handler(event)

def publish_all(events: list[DomainEvent]) -> None:
    """Dispatch multiple events."""
    for event in events:
        publish(event)
```

### Pattern 2: Procrastinate FastAPI Integration (Worker in Same Process)
**What:** Run Procrastinate worker alongside FastAPI in the same async event loop
**When to use:** When you want API and worker in one container without separate processes
**Example:**
```python
# Source: https://procrastinate.readthedocs.io/en/stable/howto/basics/worker.html
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from procrastinate import App, PsycopgConnector

# Procrastinate app with separate database
job_queue = App(
    connector=PsycopgConnector(
        conninfo="postgresql://user:pass@host:5432/jobs_db"
    )
)

@job_queue.task(queue="events")
async def send_welcome_email(user_id: str, email: str):
    """Async job for sending welcome email."""
    # Implementation in Phase 6
    pass

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with job_queue.open_async():
        worker = asyncio.create_task(
            job_queue.run_worker_async(install_signal_handlers=False)
        )
        yield
        worker.cancel()
        try:
            await asyncio.wait_for(worker, timeout=10)
        except (asyncio.TimeoutError, asyncio.CancelledError):
            pass

app = FastAPI(lifespan=lifespan)
```

### Pattern 3: Event Handler Enqueuing Jobs
**What:** Event handlers delegate to job queue for side effects
**When to use:** For any side effect that could fail or is slow (email, external API)
**Example:**
```python
# Source: Project CONTEXT.md decisions
from src.domain.events.user_events import UserRegistered
from src.adapters.jobs.app import job_queue
from src.adapters.jobs.tasks import send_welcome_email

async def handle_user_registered(event: UserRegistered) -> None:
    """Handle UserRegistered event by enqueuing welcome email job."""
    await send_welcome_email.defer_async(
        user_id=event.user_id,
        email=event.email,
    )
```

### Pattern 4: Retry Strategy with Exponential Backoff
**What:** Configure task retries with increasing delays
**When to use:** For jobs that may fail transiently (network issues, rate limits)
**Example:**
```python
# Source: https://procrastinate.readthedocs.io/en/stable/howto/advanced/retry.html
from procrastinate import RetryStrategy

email_retry = RetryStrategy(
    max_attempts=5,
    exponential_wait=60,  # 60s, then 3600s, then 216000s...
    retry_exceptions={ConnectionError, TimeoutError},
)

@job_queue.task(queue="email", retry=email_retry)
async def send_email(recipient: str, subject: str, body: str):
    """Send email with retry on connection failures."""
    pass
```

### Anti-Patterns to Avoid
- **Publishing events before commit:** Events dispatched before transaction commit can lead to inconsistent state if transaction rolls back. Always dispatch AFTER commit succeeds.
- **Blocking handlers in request path:** Heavy handlers (email, external API) should enqueue jobs, not block the HTTP response.
- **Mixing sync and async carelessly:** Procrastinate async tasks need async handlers. Use `defer_async()` from async code.
- **Logging PII in job payloads:** Per CONTEXT.md, only log job_id, event_type, status, retry_count. No email addresses or user data in logs.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Job persistence | Custom DB table + polling | Procrastinate | LISTEN/NOTIFY, FOR UPDATE SKIP LOCKED, proven at scale |
| Retry with backoff | Custom retry counter | Procrastinate RetryStrategy | Handles exponential backoff, max attempts, exception filtering |
| Dead letter handling | Custom "failed_jobs" table | Procrastinate failed status | Jobs stay in DB with "failed" status, queryable and retriable |
| Worker coordination | Custom lock table | Procrastinate | Uses PostgreSQL advisory locks, handles stalled workers |
| Job scheduling | Custom cron table | Procrastinate periodic tasks | Built-in periodic task support |

**Key insight:** PostgreSQL job queues require careful handling of concurrency (FOR UPDATE SKIP LOCKED), notification (LISTEN/NOTIFY), and failure modes. Procrastinate has solved these problems over years of production use.

## Common Pitfalls

### Pitfall 1: Publishing Events Before Transaction Commit
**What goes wrong:** Event handlers execute, then transaction rolls back. Side effects (emails sent) cannot be undone.
**Why it happens:** Natural to dispatch events immediately after aggregate mutation.
**How to avoid:** Collect events during UoW, dispatch only AFTER commit() succeeds.
**Warning signs:** Test failures where events fire but data isn't persisted.

### Pitfall 2: Async/Await Event Loop Conflicts
**What goes wrong:** "The future belongs to a different loop" errors when deferring jobs.
**Why it happens:** Procrastinate connector opened in different event loop than where defer is called.
**How to avoid:** Use `async with job_queue.open_async()` in FastAPI lifespan, use `defer_async()` in async code.
**Warning signs:** RuntimeError about event loops when deferring jobs from routes.

### Pitfall 3: Missing Job Queue Database Migrations
**What goes wrong:** Worker crashes with "relation does not exist" errors.
**Why it happens:** Procrastinate requires its own schema tables (jobs, events, etc.).
**How to avoid:** Run `procrastinate schema --apply` against job queue database before starting workers.
**Warning signs:** SQL errors referencing procrastinate_jobs table.

### Pitfall 4: Handlers Modifying State Without Transaction
**What goes wrong:** Partial state changes if handler fails midway.
**Why it happens:** Event handlers that modify multiple aggregates without their own UoW.
**How to avoid:** Handlers that modify state should open their own UoW context. For side effects only (email), no transaction needed.
**Warning signs:** Inconsistent state after handler exceptions.

### Pitfall 5: No Visibility Into Failed Jobs
**What goes wrong:** Jobs silently fail, no alerts, users don't get emails.
**Why it happens:** Not monitoring job queue health.
**How to avoid:** Log job failures at WARNING/ERROR level. Query failed jobs periodically. Use Procrastinate shell to inspect.
**Warning signs:** Users reporting missing emails; no failed job alerts.

## Code Examples

Verified patterns from official sources:

### Complete Event Bus Implementation
```python
# src/application/event_bus.py
# Source: Cosmic Python pattern + project conventions
from collections.abc import Callable
from typing import Any

from src.adapters.logging import get_logger

logger = get_logger(__name__)

# Handler registry: event_type -> list of handler functions
_handlers: dict[type, list[Callable[..., Any]]] = {}

def register(event_type: type, handler: Callable[..., Any]) -> None:
    """Register a handler for an event type.

    Multiple handlers can be registered for the same event type.
    Handlers are called in registration order.
    """
    _handlers.setdefault(event_type, []).append(handler)
    logger.debug("handler_registered", event_type=event_type.__name__, handler=handler.__name__)

def publish(event: Any) -> None:
    """Publish event to all registered handlers.

    Handlers are called synchronously. If a handler needs to do
    async work or potentially-failing operations, it should
    enqueue a job instead.
    """
    event_type = type(event)
    handlers = _handlers.get(event_type, [])

    for handler in handlers:
        try:
            logger.info("handling_event", event_type=event_type.__name__, handler=handler.__name__)
            handler(event)
        except Exception:
            logger.exception("handler_failed", event_type=event_type.__name__, handler=handler.__name__)
            # Continue to next handler - don't let one failure stop others
            raise  # Re-raise to fail fast during development

def publish_all(events: list[Any]) -> None:
    """Publish multiple events in order."""
    for event in events:
        publish(event)

def clear_handlers() -> None:
    """Clear all handlers. Used for testing."""
    _handlers.clear()
```

### Procrastinate App Configuration
```python
# src/adapters/jobs/app.py
# Source: https://procrastinate.readthedocs.io/en/stable/howto/basics/connector.html
import os
from procrastinate import App, PsycopgConnector

def create_job_queue() -> App:
    """Create and configure Procrastinate job queue app.

    Uses a separate database from the main app as per CONTEXT.md decisions.
    Connection string from JOB_QUEUE_DATABASE_URL environment variable.
    """
    conninfo = os.getenv(
        "JOB_QUEUE_DATABASE_URL",
        "postgresql://postgres:postgres@postgres:5432/jobs"
    )

    return App(
        connector=PsycopgConnector(conninfo=conninfo),
        import_paths=["src.adapters.jobs.tasks"],
    )

# Singleton instance
job_queue = create_job_queue()
```

### Event Handler Registration
```python
# src/application/handlers/__init__.py
# Source: Project conventions
from src.application.event_bus import register
from src.domain.events.user_events import UserRegistered, EmailVerified

from .user_handlers import (
    on_user_registered,
    on_email_verified,
)

def register_all_handlers() -> None:
    """Register all event handlers.

    Called during application startup.
    """
    # User domain handlers
    register(UserRegistered, on_user_registered)
    register(EmailVerified, on_email_verified)
```

### Modified UoW Commit with Event Publishing
```python
# Integration point - modify existing UoW.commit()
# Source: Project UoW + Cosmic Python pattern
def commit(self) -> None:
    """Commit transaction, writing events to outbox, then publishing.

    Events are published AFTER successful commit to ensure
    handlers see committed data.
    """
    from src.application.event_bus import publish_all

    # Capture events before commit clears them
    events_to_publish = list(self._events)

    # Write collected events to outbox (existing behavior)
    for event in self._events:
        if hasattr(event, "event_type") and hasattr(event, "aggregate_type"):
            self.session.execute(
                insert(outbox).values(
                    event_type=event.event_type,
                    aggregate_type=event.aggregate_type,
                    aggregate_id=event.aggregate_id,
                    payload=json.dumps(event.to_dict(), default=str),
                )
            )

    # Commit transaction
    self.session.commit()
    self._events.clear()

    # Publish events to handlers AFTER commit succeeds
    publish_all(events_to_publish)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Celery + Redis | PostgreSQL-based queues (Procrastinate, PGQueuer) | 2023+ | Simpler infra, fewer services |
| Dispatch events before commit | Dispatch after commit | Always best practice | Consistency guaranteed |
| Separate worker process | Worker in API process (lifespan) | FastAPI lifespan (2020+) | Single container deployment |
| Django admin for all | CLI + shell for non-Django | Procrastinate design | Framework-agnostic visibility |

**Deprecated/outdated:**
- `aiopg` connector: Procrastinate deprecated aiopg in favor of psycopg v3
- Event dispatch before commit: Leads to inconsistencies, never recommended

## Open Questions

Things that couldn't be fully resolved:

1. **Non-Django Admin Dashboard**
   - What we know: Procrastinate has Django admin integration for job visibility
   - What's unclear: Best approach for non-Django apps (this project uses FastAPI)
   - Recommendation: Use Procrastinate CLI shell (`procrastinate shell`) for job inspection. If more visibility needed, build simple FastAPI endpoint to query job status.

2. **Job Queue Database Cleanup**
   - What we know: Completed jobs persist in the database
   - What's unclear: Best retention policy, cleanup strategy
   - Recommendation: Add periodic cleanup of old successful jobs (e.g., older than 30 days). Failed jobs should persist longer for debugging.

3. **Worker Concurrency Tuning**
   - What we know: Procrastinate supports configuring worker concurrency
   - What's unclear: Optimal settings for this app's workload
   - Recommendation: Start with defaults (1 concurrent job per worker), tune based on observed performance.

## Sources

### Primary (HIGH confidence)
- [Procrastinate Documentation](https://procrastinate.readthedocs.io/en/stable/) - Official docs for job queue configuration, retry strategies, FastAPI integration
- [Procrastinate GitHub](https://github.com/procrastinate-org/procrastinate) - Version info, examples, issue discussions
- [Cosmic Python - Events and Message Bus](https://www.cosmicpython.com/book/chapter_08_events_and_message_bus.html) - Event bus pattern, handler registration, UoW integration

### Secondary (MEDIUM confidence)
- [Microsoft Domain Events Design](https://learn.microsoft.com/en-us/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/domain-events-design-implementation) - Commit-before-dispatch pattern, verified with multiple sources
- [LeanIX Engineering Blog](https://engineering.leanix.net/blog/task-queues-in-python/) - Real-world Procrastinate usage experience

### Tertiary (LOW confidence)
- PGQueuer comparison - WebSearch only, newer library with less production usage evidence

## Metadata

**Confidence breakdown:**
- Standard stack (Procrastinate): HIGH - Official docs verified, active maintenance, production usage evidence
- Architecture (event bus + job queue): HIGH - Cosmic Python pattern widely used, Procrastinate integration documented
- Pitfalls: MEDIUM - Common patterns from multiple sources, some derived from project structure analysis

**Research date:** 2026-02-06
**Valid until:** 2026-03-06 (30 days - Procrastinate is stable, slow-moving)
