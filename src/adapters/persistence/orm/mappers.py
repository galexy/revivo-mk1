"""Imperative mapping between domain and ORM.

This module connects domain entities to SQLAlchemy tables using
imperative (classical) mapping. This approach:
- Keeps domain models pure (no SQLAlchemy imports in domain layer)
- Follows Data Mapper pattern from RESEARCH.md Pattern 1
- Enables clean architecture with persistence ignorance

Mappings are registered once at application startup via start_mappers().
"""

from .base import mapper_registry

_mappers_started = False


def start_mappers() -> None:
    """Initialize SQLAlchemy imperative mappings.

    Call once at application startup (e.g., in main.py or FastAPI lifespan).
    Idempotent - safe to call multiple times.

    Note: Currently no domain entities to map. Mappings will be added
    as entities are created in later phases:
    - Phase 2: Account entity mapping
    - Phase 3: Transaction entity mapping

    Example future mapping:
        from src.domain.model.account import Account
        from .tables import accounts
        mapper_registry.map_imperatively(Account, accounts)
    """
    global _mappers_started
    if _mappers_started:
        return

    # Domain entity mappings will be added here as entities are created.
    # Example (Phase 2):
    # from src.domain.model.account import Account
    # from .tables import accounts
    # mapper_registry.map_imperatively(Account, accounts)

    _mappers_started = True


def clear_mappers() -> None:
    """Clear all mappers. Used in tests to reset mapping state.

    After calling this, start_mappers() can be called again to
    re-register mappings. Useful for test isolation.
    """
    global _mappers_started
    mapper_registry.dispose()
    _mappers_started = False
