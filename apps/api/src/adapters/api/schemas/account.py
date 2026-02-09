"""Pydantic schemas for Account API endpoints.

Provides request/response schemas for Account CRUD operations.
All schemas handle validation and serialization between HTTP and domain layers.

Key features:
- Request schemas validate input data
- Response schemas convert domain objects to API format
- Account numbers are masked (last 4 digits only) for security
- MoneySchema handles decimal serialization
"""

from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

from domain.model.account import Account
from domain.model.account_types import AccountStatus, AccountSubtype, AccountType


# --- Value Object Schemas ---


class MoneySchema(BaseModel):
    """Schema for Money value object serialization."""

    model_config = ConfigDict(from_attributes=True)

    amount: Decimal = Field(..., description="Monetary amount with up to 4 decimal places")
    currency: str = Field(
        default="USD",
        description="ISO 4217 3-letter currency code",
        min_length=3,
        max_length=3,
    )

    @field_validator("amount", mode="before")
    @classmethod
    def coerce_amount(cls, v: str | int | float | Decimal) -> Decimal:
        """Coerce amount to Decimal."""
        if isinstance(v, Decimal):
            return v
        return Decimal(str(v))


class InstitutionSchema(BaseModel):
    """Schema for InstitutionDetails value object."""

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., description="Institution name", min_length=1, max_length=200)
    website: str | None = Field(default=None, max_length=500)
    phone: str | None = Field(default=None, max_length=50)
    notes: str | None = Field(default=None, max_length=2000)


class RewardsBalanceSchema(BaseModel):
    """Schema for RewardsBalance value object."""

    model_config = ConfigDict(from_attributes=True)

    value: Decimal = Field(..., description="Number of points/miles")
    unit: str = Field(..., description="Reward program name (e.g., 'Alaska Miles')")

    @field_validator("value", mode="before")
    @classmethod
    def coerce_value(cls, v: str | int | float | Decimal) -> Decimal:
        """Coerce value to Decimal."""
        if isinstance(v, Decimal):
            return v
        return Decimal(str(v))


# --- Create Account Request Schemas (one per account type) ---


class CreateCheckingAccountRequest(BaseModel):
    """Request schema for creating a checking account."""

    name: str = Field(..., description="Account display name", min_length=1, max_length=200)
    opening_balance: MoneySchema = Field(..., description="Initial balance")
    opening_date: datetime | None = Field(
        default=None, description="Date account was opened (defaults to now)"
    )
    institution: InstitutionSchema | None = Field(
        default=None, description="Financial institution details"
    )
    account_number: str | None = Field(
        default=None, description="Account number (will be encrypted)", max_length=50
    )
    notes: str | None = Field(default=None, max_length=2000)


class CreateSavingsAccountRequest(BaseModel):
    """Request schema for creating a savings account."""

    name: str = Field(..., description="Account display name", min_length=1, max_length=200)
    opening_balance: MoneySchema = Field(..., description="Initial balance")
    opening_date: datetime | None = Field(
        default=None, description="Date account was opened (defaults to now)"
    )
    institution: InstitutionSchema | None = Field(
        default=None, description="Financial institution details"
    )
    account_number: str | None = Field(
        default=None, description="Account number (will be encrypted)", max_length=50
    )
    notes: str | None = Field(default=None, max_length=2000)


class CreateCreditCardAccountRequest(BaseModel):
    """Request schema for creating a credit card account."""

    name: str = Field(..., description="Account display name", min_length=1, max_length=200)
    opening_balance: MoneySchema = Field(..., description="Initial balance (current charges)")
    credit_limit: MoneySchema = Field(..., description="Credit limit")
    opening_date: datetime | None = Field(
        default=None, description="Date account was opened (defaults to now)"
    )
    institution: InstitutionSchema | None = Field(
        default=None, description="Financial institution details"
    )
    notes: str | None = Field(default=None, max_length=2000)


class CreateLoanAccountRequest(BaseModel):
    """Request schema for creating a loan account."""

    name: str = Field(..., description="Account display name", min_length=1, max_length=200)
    opening_balance: MoneySchema = Field(..., description="Initial loan balance (principal)")
    subtype: AccountSubtype | None = Field(
        default=None, description="Loan type (mortgage, auto, personal, line_of_credit)"
    )
    apr: Annotated[Decimal, Field(ge=0, le=1)] | None = Field(
        default=None, description="Annual percentage rate as decimal (e.g., 0.0599 for 5.99%)"
    )
    term_months: Annotated[int, Field(ge=1, le=600)] | None = Field(
        default=None, description="Loan term in months"
    )
    due_date: datetime | None = Field(default=None, description="Final payment due date")
    opening_date: datetime | None = Field(
        default=None, description="Date loan originated (defaults to now)"
    )
    institution: InstitutionSchema | None = Field(
        default=None, description="Financial institution details"
    )
    notes: str | None = Field(default=None, max_length=2000)


class CreateBrokerageAccountRequest(BaseModel):
    """Request schema for creating a brokerage account."""

    name: str = Field(..., description="Account display name", min_length=1, max_length=200)
    opening_balance: MoneySchema = Field(..., description="Initial cash balance")
    opening_date: datetime | None = Field(
        default=None, description="Date account was opened (defaults to now)"
    )
    institution: InstitutionSchema | None = Field(
        default=None, description="Financial institution details"
    )
    notes: str | None = Field(default=None, max_length=2000)


class CreateIraAccountRequest(BaseModel):
    """Request schema for creating an IRA account."""

    name: str = Field(..., description="Account display name", min_length=1, max_length=200)
    opening_balance: MoneySchema = Field(..., description="Initial balance")
    subtype: AccountSubtype | None = Field(
        default=None, description="IRA type (traditional_ira, roth_ira, sep_ira)"
    )
    opening_date: datetime | None = Field(
        default=None, description="Date account was opened (defaults to now)"
    )
    institution: InstitutionSchema | None = Field(
        default=None, description="Financial institution details"
    )
    notes: str | None = Field(default=None, max_length=2000)


class CreateRewardsAccountRequest(BaseModel):
    """Request schema for creating a rewards account."""

    name: str = Field(..., description="Account display name", min_length=1, max_length=200)
    rewards_balance: RewardsBalanceSchema = Field(
        ..., description="Initial rewards balance (points/miles)"
    )
    opening_date: datetime | None = Field(
        default=None, description="Date account was opened (defaults to now)"
    )
    institution: InstitutionSchema | None = Field(
        default=None, description="Rewards program provider"
    )
    notes: str | None = Field(default=None, max_length=2000)


# --- Update Account Request ---


class UpdateAccountRequest(BaseModel):
    """Request schema for updating an account."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    institution: InstitutionSchema | None = Field(default=None)
    notes: str | None = Field(default=None, max_length=2000)
    # Note: Most fields cannot be updated after creation (opening_balance, type, etc.)


# --- Response Schemas ---


class AccountResponse(BaseModel):
    """Response schema for a single account.

    Masks account numbers for security (shows only last 4 digits).
    Current balance equals opening balance until Phase 3 transactions.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Account ID (prefixed)")
    user_id: str = Field(..., description="Owner user ID")
    name: str = Field(..., description="Account display name")
    account_type: AccountType = Field(..., description="Account type")
    status: AccountStatus = Field(..., description="Account status")

    # Balance info
    opening_balance: MoneySchema = Field(..., description="Opening balance")
    current_balance: MoneySchema = Field(
        ..., description="Current balance (equals opening until Phase 3)"
    )
    opening_date: datetime = Field(..., description="Date account was opened")

    # Type-specific fields
    subtype: AccountSubtype | None = Field(default=None, description="Account subtype")
    credit_limit: MoneySchema | None = Field(default=None, description="Credit limit")
    available_credit: MoneySchema | None = Field(default=None, description="Available credit")
    apr: Decimal | None = Field(default=None, description="Annual percentage rate")
    term_months: int | None = Field(default=None, description="Loan term in months")
    due_date: datetime | None = Field(default=None, description="Due date for loans")
    rewards_balance: RewardsBalanceSchema | None = Field(
        default=None, description="Rewards balance"
    )

    # Institution
    institution: InstitutionSchema | None = Field(default=None, description="Institution details")
    account_number_last4: str | None = Field(
        default=None, description="Last 4 digits of account number"
    )

    # Lifecycle
    closing_date: datetime | None = Field(default=None, description="Date account was closed")
    notes: str | None = Field(default=None, description="Account notes")

    # Audit
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    @classmethod
    def from_domain(
        cls,
        account: Account,
        decrypted_account_number: str | None = None,
    ) -> "AccountResponse":
        """Convert domain Account to response schema.

        Args:
            account: Domain Account aggregate.
            decrypted_account_number: Decrypted account number (for masking).

        Returns:
            AccountResponse with masked account number.
        """
        # Mask account number - show only last 4 digits
        account_number_last4 = None
        if decrypted_account_number:
            account_number_last4 = decrypted_account_number[-4:] if len(decrypted_account_number) >= 4 else decrypted_account_number

        # Build opening balance schema
        opening_balance = MoneySchema(
            amount=account.opening_balance.amount,
            currency=account.opening_balance.currency,
        )

        # Current balance equals opening balance until Phase 3
        current_balance = opening_balance

        # Type-specific fields
        credit_limit = None
        if account.credit_limit:
            credit_limit = MoneySchema(
                amount=account.credit_limit.amount,
                currency=account.credit_limit.currency,
            )

        available_credit = None
        if account.available_credit:
            available_credit = MoneySchema(
                amount=account.available_credit.amount,
                currency=account.available_credit.currency,
            )

        rewards_balance = None
        if account.rewards_balance:
            rewards_balance = RewardsBalanceSchema(
                value=account.rewards_balance.value,
                unit=account.rewards_balance.unit,
            )

        institution = None
        if account.institution:
            institution = InstitutionSchema(
                name=account.institution.name,
                website=account.institution.website,
                phone=account.institution.phone,
                notes=account.institution.notes,
            )

        return cls(
            id=str(account.id),
            user_id=str(account.user_id),
            name=account.name,
            account_type=account.account_type,
            status=account.status,
            opening_balance=opening_balance,
            current_balance=current_balance,
            opening_date=account.opening_date,
            subtype=account.subtype,
            credit_limit=credit_limit,
            available_credit=available_credit,
            apr=account.apr,
            term_months=account.term_months,
            due_date=account.due_date,
            rewards_balance=rewards_balance,
            institution=institution,
            account_number_last4=account_number_last4,
            closing_date=account.closing_date,
            notes=account.notes,
            created_at=account.created_at,
            updated_at=account.updated_at,
        )


class AccountListResponse(BaseModel):
    """Response schema for listing accounts."""

    accounts: list[AccountResponse] = Field(..., description="List of accounts")
    total: int = Field(..., description="Total number of accounts matching filters")
