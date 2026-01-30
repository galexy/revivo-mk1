"""Imperative mapping between domain and ORM.

This module connects domain entities to SQLAlchemy tables using
imperative (classical) mapping. This approach:
- Keeps domain models pure (no SQLAlchemy imports in domain layer)
- Follows Data Mapper pattern from RESEARCH.md Pattern 1
- Enables clean architecture with persistence ignorance

Mappings are registered once at application startup via start_mappers().

Note: Value object reconstruction (Money, InstitutionDetails, RewardsBalance, etc.)
is handled in the repository layer rather than via composite() mappings.
This simplifies handling of nullable value objects.
"""

from .base import mapper_registry

_mappers_started = False


def start_mappers() -> None:
    """Initialize SQLAlchemy imperative mappings.

    Call once at application startup (e.g., in main.py or FastAPI lifespan).
    Idempotent - safe to call multiple times.

    Mappings:
    - Account: Maps to accounts table with primitive columns.
      Value object reconstruction handled in SqlAlchemyAccountRepository.
    """
    global _mappers_started
    if _mappers_started:
        return

    # Import domain entities inside function to avoid circular imports
    from src.domain.model.account import Account

    from .tables import accounts

    # Account aggregate mapping
    # Maps Account class to accounts table.
    # Value objects (Money, InstitutionDetails, RewardsBalance) are reconstructed
    # in the repository layer after loading - not via composite() mappings.
    # This approach avoids complexity with nullable composite fields.
    mapper_registry.map_imperatively(
        Account,
        accounts,
        exclude_properties=["_events"],  # _events is transient, not persisted
    )

    _mappers_started = True


def clear_mappers() -> None:
    """Clear all mappers. Used in tests to reset mapping state.

    After calling this, start_mappers() can be called again to
    re-register mappings. Useful for test isolation.
    """
    global _mappers_started
    mapper_registry.dispose()
    _mappers_started = False
