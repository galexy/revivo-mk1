# Phase 5: Domain Event Publishing - Context

**Gathered:** 2026-02-06
**Status:** Ready for planning

<domain>
## Phase Boundary

Establish domain event publishing infrastructure that enables async event handlers and event-driven architecture patterns. This phase creates the foundational event bus that other features (email, notifications, external integrations) will use.

The project already has domain events (UserRegistered, AccountCreated, etc.) collected via UoW. This phase adds the infrastructure to actually publish and handle those events.

</domain>

<decisions>
## Implementation Decisions

### Event Architecture
- Hybrid approach: sync domain events + async job queue for side effects
- Event handlers subscribe to specific event types
- Handlers can enqueue jobs for async processing (e.g., send email)
- Maintains existing UoW-managed event pattern
- Side effects (email, external calls) should be async via job queue

### Background Job Infrastructure
- Full job queue implementation for async side effects
- PostgreSQL-backed job queue (no Redis dependency)
- Separate database for job queue (not same as app database)
- Worker runs in same container as API if library supports (auto-start with API)
- Dead letter queue for permanently failed jobs
- Logging: standard level (job ID, event type, status, retry count) — no PII
- Admin visibility via library-provided dashboard UI

### Error Handling & Retries
- Job queue handles retries with backoff (library-provided)
- Failed jobs go to dead letter queue for review
- Event publishing is transactional with domain operation

### Claude's Discretion
- Specific job queue library choice (research PostgreSQL-backed options: e.g., procrastinate, apscheduler, or similar)
- Exact retry backoff strategy
- Dashboard port configuration
- Worker concurrency settings

</decisions>

<specifics>
## Specific Ideas

- Existing `UserRegistered` event pattern should work seamlessly with new infrastructure
- Job queue must have operational visibility for when jobs consistently fail
- No logging of PII — use job IDs for debugging correlation
- Event handlers should be simple and delegate to job queue for heavy work

</specifics>

<deferred>
## Deferred Ideas

- Email sending (Phase 6)
- External webhook notifications
- Real-time WebSocket push

</deferred>

---

*Phase: 05-domain-event-publishing*
*Context gathered: 2026-02-06*
