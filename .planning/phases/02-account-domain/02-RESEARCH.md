# Phase 2: Account Domain - Research

**Researched:** 2026-01-30
**Domain:** DDD Aggregate Design, Account Entity Modeling, Python Dataclass Patterns
**Confidence:** HIGH

## Summary

This research covers the design patterns and implementation strategies for building the Account aggregate root in a personal finance application. The phase establishes the Account domain as the foundation for transaction recording (Phase 3) and bank synchronization (Phase 6).

The standard approach follows Domain-Driven Design principles with the Account as an aggregate root. Key patterns include:
- **Single Table Inheritance with Type Discriminator** for polymorphic account types (checking, savings, credit card, loan, brokerage, IRA, rewards)
- **Frozen dataclasses** for the Account entity with explicit mutation methods that emit domain events
- **StrEnum** (Python 3.11+) for AccountType and AccountStatus enumerations
- **Value objects** for RewardsBalance (non-monetary units) and InstitutionDetails (metadata)
- **Imperative mapping** connecting domain dataclass to SQLAlchemy table (as established in Phase 1)
- **Repository pattern** with specific query methods for account operations

The codebase already establishes Money value object, EntityId pattern, DomainEvent base, and UnitOfWork - Phase 2 builds directly on these foundations.

**Primary recommendation:** Use single table inheritance with a `type` discriminator column, frozen dataclass for Account aggregate, and type-specific validation in factory methods rather than subclasses.

## Standard Stack

The established libraries/tools for this domain are already in place from Phase 1:

### Core (Already Installed)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| SQLAlchemy | 2.0.36+ | ORM with imperative mapping | Already configured with Data Mapper pattern |
| Pydantic | 2.10+ | API schema validation | Already in use for settings, will use for DTOs |
| typeid-python | 0.3+ | Prefixed IDs | AccountId already defined in entity_id.py |
| cryptography | 43+ | Field encryption | Already implemented for account numbers |

### New for Phase 2
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Python enum.StrEnum | 3.11+ (built-in) | Type-safe string enums | AccountType, AccountStatus, AccountSubtype |

### No New Dependencies Required
Phase 2 uses existing stack. No additional packages needed.

## Architecture Patterns

### Recommended Project Structure (Additions to Phase 1)

```
src/
    domain/
        model/
            account.py          # Account aggregate root entity
            account_types.py    # AccountType, AccountStatus, AccountSubtype enums
            rewards_balance.py  # RewardsBalance value object (points + unit)
            institution.py      # InstitutionDetails value object
        events/
            account_events.py   # AccountCreated, AccountUpdated, AccountClosed, etc.
        ports/
            account_repository.py  # AccountRepository protocol
    adapters/
        persistence/
            orm/
                tables.py       # Add accounts table definition
                mappers.py      # Add Account imperative mapping
            repositories/
                account.py      # SqlAlchemyAccountRepository
        api/
            schemas/
                account.py      # Pydantic request/response schemas
            routes/
                accounts.py     # Account CRUD endpoints
    application/
        services/
            account_service.py  # Account use case orchestration
tests/
    unit/
        domain/
            test_account.py         # Account aggregate tests
            test_account_types.py   # Enum tests
            test_rewards_balance.py # RewardsBalance tests
    integration/
        test_account_repository.py  # Repository integration tests
```

### Pattern 1: Account Aggregate with Type Discriminator (NOT Subclasses)

**What:** Single Account class with type field, type-specific validation via factory methods
**When to use:** When account types share 90%+ structure with minor field differences
**Why not subclasses:** Simpler mapping, avoids dataclass inheritance issues, type validation via factories

**Example:**
```python
# src/domain/model/account.py
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from typing import Self

from src.domain.events.base import DomainEvent
from src.domain.model.entity_id import AccountId, UserId
from src.domain.model.money import Money
from src.domain.model.account_types import AccountType, AccountStatus, AccountSubtype
from src.domain.model.rewards_balance import RewardsBalance
from src.domain.model.institution import InstitutionDetails


@dataclass(eq=False, slots=True)
class Account:
    """Account aggregate root.

    Supports multiple account types with type-specific fields.
    Uses factory methods for type-specific validation.
    Not frozen - uses explicit mutation methods that emit events.
    """
    id: AccountId
    user_id: UserId
    name: str
    account_type: AccountType
    status: AccountStatus

    # Opening/balance info
    opening_balance: Money
    opening_date: datetime

    # Optional type-specific fields
    subtype: AccountSubtype | None = None
    credit_limit: Money | None = None  # Credit cards only
    apr: Decimal | None = None  # Loans only
    term_months: int | None = None  # Loans only
    due_date: datetime | None = None  # Loans with fixed terms
    rewards_balance: RewardsBalance | None = None  # Rewards accounts

    # Institution metadata
    institution: InstitutionDetails | None = None
    encrypted_account_number: str | None = None

    # Lifecycle
    closing_date: datetime | None = None
    notes: str | None = None
    sort_order: int = 0

    # Audit
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    created_by: UserId | None = None
    updated_by: UserId | None = None

    # Domain events (not persisted directly)
    _events: list[DomainEvent] = field(default_factory=list, repr=False)

    @property
    def events(self) -> list[DomainEvent]:
        """Get collected domain events."""
        return list(self._events)

    def clear_events(self) -> None:
        """Clear collected events after processing."""
        self._events.clear()

    @classmethod
    def create_checking(
        cls,
        user_id: UserId,
        name: str,
        opening_balance: Money,
        institution: InstitutionDetails | None = None,
        opening_date: datetime | None = None,
        account_number: str | None = None,
        notes: str | None = None,
    ) -> Self:
        """Factory for checking account with validation."""
        account = cls(
            id=AccountId.generate(),
            user_id=user_id,
            name=name,
            account_type=AccountType.CHECKING,
            status=AccountStatus.ACTIVE,
            opening_balance=opening_balance,
            opening_date=opening_date or datetime.now(UTC),
            institution=institution,
            notes=notes,
        )
        # Event emission
        account._events.append(AccountCreated(
            aggregate_id=str(account.id),
            aggregate_type="Account",
            account_name=name,
            account_type=AccountType.CHECKING.value,
        ))
        return account

    @classmethod
    def create_credit_card(
        cls,
        user_id: UserId,
        name: str,
        opening_balance: Money,
        credit_limit: Money,
        institution: InstitutionDetails | None = None,
        opening_date: datetime | None = None,
        notes: str | None = None,
    ) -> Self:
        """Factory for credit card with required credit_limit."""
        if credit_limit.currency != opening_balance.currency:
            raise ValueError("Credit limit currency must match balance currency")
        account = cls(
            id=AccountId.generate(),
            user_id=user_id,
            name=name,
            account_type=AccountType.CREDIT_CARD,
            status=AccountStatus.ACTIVE,
            opening_balance=opening_balance,
            opening_date=opening_date or datetime.now(UTC),
            credit_limit=credit_limit,
            institution=institution,
            notes=notes,
        )
        account._events.append(AccountCreated(
            aggregate_id=str(account.id),
            aggregate_type="Account",
            account_name=name,
            account_type=AccountType.CREDIT_CARD.value,
        ))
        return account

    # Similar factories for: create_savings, create_loan, create_brokerage,
    # create_ira, create_rewards

    def close(self, closed_by: UserId | None = None) -> None:
        """Close the account."""
        if self.status == AccountStatus.CLOSED:
            raise ValueError("Account is already closed")
        self.status = AccountStatus.CLOSED
        self.closing_date = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)
        self.updated_by = closed_by
        self._events.append(AccountClosed(
            aggregate_id=str(self.id),
            aggregate_type="Account",
        ))

    def reopen(self, reopened_by: UserId | None = None) -> None:
        """Reopen a closed account."""
        if self.status != AccountStatus.CLOSED:
            raise ValueError("Only closed accounts can be reopened")
        self.status = AccountStatus.ACTIVE
        self.closing_date = None
        self.updated_at = datetime.now(UTC)
        self.updated_by = reopened_by
        self._events.append(AccountReopened(
            aggregate_id=str(self.id),
            aggregate_type="Account",
        ))

    def update_name(self, new_name: str, updated_by: UserId | None = None) -> None:
        """Update account name."""
        if not new_name or not new_name.strip():
            raise ValueError("Account name cannot be empty")
        old_name = self.name
        self.name = new_name.strip()
        self.updated_at = datetime.now(UTC)
        self.updated_by = updated_by
        self._events.append(AccountUpdated(
            aggregate_id=str(self.id),
            aggregate_type="Account",
            field="name",
            old_value=old_name,
            new_value=self.name,
        ))

    @property
    def is_active(self) -> bool:
        """Check if account is active."""
        return self.status == AccountStatus.ACTIVE

    @property
    def available_credit(self) -> Money | None:
        """Calculate available credit for credit cards.

        Note: current_balance comes from transactions (Phase 3).
        This is a placeholder showing the calculation pattern.
        """
        if self.account_type != AccountType.CREDIT_CARD or self.credit_limit is None:
            return None
        # In Phase 3: return self.credit_limit - self.current_balance
        return self.credit_limit  # Placeholder until Phase 3
```

### Pattern 2: Account Type Enumerations with StrEnum

**What:** Type-safe string enums for account type, status, and subtype
**When to use:** All account classification fields

**Example:**
```python
# src/domain/model/account_types.py
from enum import StrEnum, auto


class AccountType(StrEnum):
    """Supported account types."""
    CHECKING = auto()
    SAVINGS = auto()
    CREDIT_CARD = auto()
    LOAN = auto()
    BROKERAGE = auto()
    IRA = auto()
    REWARDS = auto()


class AccountStatus(StrEnum):
    """Account lifecycle status."""
    ACTIVE = auto()
    CLOSED = auto()


class AccountSubtype(StrEnum):
    """Optional subtypes for type-specific domain logic."""
    # IRA subtypes
    TRADITIONAL_IRA = auto()
    ROTH_IRA = auto()
    SEP_IRA = auto()
    # Loan subtypes
    MORTGAGE = auto()
    AUTO_LOAN = auto()
    PERSONAL_LOAN = auto()
    LINE_OF_CREDIT = auto()
```

### Pattern 3: RewardsBalance Value Object

**What:** Value object for non-monetary balances with unit tracking
**When to use:** Rewards/miles accounts

**Example:**
```python
# src/domain/model/rewards_balance.py
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class RewardsBalance:
    """Value object for rewards/points/miles balances.

    Unlike Money, rewards have a unit name (e.g., "Alaska Miles", "Chase Points")
    and no currency. Value is typically an integer but stored as Decimal
    for consistency with Money.
    """
    value: Decimal
    unit: str

    def __post_init__(self) -> None:
        if not self.unit or not self.unit.strip():
            raise ValueError("Rewards unit cannot be empty")
        # Normalize to integer value (no decimals for points/miles)
        object.__setattr__(
            self,
            "value",
            Decimal(str(self.value)).quantize(Decimal("1"))
        )
        object.__setattr__(self, "unit", self.unit.strip())

    def __add__(self, other: "RewardsBalance") -> "RewardsBalance":
        if self.unit != other.unit:
            raise ValueError(f"Cannot add {self.unit} to {other.unit}")
        return RewardsBalance(self.value + other.value, self.unit)

    def __sub__(self, other: "RewardsBalance") -> "RewardsBalance":
        if self.unit != other.unit:
            raise ValueError(f"Cannot subtract {other.unit} from {self.unit}")
        return RewardsBalance(self.value - other.value, self.unit)

    def __str__(self) -> str:
        return f"{int(self.value):,} {self.unit}"
```

### Pattern 4: InstitutionDetails Value Object

**What:** Composite value object for institution metadata
**When to use:** Account institution information

**Example:**
```python
# src/domain/model/institution.py
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class InstitutionDetails:
    """Value object for financial institution details.

    Contains metadata about the institution where an account is held.
    Immutable - create new instance for changes.
    """
    name: str
    website: str | None = None
    phone: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("Institution name cannot be empty")
        object.__setattr__(self, "name", self.name.strip())
```

### Pattern 5: Account Domain Events

**What:** Frozen dataclass events for account lifecycle changes
**When to use:** All state changes that need audit trail or downstream processing

**Example:**
```python
# src/domain/events/account_events.py
from dataclasses import dataclass

from src.domain.events.base import DomainEvent


@dataclass(frozen=True)
class AccountCreated(DomainEvent):
    """Emitted when a new account is created."""
    account_name: str
    account_type: str


@dataclass(frozen=True)
class AccountUpdated(DomainEvent):
    """Emitted when account properties change."""
    field: str
    old_value: str | None
    new_value: str | None


@dataclass(frozen=True)
class AccountClosed(DomainEvent):
    """Emitted when an account is closed."""
    pass


@dataclass(frozen=True)
class AccountReopened(DomainEvent):
    """Emitted when a closed account is reopened."""
    pass


@dataclass(frozen=True)
class AccountDeleted(DomainEvent):
    """Emitted when an account without transactions is deleted."""
    pass
```

### Pattern 6: Account Repository Protocol

**What:** Domain port defining account persistence operations
**When to use:** Interface between domain and persistence layer

**Example:**
```python
# src/domain/ports/account_repository.py
from typing import Protocol

from src.domain.model.account import Account
from src.domain.model.entity_id import AccountId, UserId
from src.domain.model.account_types import AccountType, AccountStatus


class AccountRepository(Protocol):
    """Repository protocol for Account aggregate."""

    def add(self, account: Account) -> None:
        """Add a new account."""
        ...

    def get(self, account_id: AccountId) -> Account | None:
        """Get account by ID, returns None if not found."""
        ...

    def get_or_raise(self, account_id: AccountId) -> Account:
        """Get account by ID, raises EntityNotFoundError if not found."""
        ...

    def get_by_user(
        self,
        user_id: UserId,
        status: AccountStatus | None = None,
        account_type: AccountType | None = None,
    ) -> list[Account]:
        """Get all accounts for a user with optional filters."""
        ...

    def delete(self, account: Account) -> None:
        """Delete an account (only if no transactions exist)."""
        ...

    def has_transactions(self, account_id: AccountId) -> bool:
        """Check if account has any transactions (for deletion guard)."""
        ...
```

### Pattern 7: SQLAlchemy Table with Single Table Inheritance

**What:** Accounts table with type discriminator column
**When to use:** Persistent storage for all account types

**Example:**
```python
# Addition to src/adapters/persistence/orm/tables.py

accounts = Table(
    "accounts",
    metadata,
    # Identity
    Column("id", String(36), primary_key=True),  # acct_xxx
    Column("user_id", String(36), ForeignKey("users.id"), nullable=False),

    # Core fields
    Column("name", String(255), nullable=False),
    Column("account_type", String(50), nullable=False),  # Discriminator
    Column("status", String(20), nullable=False, default="active"),
    Column("subtype", String(50), nullable=True),

    # Balance tracking
    Column("opening_balance_amount", Numeric(19, 4), nullable=False),
    Column("opening_balance_currency", String(3), nullable=False),
    Column("opening_date", DateTime(timezone=True), nullable=False),

    # Type-specific fields (nullable for types that don't use them)
    Column("credit_limit_amount", Numeric(19, 4), nullable=True),
    Column("credit_limit_currency", String(3), nullable=True),
    Column("apr", Numeric(5, 4), nullable=True),  # e.g., 0.1999 for 19.99%
    Column("term_months", Integer, nullable=True),
    Column("due_date", DateTime(timezone=True), nullable=True),

    # Rewards-specific
    Column("rewards_value", Numeric(19, 0), nullable=True),
    Column("rewards_unit", String(100), nullable=True),

    # Institution
    Column("institution_name", String(255), nullable=True),
    Column("institution_website", String(500), nullable=True),
    Column("institution_phone", String(50), nullable=True),
    Column("institution_notes", Text, nullable=True),

    # Encrypted account number (AES-256-GCM via FieldEncryption)
    Column("encrypted_account_number", Text, nullable=True),

    # Lifecycle
    Column("closing_date", DateTime(timezone=True), nullable=True),
    Column("notes", Text, nullable=True),
    Column("sort_order", Integer, nullable=False, default=0),

    # Audit
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("created_by", String(36), nullable=True),
    Column("updated_by", String(36), nullable=True),

    # Indexes
    Index("ix_accounts_user_id", "user_id"),
    Index("ix_accounts_user_type", "user_id", "account_type"),
    Index("ix_accounts_user_status", "user_id", "status"),
)
```

### Anti-Patterns to Avoid

- **Subclassing for each account type:** Creates complex inheritance hierarchies, dataclass inheritance issues, and complicated SQLAlchemy mappings. Use single class with type discriminator instead.
- **Caching current balance on Account:** Balance should be calculated from transactions (Phase 3). Cached balances lead to inconsistency.
- **Mutable value objects:** InstitutionDetails and RewardsBalance must be frozen dataclasses.
- **Direct field mutation:** Use explicit methods like `update_name()`, `close()`, `reopen()` that emit events.
- **Generic CRUD repository:** AccountRepository should have domain-specific methods like `get_by_user()`, not generic `find_all()`.
- **Storing decrypted account numbers:** Always store encrypted, decrypt on read when needed.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Account number encryption | Custom cipher | FieldEncryption (Phase 1) | Already implemented with AES-256-GCM |
| Prefixed account IDs | String concatenation | AccountId from entity_id.py | Already implemented with TypeID |
| Money for balances | Custom amount class | Money from money.py | Already handles precision, currency |
| Event collection | Manual list management | _events pattern + UoW.collect_events | Already established in Phase 1 |
| Transaction management | Manual session handling | SqlAlchemyUnitOfWork | Already implemented |
| Audit timestamps | Manual datetime.now() | SQLAlchemy column defaults | Already in tables.py pattern |

**Key insight:** Phase 1 established all foundation patterns. Phase 2 should compose existing building blocks, not recreate them.

## Common Pitfalls

### Pitfall 1: Dataclass Inheritance with Defaults

**What goes wrong:** TypeError when subclass without defaults inherits from parent with defaults
**Why it happens:** Python dataclass requires non-default fields before default fields
**How to avoid:** Don't use inheritance for account types. Use single Account class with factory methods.
**Warning signs:** "non-default argument follows default argument" errors

### Pitfall 2: Forgetting Event Collection

**What goes wrong:** Domain events not persisted to outbox
**Why it happens:** Repository add() doesn't collect events, UoW commit() doesn't see them
**How to avoid:** Always call `uow.collect_events(account.events)` before commit
**Warning signs:** Outbox table empty after account operations

### Pitfall 3: Validation in Wrong Layer

**What goes wrong:** Business rules scattered across API, service, and domain layers
**Why it happens:** Validation added wherever first needed
**How to avoid:**
- Domain: Invariants in value object constructors and aggregate factory methods
- API: Request format validation in Pydantic schemas
- Service: Cross-aggregate rules
**Warning signs:** Same validation logic in multiple places

### Pitfall 4: Mutable Account Without Events

**What goes wrong:** Account state changes but no audit trail
**Why it happens:** Direct field assignment bypasses event emission
**How to avoid:** Make fields non-public or use explicit mutation methods that emit events
**Warning signs:** Account changes with empty events list

### Pitfall 5: Account Deletion Without Transaction Check

**What goes wrong:** Financial history lost when account deleted
**Why it happens:** No check for existing transactions before hard delete
**How to avoid:** Repository.has_transactions() check in application service, return error if true
**Warning signs:** Orphaned transactions, broken financial history

### Pitfall 6: Imperative Mapping with Complex Types

**What goes wrong:** SQLAlchemy can't map Money or InstitutionDetails directly
**Why it happens:** Value objects are custom types, not primitive columns
**How to avoid:** Use composite() for value objects or decompose to columns in table with reconstitution in repository
**Warning signs:** Mapping errors, "can't adapt type" exceptions

### Pitfall 7: Not Masking Account Numbers in API

**What goes wrong:** Full account numbers exposed in API responses
**Why it happens:** Returning domain entity directly without DTO transformation
**How to avoid:** Create response schema that shows only last 4 digits: `account_number_last4`
**Warning signs:** Security audit findings, PII exposure

## Code Examples

### Account Service (Application Layer)

```python
# src/application/services/account_service.py
from dataclasses import dataclass
from returns.result import Result, Success, Failure

from src.domain.model.account import Account
from src.domain.model.entity_id import AccountId, UserId
from src.domain.model.money import Money
from src.domain.model.account_types import AccountStatus
from src.domain.model.institution import InstitutionDetails
from src.domain.exceptions import EntityNotFoundError, BusinessRuleViolationError
from src.domain.ports.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class AccountError:
    """Application-level error for account operations."""
    code: str
    message: str


class AccountService:
    """Application service for account use cases."""

    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    def create_checking_account(
        self,
        user_id: UserId,
        name: str,
        opening_balance: Money,
        institution_name: str | None = None,
    ) -> Result[Account, AccountError]:
        """Create a new checking account."""
        with self._uow:
            institution = None
            if institution_name:
                institution = InstitutionDetails(name=institution_name)

            account = Account.create_checking(
                user_id=user_id,
                name=name,
                opening_balance=opening_balance,
                institution=institution,
            )

            self._uow.accounts.add(account)
            self._uow.collect_events(account.events)
            self._uow.commit()

            return Success(account)

    def close_account(
        self,
        account_id: AccountId,
        closed_by: UserId,
    ) -> Result[Account, AccountError]:
        """Close an account."""
        with self._uow:
            account = self._uow.accounts.get(account_id)
            if account is None:
                return Failure(AccountError(
                    code="ACCOUNT_NOT_FOUND",
                    message=f"Account {account_id} not found",
                ))

            try:
                account.close(closed_by=closed_by)
            except ValueError as e:
                return Failure(AccountError(
                    code="INVALID_STATE",
                    message=str(e),
                ))

            self._uow.collect_events(account.events)
            self._uow.commit()

            return Success(account)

    def delete_account(
        self,
        account_id: AccountId,
    ) -> Result[None, AccountError]:
        """Delete an account (only if no transactions exist)."""
        with self._uow:
            account = self._uow.accounts.get(account_id)
            if account is None:
                return Failure(AccountError(
                    code="ACCOUNT_NOT_FOUND",
                    message=f"Account {account_id} not found",
                ))

            if self._uow.accounts.has_transactions(account_id):
                return Failure(AccountError(
                    code="HAS_TRANSACTIONS",
                    message="Cannot delete account with transactions. Close it instead.",
                ))

            # Emit event before delete
            from src.domain.events.account_events import AccountDeleted
            deleted_event = AccountDeleted(
                aggregate_id=str(account_id),
                aggregate_type="Account",
            )

            self._uow.accounts.delete(account)
            self._uow.collect_events([deleted_event])
            self._uow.commit()

            return Success(None)
```

### Pydantic API Schemas

```python
# src/adapters/api/schemas/account.py
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator

from src.domain.model.account_types import AccountType, AccountStatus, AccountSubtype


class MoneySchema(BaseModel):
    """Money representation for API."""
    amount: Decimal
    currency: str = Field(min_length=3, max_length=3)


class InstitutionSchema(BaseModel):
    """Institution details for API."""
    name: str = Field(min_length=1, max_length=255)
    website: str | None = Field(default=None, max_length=500)
    phone: str | None = Field(default=None, max_length=50)
    notes: str | None = None


class CreateCheckingAccountRequest(BaseModel):
    """Request to create a checking account."""
    name: str = Field(min_length=1, max_length=255)
    opening_balance: MoneySchema
    institution: InstitutionSchema | None = None
    notes: str | None = None


class CreateCreditCardAccountRequest(BaseModel):
    """Request to create a credit card account."""
    name: str = Field(min_length=1, max_length=255)
    opening_balance: MoneySchema
    credit_limit: MoneySchema
    institution: InstitutionSchema | None = None
    notes: str | None = None


class AccountResponse(BaseModel):
    """Account response (masks sensitive data)."""
    id: str
    name: str
    account_type: AccountType
    status: AccountStatus
    subtype: AccountSubtype | None = None
    opening_balance: MoneySchema
    opening_date: datetime
    credit_limit: MoneySchema | None = None
    institution: InstitutionSchema | None = None
    account_number_last4: str | None = None  # Masked!
    closing_date: datetime | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

### SQLAlchemy Repository Implementation

```python
# src/adapters/persistence/repositories/account.py
from decimal import Decimal
from sqlalchemy import select, exists
from sqlalchemy.orm import Session

from src.domain.model.account import Account
from src.domain.model.entity_id import AccountId, UserId
from src.domain.model.money import Money
from src.domain.model.account_types import AccountType, AccountStatus, AccountSubtype
from src.domain.model.rewards_balance import RewardsBalance
from src.domain.model.institution import InstitutionDetails
from src.domain.exceptions import EntityNotFoundError
from src.adapters.persistence.orm.tables import accounts
# Note: transactions table will be added in Phase 3


class SqlAlchemyAccountRepository:
    """SQLAlchemy implementation of AccountRepository."""

    def __init__(self, session: Session):
        self._session = session

    def add(self, account: Account) -> None:
        """Add account to session."""
        self._session.add(account)

    def get(self, account_id: AccountId) -> Account | None:
        """Get account by ID."""
        return self._session.get(Account, str(account_id))

    def get_or_raise(self, account_id: AccountId) -> Account:
        """Get account by ID, raise if not found."""
        account = self.get(account_id)
        if account is None:
            raise EntityNotFoundError(
                "Account not found",
                context={"account_id": str(account_id)},
            )
        return account

    def get_by_user(
        self,
        user_id: UserId,
        status: AccountStatus | None = None,
        account_type: AccountType | None = None,
    ) -> list[Account]:
        """Get all accounts for a user with optional filters."""
        stmt = select(Account).where(Account.user_id == user_id)

        if status is not None:
            stmt = stmt.where(Account.status == status)
        if account_type is not None:
            stmt = stmt.where(Account.account_type == account_type)

        stmt = stmt.order_by(Account.sort_order, Account.name)

        result = self._session.execute(stmt)
        return list(result.scalars().all())

    def delete(self, account: Account) -> None:
        """Delete account from session."""
        self._session.delete(account)

    def has_transactions(self, account_id: AccountId) -> bool:
        """Check if account has transactions.

        Note: Transactions table will be added in Phase 3.
        For now, always returns False (can be deleted).
        """
        # Phase 3 implementation:
        # from src.adapters.persistence.orm.tables import transactions
        # stmt = select(exists().where(transactions.c.account_id == str(account_id)))
        # return self._session.execute(stmt).scalar() or False
        return False  # Placeholder until Phase 3
```

### Imperative Mapper Registration

```python
# Addition to src/adapters/persistence/orm/mappers.py

def start_mappers() -> None:
    """Initialize SQLAlchemy imperative mappings."""
    global _mappers_started
    if _mappers_started:
        return

    from src.domain.model.account import Account
    from src.domain.model.entity_id import AccountId, UserId
    from src.domain.model.money import Money
    from src.domain.model.account_types import AccountType, AccountStatus, AccountSubtype
    from src.domain.model.rewards_balance import RewardsBalance
    from src.domain.model.institution import InstitutionDetails
    from .tables import accounts

    mapper_registry.map_imperatively(
        Account,
        accounts,
        properties={
            "id": composite(
                lambda v: AccountId(value=v),
                accounts.c.id,
            ),
            "user_id": composite(
                lambda v: UserId(value=v),
                accounts.c.user_id,
            ),
            "account_type": column_property(accounts.c.account_type),
            "status": column_property(accounts.c.status),
            "subtype": column_property(accounts.c.subtype),
            "opening_balance": composite(
                Money,
                accounts.c.opening_balance_amount,
                accounts.c.opening_balance_currency,
            ),
            "credit_limit": composite(
                lambda amt, cur: Money(amt, cur) if amt is not None else None,
                accounts.c.credit_limit_amount,
                accounts.c.credit_limit_currency,
            ),
            "rewards_balance": composite(
                lambda val, unit: RewardsBalance(val, unit) if val is not None else None,
                accounts.c.rewards_value,
                accounts.c.rewards_unit,
            ),
            "institution": composite(
                lambda n, w, p, nt: InstitutionDetails(n, w, p, nt) if n is not None else None,
                accounts.c.institution_name,
                accounts.c.institution_website,
                accounts.c.institution_phone,
                accounts.c.institution_notes,
            ),
            # _events is transient, not mapped
        },
        exclude_properties=["_events"],
    )

    _mappers_started = True
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Class inheritance per account type | Single class with type discriminator | DDD best practices | Simpler mapping, less boilerplate |
| Regular Enum | StrEnum (Python 3.11) | 2022 | Direct string comparison, JSON friendly |
| Mutable entities with setters | Explicit mutation methods with events | Event-driven DDD | Full audit trail, better encapsulation |
| Repository returns primitives | Repository returns domain objects | Clean Architecture | Domain objects used throughout |

**Deprecated/outdated:**
- **auto_now for SQLAlchemy:** Use column defaults with timezone-aware datetime
- **IntEnum for API types:** Use StrEnum for JSON compatibility
- **Active Record pattern:** Use Data Mapper with imperative mapping

## Open Questions

Things that couldn't be fully resolved:

1. **SQLAlchemy composite() with nullable values**
   - What we know: composite() maps multiple columns to value objects
   - What's unclear: Best pattern for nullable composites (credit_limit, institution)
   - Recommendation: Use conditional lambda in composite, test thoroughly in integration tests

2. **Attachment storage implementation**
   - What we know: CONTEXT.md mentions attachment support for statements/letters
   - What's unclear: Local file vs S3, metadata tracking
   - Recommendation: Defer to Claude's discretion - simple local storage with path reference in accounts table, or dedicated attachments table

3. **has_transactions() implementation before Phase 3**
   - What we know: Method needed for deletion guard
   - What's unclear: Cannot implement until transactions table exists
   - Recommendation: Return False as placeholder, add TODO comment, implement in Phase 3

## Sources

### Primary (HIGH confidence)
- [SQLAlchemy 2.0 Inheritance Documentation](https://docs.sqlalchemy.org/en/20/orm/inheritance.html) - Single table inheritance, polymorphic_on
- [Python dataclasses documentation](https://docs.python.org/3/library/dataclasses.html) - Inheritance, slots, frozen
- [Python enum/StrEnum documentation](https://docs.python.org/3/library/enum.html) - StrEnum usage
- Phase 1 RESEARCH.md - Established patterns for Money, EntityId, Events, UoW

### Secondary (MEDIUM confidence)
- [Martin Fowler DDD Aggregate](https://martinfowler.com/bliki/DDD_Aggregate.html) - Aggregate design principles
- [DDD Modelling: Aggregates vs Entities](https://www.dandoescode.com/blog/ddd-modelling-aggregates-vs-entities) - When to use aggregates
- [Python DDD Example GitHub](https://github.com/qu3vipon/python-ddd) - Dataclass aggregate patterns

### Tertiary (LOW confidence)
- Medium articles on Python dataclass inheritance - cross-referenced with official docs
- FastAPI file upload patterns - for future attachment implementation

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Uses existing Phase 1 stack, no new dependencies
- Architecture patterns: HIGH - Based on established DDD principles and Phase 1 patterns
- Pitfalls: HIGH - Common dataclass and SQLAlchemy issues well-documented
- Code examples: MEDIUM - Imperative mapping with composites needs integration testing

**Research date:** 2026-01-30
**Valid until:** 2026-02-28 (30 days - stable patterns, Python 3.12 ecosystem mature)
