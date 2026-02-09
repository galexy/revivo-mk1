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

Transaction domain handling:
- Category and Payee are simple entities with direct mapping
- Transaction has splits excluded (loaded/saved manually in repository)
- Transaction.amount excluded (reconstructed from columns in repository)
- SplitLine is a frozen dataclass - not mapped directly, handled in repository

Authentication domain handling:
- User maps to users table with _events excluded (transient)
- Household maps to households table (simple entity, no excluded properties)
- RefreshToken is NOT mapped - it uses SQLAlchemy Core (infrastructure record)
"""

from sqlalchemy import event
from sqlalchemy.orm import Session

from .base import mapper_registry

_mappers_started = False


def _decompose_value_objects(
    session: Session,
    flush_context: object,  # UOWTransaction internal type
    instances: object | None,  # Optional list of objects to flush
) -> None:
    """Decompose value objects to flat columns before persistence.

    This event handler runs before flush and expands value objects
    (Money, InstitutionDetails, RewardsBalance) into their component
    columns for storage.

    Args:
        session: The Session about to flush.
        flush_context: Internal flush context.
        instances: Optional list of objects to be flushed.
    """
    from domain.model.account import Account

    # Process new and dirty Account objects
    for obj in session.new | session.dirty:
        if isinstance(obj, Account):
            # Decompose opening_balance Money
            if obj.opening_balance is not None:  # type: ignore[reportUnnecessaryComparison]  # SQLAlchemy may set to None at runtime
                obj.opening_balance_amount = obj.opening_balance.amount  # type: ignore[attr-defined]  # SQLAlchemy-injected attribute from imperative mapping
                obj.opening_balance_currency = obj.opening_balance.currency  # type: ignore[attr-defined]  # SQLAlchemy-injected attribute from imperative mapping

            # Decompose credit_limit Money
            if obj.credit_limit is not None:
                obj.credit_limit_amount = obj.credit_limit.amount  # type: ignore[attr-defined]  # SQLAlchemy-injected attribute from imperative mapping
                obj.credit_limit_currency = obj.credit_limit.currency  # type: ignore[attr-defined]  # SQLAlchemy-injected attribute from imperative mapping
            else:
                obj.credit_limit_amount = None  # type: ignore[attr-defined]  # SQLAlchemy-injected attribute from imperative mapping
                obj.credit_limit_currency = None  # type: ignore[attr-defined]  # SQLAlchemy-injected attribute from imperative mapping

            # Decompose institution InstitutionDetails
            if obj.institution is not None:
                obj.institution_name = obj.institution.name  # type: ignore[attr-defined]  # SQLAlchemy-injected attribute from imperative mapping
                obj.institution_website = obj.institution.website  # type: ignore[attr-defined]  # SQLAlchemy-injected attribute from imperative mapping
                obj.institution_phone = obj.institution.phone  # type: ignore[attr-defined]  # SQLAlchemy-injected attribute from imperative mapping
                obj.institution_notes = obj.institution.notes  # type: ignore[attr-defined]  # SQLAlchemy-injected attribute from imperative mapping
            else:
                obj.institution_name = None  # type: ignore[attr-defined]  # SQLAlchemy-injected attribute from imperative mapping
                obj.institution_website = None  # type: ignore[attr-defined]  # SQLAlchemy-injected attribute from imperative mapping
                obj.institution_phone = None  # type: ignore[attr-defined]  # SQLAlchemy-injected attribute from imperative mapping
                obj.institution_notes = None  # type: ignore[attr-defined]  # SQLAlchemy-injected attribute from imperative mapping

            # Decompose rewards_balance RewardsBalance
            if obj.rewards_balance is not None:
                obj.rewards_value = obj.rewards_balance.value  # type: ignore[attr-defined]  # SQLAlchemy-injected attribute from imperative mapping
                obj.rewards_unit = obj.rewards_balance.unit  # type: ignore[attr-defined]  # SQLAlchemy-injected attribute from imperative mapping
            else:
                obj.rewards_value = None  # type: ignore[attr-defined]  # SQLAlchemy-injected attribute from imperative mapping
                obj.rewards_unit = None  # type: ignore[attr-defined]  # SQLAlchemy-injected attribute from imperative mapping


def start_mappers() -> None:
    """Initialize SQLAlchemy imperative mappings.

    Call once at application startup (e.g., in main.py or FastAPI lifespan).
    Idempotent - safe to call multiple times.

    Mappings:
    - Account: Maps Account class to accounts table.
      EntityIds and Enums use TypeDecorators for automatic conversion.
      Value objects are decomposed before flush and reconstructed after load.
    - Category: Maps Category class to categories table.
      Simple entity with hierarchy support (parent_id).
    - Payee: Maps Payee class to payees table.
      Simple entity with usage tracking.
    - Transaction: Maps Transaction class to transactions table.
      splits and amount excluded - handled manually in repository.
    - Household: Maps Household class to households table.
      Simple entity with name and timestamps.
    - User: Maps User class to users table.
      _events excluded (transient domain event list).
    """
    global _mappers_started
    if _mappers_started:
        return

    # Import domain entities inside function to avoid circular imports
    from domain.model.account import Account
    from domain.model.category import Category
    from domain.model.household import Household
    from domain.model.payee import Payee
    from domain.model.transaction import Transaction
    from domain.model.user import User

    from .tables import accounts, categories, households, payees, transactions, users

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

    # Category entity mapping
    # - Simple entity with hierarchy (parent_id)
    # - _events excluded (transient)
    mapper_registry.map_imperatively(
        Category,
        categories,
        exclude_properties=[
            "_events",  # _events is transient, not persisted
        ],
    )

    # Payee entity mapping
    # - Simple entity with usage tracking
    # - No excluded properties (no domain events or value objects)
    mapper_registry.map_imperatively(
        Payee,
        payees,
    )

    # Transaction aggregate mapping
    # - splits excluded: SplitLine is frozen dataclass with Money value object
    #   Loaded and saved manually in repository
    # - amount excluded: Reconstructed from amount/currency columns in repository
    # - _events excluded: Transient, not persisted
    mapper_registry.map_imperatively(
        Transaction,
        transactions,
        exclude_properties=[
            "_events",  # _events is transient, not persisted
            "splits",  # Loaded manually in repository (frozen dataclass with Money)
            "amount",  # Reconstructed from amount/currency columns in repository
        ],
    )

    # Household entity mapping
    # - Simple entity with owner reference
    # - No excluded properties (no domain events or value objects)
    mapper_registry.map_imperatively(
        Household,
        households,
    )

    # User aggregate mapping
    # - _events excluded (transient domain event list, not persisted)
    mapper_registry.map_imperatively(
        User,
        users,
        exclude_properties=[
            "_events",  # _events is transient, not persisted
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
