"""Pydantic schemas for Transaction API endpoints.

Provides request/response schemas for Transaction CRUD operations.
Supports split transactions, search/filter, and status updates.
"""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from domain.model.transaction_types import TransactionSource, TransactionStatus


class MoneySchema(BaseModel):
    """Schema for money amounts."""

    model_config = ConfigDict(from_attributes=True)

    amount: Decimal = Field(..., description="Monetary amount with up to 4 decimal places")
    currency: str = Field(
        default="USD",
        min_length=3,
        max_length=3,
        description="ISO 4217 3-letter currency code",
    )

    @field_validator("amount", mode="before")
    @classmethod
    def coerce_amount(cls, v: str | int | float | Decimal) -> Decimal:
        """Coerce amount to Decimal."""
        if isinstance(v, Decimal):
            return v
        return Decimal(str(v))


class SplitLineRequest(BaseModel):
    """Request schema for a split line."""

    id: str | None = Field(default=None, description="Split ID (omit for new splits)")
    amount: MoneySchema
    category_id: str | None = Field(
        default=None, description="Category for expense/income splits"
    )
    transfer_account_id: str | None = Field(
        default=None, description="Target account for transfer splits"
    )
    memo: str | None = Field(default=None, max_length=500)

    @field_validator("category_id", mode="before")
    @classmethod
    def validate_category_id(cls, v: str | None) -> str | None:
        """Reject empty strings for category_id."""
        if v == "":
            raise ValueError("category_id cannot be empty string")
        return v if v else None

    @field_validator("transfer_account_id", mode="before")
    @classmethod
    def validate_transfer_account_id(cls, v: str | None) -> str | None:
        """Reject empty strings for transfer_account_id."""
        if v == "":
            raise ValueError("transfer_account_id cannot be empty string")
        return v if v else None


class SplitLineResponse(BaseModel):
    """Response schema for a split line."""

    id: str  # Always present in response
    amount: MoneySchema
    category_id: str | None
    transfer_account_id: str | None
    memo: str | None


class CreateTransactionRequest(BaseModel):
    """Request to create a transaction."""

    account_id: str = Field(..., description="Account for this transaction")
    effective_date: date = Field(..., description="When transaction logically occurred")
    posted_date: date | None = Field(
        default=None, description="When transaction cleared (defaults to effective_date)"
    )
    amount: MoneySchema = Field(
        ..., description="Net flow (positive=inflow, negative=outflow)"
    )
    splits: list[SplitLineRequest] = Field(
        ..., min_length=1, description="Split lines (must sum to amount)"
    )
    payee_name: str | None = Field(default=None, max_length=255)
    memo: str | None = Field(default=None, max_length=2000)
    check_number: str | None = Field(default=None, max_length=50)


class UpdateTransactionRequest(BaseModel):
    """Request to update transaction metadata or splits.

    Supports two modes:
    1. Metadata only: Update dates, memo, payee, check_number
    2. Full update: Include splits and amount to change financial allocations

    When updating splits, amount is required and mirror transactions are synced.
    """

    effective_date: date | None = None
    posted_date: date | None = None
    memo: str | None = None
    payee_name: str | None = None
    check_number: str | None = None
    splits: list[SplitLineRequest] | None = Field(
        default=None, description="New splits (if provided, amount must also be provided)"
    )
    amount: MoneySchema | None = Field(
        default=None, description="New amount (required if splits provided)"
    )


class TransactionResponse(BaseModel):
    """Response schema for a transaction."""

    id: str
    user_id: str
    account_id: str
    effective_date: date
    posted_date: date | None
    amount: MoneySchema
    status: TransactionStatus
    source: TransactionSource
    splits: list[SplitLineResponse]
    payee_id: str | None
    payee_name: str | None
    memo: str | None
    check_number: str | None
    is_mirror: bool
    source_transaction_id: str | None
    source_split_id: str | None  # Links mirror to source split
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TransactionListResponse(BaseModel):
    """Response for listing transactions."""

    transactions: list[TransactionResponse]
    total: int
    limit: int
    offset: int


class TransactionFilterParams(BaseModel):
    """Query parameters for filtering transactions."""

    account_id: str | None = None
    category_id: str | None = None
    date_from: date | None = None
    date_to: date | None = None
    amount_min: Decimal | None = None
    amount_max: Decimal | None = None
    search: str | None = Field(default=None, description="Full-text search on payee/memo")
    limit: int = Field(default=100, le=500)
    offset: int = Field(default=0, ge=0)


class MarkClearedRequest(BaseModel):
    """Request to mark transaction as cleared."""

    posted_date: date | None = Field(default=None, description="Posted date (optional)")
