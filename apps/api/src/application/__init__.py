"""Application layer - use cases and orchestration.

The application layer coordinates domain operations, manages transaction
boundaries through the Unit of Work pattern, and handles domain event
collection for the outbox pattern.

This layer:
- Orchestrates domain operations (create, update, delete)
- Manages transaction boundaries
- Collects and persists domain events
- Returns domain entities or error results (not raise exceptions)

Exports:
    AccountService: Account use case orchestration
"""

from src.application import event_bus
from src.application.services.account_service import AccountService

__all__ = ["AccountService", "event_bus"]
