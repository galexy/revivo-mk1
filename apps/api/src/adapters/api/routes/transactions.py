"""Transaction API endpoints.

Provides REST endpoints for transaction management:
- POST /transactions - Create transaction with splits
- GET /transactions - List with search and filter
- GET /transactions/{id} - Get single transaction
- PATCH /transactions/{id} - Update transaction (metadata or splits)
- POST /transactions/{id}/clear - Mark as cleared
- POST /transactions/{id}/reconcile - Mark as reconciled
- DELETE /transactions/{id} - Delete transaction

All endpoints use dependency injection for TransactionService and current user.
Routes are protected by JWT authentication via get_current_user dependency.
Supports split transactions with automatic mirror creation for transfers.
"""

from datetime import date
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from domain.model.entity_id import AccountId, CategoryId, SplitId, TransactionId
from domain.model.money import Money
from domain.model.split_line import SplitLine
from domain.model.transaction import Transaction
from src.adapters.api.dependencies import (
    CurrentUser,
    get_current_user,
    get_transaction_service,
)
from src.adapters.api.schemas.transaction import (
    CreateTransactionRequest,
    MarkClearedRequest,
    MoneySchema,
    SplitLineResponse,
    TransactionListResponse,
    TransactionResponse,
    UpdateTransactionRequest,
)
from src.application.services.transaction_service import (
    TransactionError,
    TransactionService,
)

router = APIRouter(prefix="/transactions", tags=["transactions"])

# Type alias for cleaner signatures
CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]


def _split_to_response(split: SplitLine) -> SplitLineResponse:
    """Convert domain SplitLine to response schema."""
    return SplitLineResponse(
        id=str(split.id),
        amount=MoneySchema(amount=split.amount.amount, currency=split.amount.currency),
        category_id=str(split.category_id) if split.category_id else None,
        transfer_account_id=str(split.transfer_account_id)
        if split.transfer_account_id
        else None,
        memo=split.memo,
    )


def _transaction_to_response(txn: Transaction) -> TransactionResponse:
    """Convert domain Transaction to response schema."""
    return TransactionResponse(
        id=str(txn.id),
        user_id=str(txn.user_id),
        account_id=str(txn.account_id),
        effective_date=txn.effective_date,
        posted_date=txn.posted_date,
        amount=MoneySchema(amount=txn.amount.amount, currency=txn.amount.currency),
        status=txn.status,
        source=txn.source,
        splits=[_split_to_response(s) for s in txn.splits],
        payee_id=str(txn.payee_id) if txn.payee_id else None,
        payee_name=txn.payee_name,
        memo=txn.memo,
        check_number=txn.check_number,
        is_mirror=txn.is_mirror,
        source_transaction_id=str(txn.source_transaction_id)
        if txn.source_transaction_id
        else None,
        source_split_id=str(txn.source_split_id) if txn.source_split_id else None,
        created_at=txn.created_at,
        updated_at=txn.updated_at,
    )


@router.post(
    "", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED
)
async def create_transaction(
    request: CreateTransactionRequest,
    service: TransactionService = Depends(get_transaction_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> TransactionResponse:
    """Create a new transaction with splits."""
    # Convert request to domain objects
    account_id = AccountId.from_string(request.account_id)
    amount = Money(request.amount.amount, request.amount.currency)

    splits: list[SplitLine] = []
    for split_req in request.splits:
        try:
            split = SplitLine.create(
                amount=Money(split_req.amount.amount, split_req.amount.currency),
                category_id=CategoryId.from_string(split_req.category_id)
                if split_req.category_id
                else None,
                transfer_account_id=AccountId.from_string(split_req.transfer_account_id)
                if split_req.transfer_account_id
                else None,
                memo=split_req.memo,
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "INVALID_SPLIT", "message": str(e)},
            )
        splits.append(split)

    result = await service.create_transaction(
        user_id=current_user.user_id,
        account_id=account_id,
        effective_date=request.effective_date,
        amount=amount,
        splits=splits,
        payee_name=request.payee_name,
        memo=request.memo,
        check_number=request.check_number,
        posted_date=request.posted_date,
        household_id=current_user.household_id,
    )

    if isinstance(result, TransactionError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": result.code, "message": result.message},
        )

    return _transaction_to_response(result)


@router.get("", response_model=TransactionListResponse)
def list_transactions(
    account_id: str | None = Query(default=None),
    category_id: str | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    amount_min: Decimal | None = Query(default=None),
    amount_max: Decimal | None = Query(default=None),
    search: str | None = Query(default=None, description="Full-text search"),
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
    service: TransactionService = Depends(get_transaction_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> TransactionListResponse:
    """List transactions with filtering and search."""
    user_id = current_user.user_id

    # If search provided, use full-text search
    if search:
        txns = service.search_transactions(user_id, search, limit)
        return TransactionListResponse(
            transactions=[_transaction_to_response(t) for t in txns],
            total=len(txns),
            limit=limit,
            offset=0,
        )

    # Otherwise use filter
    acct_id = AccountId.from_string(account_id) if account_id else None
    cat_id = CategoryId.from_string(category_id) if category_id else None

    txns = service.filter_transactions(
        user_id=user_id,
        account_id=acct_id,
        category_id=cat_id,
        date_from=date_from,
        date_to=date_to,
        amount_min=amount_min,
        amount_max=amount_max,
        limit=limit,
        offset=offset,
    )

    return TransactionListResponse(
        transactions=[_transaction_to_response(t) for t in txns],
        total=len(txns),  # TODO: Return actual total count for pagination
        limit=limit,
        offset=offset,
    )


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(
    transaction_id: str,
    service: TransactionService = Depends(get_transaction_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> TransactionResponse:
    """Get a transaction by ID."""
    txn_id = TransactionId.from_string(transaction_id)
    result = service.get_transaction(current_user.user_id, txn_id)

    if isinstance(result, TransactionError):
        if result.code == "NOT_FOUND":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": result.code, "message": result.message},
        )

    return _transaction_to_response(result)


@router.patch("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    transaction_id: str,
    request: UpdateTransactionRequest,
    service: TransactionService = Depends(get_transaction_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> TransactionResponse:
    """Update transaction fields.

    Supports two modes:
    1. Metadata only: Update dates, memo, payee, check_number (no splits/amount)
    2. Full update: Include splits and amount to change financial allocations

    When updating splits, mirror transactions are automatically synced.
    """
    txn_id = TransactionId.from_string(transaction_id)
    user_id = current_user.user_id

    # Handle splits update if provided
    if request.splits is not None:
        # Validate that amount is also provided
        if request.amount is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "MISSING_AMOUNT",
                    "message": "amount is required when updating splits",
                },
            )

        # Validate each split has category or transfer (no uncategorized via API)
        for split_req in request.splits:
            if not split_req.category_id and not split_req.transfer_account_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "code": "INVALID_SPLIT",
                        "message": "Split must have either category_id or transfer_account_id",
                    },
                )

        # Fetch transaction to validate split IDs
        existing_txn = service.get_transaction(user_id, txn_id)
        if isinstance(existing_txn, TransactionError):
            status_code = status.HTTP_400_BAD_REQUEST
            if existing_txn.code == "NOT_FOUND":
                status_code = status.HTTP_404_NOT_FOUND
            raise HTTPException(
                status_code=status_code,
                detail={"code": existing_txn.code, "message": existing_txn.message},
            )

        # Convert splits to domain objects, preserving IDs if provided
        # Also validate provided split IDs exist on this transaction
        existing_split_ids = {str(s.id) for s in existing_txn.splits}
        new_splits: list[SplitLine] = []
        for split_req in request.splits:
            try:
                # If split ID provided, parse it first (validates format) then check existence
                if split_req.id:
                    split_id = SplitId.from_string(split_req.id)
                    # After parsing succeeds, check if this ID exists on the transaction
                    if split_req.id not in existing_split_ids:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail={
                                "code": "INVALID_SPLIT_ID",
                                "message": f"Split ID {split_req.id} does not exist on this transaction",
                            },
                        )
                    split = SplitLine(
                        id=split_id,
                        amount=Money(
                            split_req.amount.amount, split_req.amount.currency
                        ),
                        category_id=CategoryId.from_string(split_req.category_id)
                        if split_req.category_id
                        else None,
                        transfer_account_id=AccountId.from_string(
                            split_req.transfer_account_id
                        )
                        if split_req.transfer_account_id
                        else None,
                        memo=split_req.memo,
                    )
                else:
                    split = SplitLine.create(
                        amount=Money(
                            split_req.amount.amount, split_req.amount.currency
                        ),
                        category_id=CategoryId.from_string(split_req.category_id)
                        if split_req.category_id
                        else None,
                        transfer_account_id=AccountId.from_string(
                            split_req.transfer_account_id
                        )
                        if split_req.transfer_account_id
                        else None,
                        memo=split_req.memo,
                    )
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"code": "INVALID_SPLIT", "message": str(e)},
                )
            new_splits.append(split)

        new_amount = Money(request.amount.amount, request.amount.currency)

        result = await service.update_transaction_splits(
            user_id, txn_id, new_splits, new_amount
        )
        if isinstance(result, TransactionError):
            status_code = status.HTTP_400_BAD_REQUEST
            if result.code == "NOT_FOUND":
                status_code = status.HTTP_404_NOT_FOUND
            raise HTTPException(
                status_code=status_code,
                detail={"code": result.code, "message": result.message},
            )

    # Update dates if provided
    if request.effective_date or request.posted_date:
        result = await service.update_transaction_dates(
            user_id, txn_id, request.effective_date, request.posted_date
        )
        if isinstance(result, TransactionError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": result.code, "message": result.message},
            )

    # Update memo if provided
    if request.memo is not None:
        result = await service.update_transaction_memo(user_id, txn_id, request.memo)
        if isinstance(result, TransactionError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": result.code, "message": result.message},
            )

    # Fetch updated transaction
    result = service.get_transaction(user_id, txn_id)
    if isinstance(result, TransactionError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found"
        )

    return _transaction_to_response(result)


@router.post("/{transaction_id}/clear", response_model=TransactionResponse)
async def mark_transaction_cleared(
    transaction_id: str,
    request: MarkClearedRequest | None = None,
    service: TransactionService = Depends(get_transaction_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> TransactionResponse:
    """Mark transaction as cleared."""
    txn_id = TransactionId.from_string(transaction_id)
    posted_date = request.posted_date if request else None

    result = await service.mark_transaction_cleared(
        current_user.user_id, txn_id, posted_date
    )

    if isinstance(result, TransactionError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": result.code, "message": result.message},
        )

    return _transaction_to_response(result)


@router.post("/{transaction_id}/reconcile", response_model=TransactionResponse)
async def mark_transaction_reconciled(
    transaction_id: str,
    service: TransactionService = Depends(get_transaction_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> TransactionResponse:
    """Mark transaction as reconciled."""
    txn_id = TransactionId.from_string(transaction_id)

    result = await service.mark_transaction_reconciled(current_user.user_id, txn_id)

    if isinstance(result, TransactionError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": result.code, "message": result.message},
        )

    return _transaction_to_response(result)


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    transaction_id: str,
    service: TransactionService = Depends(get_transaction_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> None:
    """Delete a transaction (and its mirrors if source)."""
    txn_id = TransactionId.from_string(transaction_id)

    result = await service.delete_transaction(current_user.user_id, txn_id)

    if isinstance(result, TransactionError):
        status_code = status.HTTP_400_BAD_REQUEST
        if result.code == "NOT_FOUND":
            status_code = status.HTTP_404_NOT_FOUND
        raise HTTPException(
            status_code=status_code,
            detail={"code": result.code, "message": result.message},
        )
