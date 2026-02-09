"""Imperative mapping between domain and ORM.

This module connects domain entities to SQLAlchemy tables using
imperative (classical) mapping. This approach:
- Keeps domain models pure (no SQLAlchemy imports in domain layer)
- Follows Data Mapper pattern from RESEARCH.md Pattern 1
- Enables clean architecture with persistence ignorance

Mappings are registered once at application startup via start_mappers().

Value object handling:
- Money, InstitutionDetails, RewardsBalance use SQLAlchemy composite()
  to map value objects to multiple database columns automatically
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

from sqlalchemy.orm import composite

from .base import mapper_registry

_mappers_started = False


def _money_factory(amount: object, currency: object) -> object:
    """Factory for Money composite that returns None when both values are None."""
    from domain.model.money import Money

    if amount is None and currency is None:
        return None
    return Money(amount, currency)  # type: ignore[arg-type]  # amount/currency are Decimal/str from DB


def _institution_factory(
    name: object, website: object, phone: object, notes: object
) -> object:
    """Factory for InstitutionDetails composite that returns None when name is None."""
    from domain.model.institution import InstitutionDetails

    if name is None:
        return None
    return InstitutionDetails(name, website, phone, notes)  # type: ignore[arg-type]  # values are str/None from DB


def _rewards_factory(value: object, unit: object) -> object:
    """Factory for RewardsBalance composite that returns None when both values are None."""
    from domain.model.rewards_balance import RewardsBalance

    if value is None and unit is None:
        return None
    return RewardsBalance(value, unit)  # type: ignore[arg-type]  # value is Decimal, unit is str from DB


def start_mappers() -> None:
    """Initialize SQLAlchemy imperative mappings.

    Call once at application startup (e.g., in main.py or FastAPI lifespan).
    Idempotent - safe to call multiple times.

    Mappings:
    - Account: Maps Account class to accounts table.
      EntityIds and Enums use TypeDecorators for automatic conversion.
      Value objects use composite() for automatic decomposition/reconstruction.
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
    # - Value objects: composite() maps to multiple database columns automatically
    #   * Money: opening_balance, credit_limit
    #   * InstitutionDetails: institution
    #   * RewardsBalance: rewards_balance
    mapper_registry.map_imperatively(
        Account,
        accounts,
        exclude_properties=[
            "_events",  # _events is transient, not persisted
        ],
        properties={
            "opening_balance": composite(
                _money_factory,
                accounts.c.opening_balance_amount,
                accounts.c.opening_balance_currency,
            ),
            "credit_limit": composite(
                _money_factory,
                accounts.c.credit_limit_amount,
                accounts.c.credit_limit_currency,
            ),
            "institution": composite(
                _institution_factory,
                accounts.c.institution_name,
                accounts.c.institution_website,
                accounts.c.institution_phone,
                accounts.c.institution_notes,
            ),
            "rewards_balance": composite(
                _rewards_factory,
                accounts.c.rewards_value,
                accounts.c.rewards_unit,
            ),
        },
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

    _mappers_started = True


def clear_mappers() -> None:
    """Clear all mappers. Used in tests to reset mapping state.

    After calling this, start_mappers() can be called again to
    re-register mappings. Useful for test isolation.
    """
    global _mappers_started
    mapper_registry.dispose()
    _mappers_started = False
