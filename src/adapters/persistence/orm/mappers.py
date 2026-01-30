"""Imperative mapping between domain and ORM.

This module connects domain entities to SQLAlchemy tables using
imperative (classical) mapping. This approach:
- Keeps domain models pure (no SQLAlchemy imports in domain layer)
- Follows Data Mapper pattern from RESEARCH.md Pattern 1
- Enables clean architecture with persistence ignorance

Mappings are registered once at application startup via start_mappers().

Value object handling:
- Money, InstitutionDetails, RewardsBalance are decomposed to flat columns
  before persistence via a before_flush event listener
- Reconstruction from flat columns to value objects happens in the repository
- Type conversions for EntityIds and Enums use custom TypeDecorators
"""

from sqlalchemy import event
from sqlalchemy.orm import Session

from .base import mapper_registry

_mappers_started = False


def _decompose_value_objects(session: Session, flush_context, instances) -> None:
    """Decompose value objects to flat columns before persistence.

    This event handler runs before flush and expands value objects
    (Money, InstitutionDetails, RewardsBalance) into their component
    columns for storage.

    Args:
        session: The Session about to flush.
        flush_context: Internal flush context.
        instances: Optional list of objects to be flushed.
    """
    from src.domain.model.account import Account

    # Process new and dirty Account objects
    for obj in session.new | session.dirty:
        if isinstance(obj, Account):
            # Decompose opening_balance Money
            if obj.opening_balance is not None:
                obj.opening_balance_amount = obj.opening_balance.amount
                obj.opening_balance_currency = obj.opening_balance.currency

            # Decompose credit_limit Money
            if obj.credit_limit is not None:
                obj.credit_limit_amount = obj.credit_limit.amount
                obj.credit_limit_currency = obj.credit_limit.currency
            else:
                obj.credit_limit_amount = None
                obj.credit_limit_currency = None

            # Decompose institution InstitutionDetails
            if obj.institution is not None:
                obj.institution_name = obj.institution.name
                obj.institution_website = obj.institution.website
                obj.institution_phone = obj.institution.phone
                obj.institution_notes = obj.institution.notes
            else:
                obj.institution_name = None
                obj.institution_website = None
                obj.institution_phone = None
                obj.institution_notes = None

            # Decompose rewards_balance RewardsBalance
            if obj.rewards_balance is not None:
                obj.rewards_value = obj.rewards_balance.value
                obj.rewards_unit = obj.rewards_balance.unit
            else:
                obj.rewards_value = None
                obj.rewards_unit = None


def start_mappers() -> None:
    """Initialize SQLAlchemy imperative mappings.

    Call once at application startup (e.g., in main.py or FastAPI lifespan).
    Idempotent - safe to call multiple times.

    Mappings:
    - Account: Maps Account class to accounts table.
      EntityIds and Enums use TypeDecorators for automatic conversion.
      Value objects are decomposed before flush and reconstructed after load.
    """
    global _mappers_started
    if _mappers_started:
        return

    # Import domain entities inside function to avoid circular imports
    from src.domain.model.account import Account

    from .tables import accounts

    # Account aggregate mapping
    # - EntityIds (id, user_id, etc.): TypeDecorators handle string conversion
    # - Enums (account_type, status, subtype): TypeDecorators handle value conversion
    # - Value objects: Excluded from direct mapping
    #   * Decomposed to flat columns via before_flush event
    #   * Reconstructed in repository after loading
    mapper_registry.map_imperatively(
        Account,
        accounts,
        exclude_properties=[
            "_events",  # _events is transient, not persisted
            "opening_balance",  # Decomposed/reconstructed via events/repository
            "credit_limit",  # Decomposed/reconstructed via events/repository
            "institution",  # Decomposed/reconstructed via events/repository
            "rewards_balance",  # Decomposed/reconstructed via events/repository
        ],
    )

    # Register event listener for value object decomposition
    event.listen(Session, "before_flush", _decompose_value_objects)

    _mappers_started = True


def clear_mappers() -> None:
    """Clear all mappers. Used in tests to reset mapping state.

    After calling this, start_mappers() can be called again to
    re-register mappings. Useful for test isolation.
    """
    global _mappers_started

    # Remove event listener
    try:
        event.remove(Session, "before_flush", _decompose_value_objects)
    except Exception:
        pass  # Listener might not be registered

    mapper_registry.dispose()
    _mappers_started = False
