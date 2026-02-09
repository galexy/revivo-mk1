"""Account API routes for CRUD operations.

Provides REST endpoints for account management:
- POST /accounts/{type} - Create accounts for all 7 types
- GET /accounts - List accounts with filters
- GET /accounts/{id} - Get single account
- PATCH /accounts/{id} - Update account
- POST /accounts/{id}/close - Close account
- POST /accounts/{id}/reopen - Reopen closed account
- DELETE /accounts/{id} - Delete account (without transactions only)

All endpoints use dependency injection for AccountService and current user.
Routes are protected by JWT authentication via get_current_user dependency.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typeid.errors import SuffixValidationException

from src.adapters.api.dependencies import (
    CurrentUser,
    get_current_user,
    get_unit_of_work,
)
from src.adapters.persistence.unit_of_work import SqlAlchemyUnitOfWork
from src.application.services.account_service import AccountError, AccountService
from domain.model.account_types import AccountStatus, AccountType
from domain.model.entity_id import AccountId
from domain.model.institution import InstitutionDetails
from domain.model.money import Money
from domain.model.rewards_balance import RewardsBalance

from ..schemas.account import (
    AccountListResponse,
    AccountResponse,
    CreateBrokerageAccountRequest,
    CreateCheckingAccountRequest,
    CreateCreditCardAccountRequest,
    CreateIraAccountRequest,
    CreateLoanAccountRequest,
    CreateRewardsAccountRequest,
    CreateSavingsAccountRequest,
    UpdateAccountRequest,
)

router = APIRouter(prefix="/accounts", tags=["accounts"])


# --- Dependencies ---


def get_account_service(
    uow: Annotated[SqlAlchemyUnitOfWork, Depends(get_unit_of_work)],
) -> AccountService:
    """Provide AccountService with UnitOfWork.

    Args:
        uow: Unit of Work from dependency injection.

    Returns:
        AccountService configured with the UnitOfWork.
    """
    return AccountService(uow)


# Type aliases for cleaner signatures
AccountServiceDep = Annotated[AccountService, Depends(get_account_service)]
CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]


# --- Helper Functions ---


def _handle_error(error: AccountError) -> None:
    """Convert AccountError to HTTPException.

    Args:
        error: AccountError from service layer.

    Raises:
        HTTPException with appropriate status code.
    """
    status_map = {
        "NOT_FOUND": status.HTTP_404_NOT_FOUND,
        "ALREADY_CLOSED": status.HTTP_409_CONFLICT,
        "NOT_CLOSED": status.HTTP_409_CONFLICT,
        "HAS_TRANSACTIONS": status.HTTP_409_CONFLICT,
        "VALIDATION_ERROR": status.HTTP_422_UNPROCESSABLE_ENTITY,
    }
    http_status = status_map.get(error.code, status.HTTP_400_BAD_REQUEST)
    raise HTTPException(status_code=http_status, detail=error.message)


def _institution_from_schema(
    schema: "CreateCheckingAccountRequest",
) -> InstitutionDetails | None:
    """Convert institution schema to domain object.

    Args:
        schema: Request schema with optional institution.

    Returns:
        InstitutionDetails or None.
    """
    if schema.institution is None:
        return None
    return InstitutionDetails(
        name=schema.institution.name,
        website=schema.institution.website,
        phone=schema.institution.phone,
        notes=schema.institution.notes,
    )


# --- Create Endpoints ---


@router.post(
    "/checking",
    response_model=AccountResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create checking account",
)
async def create_checking_account(
    request: CreateCheckingAccountRequest,
    service: AccountServiceDep,
    current_user: CurrentUserDep,
) -> AccountResponse:
    """Create a new checking account.

    Args:
        request: Checking account creation data.
        service: AccountService from dependency injection.
        current_user: Authenticated user context from JWT.

    Returns:
        Created account details.

    Raises:
        HTTPException: On validation or creation failure.
    """
    institution = None
    if request.institution:
        institution = InstitutionDetails(
            name=request.institution.name,
            website=request.institution.website,
            phone=request.institution.phone,
            notes=request.institution.notes,
        )

    result = await service.create_checking(
        user_id=current_user.user_id,
        name=request.name,
        opening_balance=Money(
            request.opening_balance.amount,
            request.opening_balance.currency,
        ),
        household_id=current_user.household_id,
        institution=institution,
        opening_date=request.opening_date,
        account_number=request.account_number,
        notes=request.notes,
    )

    if isinstance(result, AccountError):
        _handle_error(result)

    return AccountResponse.from_domain(result, request.account_number)


@router.post(
    "/savings",
    response_model=AccountResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create savings account",
)
async def create_savings_account(
    request: CreateSavingsAccountRequest,
    service: AccountServiceDep,
    current_user: CurrentUserDep,
) -> AccountResponse:
    """Create a new savings account.

    Args:
        request: Savings account creation data.
        service: AccountService from dependency injection.
        current_user: Authenticated user context from JWT.

    Returns:
        Created account details.

    Raises:
        HTTPException: On validation or creation failure.
    """
    institution = None
    if request.institution:
        institution = InstitutionDetails(
            name=request.institution.name,
            website=request.institution.website,
            phone=request.institution.phone,
            notes=request.institution.notes,
        )

    result = await service.create_savings(
        user_id=current_user.user_id,
        name=request.name,
        opening_balance=Money(
            request.opening_balance.amount,
            request.opening_balance.currency,
        ),
        household_id=current_user.household_id,
        institution=institution,
        opening_date=request.opening_date,
        account_number=request.account_number,
        notes=request.notes,
    )

    if isinstance(result, AccountError):
        _handle_error(result)

    return AccountResponse.from_domain(result, request.account_number)


@router.post(
    "/credit-card",
    response_model=AccountResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create credit card account",
)
async def create_credit_card_account(
    request: CreateCreditCardAccountRequest,
    service: AccountServiceDep,
    current_user: CurrentUserDep,
) -> AccountResponse:
    """Create a new credit card account.

    Args:
        request: Credit card account creation data.
        service: AccountService from dependency injection.
        current_user: Authenticated user context from JWT.

    Returns:
        Created account details.

    Raises:
        HTTPException: On validation or creation failure.
    """
    institution = None
    if request.institution:
        institution = InstitutionDetails(
            name=request.institution.name,
            website=request.institution.website,
            phone=request.institution.phone,
            notes=request.institution.notes,
        )

    result = await service.create_credit_card(
        user_id=current_user.user_id,
        name=request.name,
        opening_balance=Money(
            request.opening_balance.amount,
            request.opening_balance.currency,
        ),
        credit_limit=Money(
            request.credit_limit.amount,
            request.credit_limit.currency,
        ),
        household_id=current_user.household_id,
        institution=institution,
        opening_date=request.opening_date,
        notes=request.notes,
    )

    if isinstance(result, AccountError):
        _handle_error(result)

    return AccountResponse.from_domain(result)


@router.post(
    "/loan",
    response_model=AccountResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create loan account",
)
async def create_loan_account(
    request: CreateLoanAccountRequest,
    service: AccountServiceDep,
    current_user: CurrentUserDep,
) -> AccountResponse:
    """Create a new loan account.

    Args:
        request: Loan account creation data.
        service: AccountService from dependency injection.
        current_user: Authenticated user context from JWT.

    Returns:
        Created account details.

    Raises:
        HTTPException: On validation or creation failure.
    """
    institution = None
    if request.institution:
        institution = InstitutionDetails(
            name=request.institution.name,
            website=request.institution.website,
            phone=request.institution.phone,
            notes=request.institution.notes,
        )

    result = await service.create_loan(
        user_id=current_user.user_id,
        name=request.name,
        opening_balance=Money(
            request.opening_balance.amount,
            request.opening_balance.currency,
        ),
        subtype=request.subtype,
        apr=request.apr,
        term_months=request.term_months,
        due_date=request.due_date,
        household_id=current_user.household_id,
        institution=institution,
        opening_date=request.opening_date,
        notes=request.notes,
    )

    if isinstance(result, AccountError):
        _handle_error(result)

    return AccountResponse.from_domain(result)


@router.post(
    "/brokerage",
    response_model=AccountResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create brokerage account",
)
async def create_brokerage_account(
    request: CreateBrokerageAccountRequest,
    service: AccountServiceDep,
    current_user: CurrentUserDep,
) -> AccountResponse:
    """Create a new brokerage account.

    Args:
        request: Brokerage account creation data.
        service: AccountService from dependency injection.
        current_user: Authenticated user context from JWT.

    Returns:
        Created account details.

    Raises:
        HTTPException: On validation or creation failure.
    """
    institution = None
    if request.institution:
        institution = InstitutionDetails(
            name=request.institution.name,
            website=request.institution.website,
            phone=request.institution.phone,
            notes=request.institution.notes,
        )

    result = await service.create_brokerage(
        user_id=current_user.user_id,
        name=request.name,
        opening_balance=Money(
            request.opening_balance.amount,
            request.opening_balance.currency,
        ),
        household_id=current_user.household_id,
        institution=institution,
        opening_date=request.opening_date,
        notes=request.notes,
    )

    if isinstance(result, AccountError):
        _handle_error(result)

    return AccountResponse.from_domain(result)


@router.post(
    "/ira",
    response_model=AccountResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create IRA account",
)
async def create_ira_account(
    request: CreateIraAccountRequest,
    service: AccountServiceDep,
    current_user: CurrentUserDep,
) -> AccountResponse:
    """Create a new IRA account.

    Args:
        request: IRA account creation data.
        service: AccountService from dependency injection.
        current_user: Authenticated user context from JWT.

    Returns:
        Created account details.

    Raises:
        HTTPException: On validation or creation failure.
    """
    institution = None
    if request.institution:
        institution = InstitutionDetails(
            name=request.institution.name,
            website=request.institution.website,
            phone=request.institution.phone,
            notes=request.institution.notes,
        )

    result = await service.create_ira(
        user_id=current_user.user_id,
        name=request.name,
        opening_balance=Money(
            request.opening_balance.amount,
            request.opening_balance.currency,
        ),
        subtype=request.subtype,
        household_id=current_user.household_id,
        institution=institution,
        opening_date=request.opening_date,
        notes=request.notes,
    )

    if isinstance(result, AccountError):
        _handle_error(result)

    return AccountResponse.from_domain(result)


@router.post(
    "/rewards",
    response_model=AccountResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create rewards account",
)
async def create_rewards_account(
    request: CreateRewardsAccountRequest,
    service: AccountServiceDep,
    current_user: CurrentUserDep,
) -> AccountResponse:
    """Create a new rewards account.

    Args:
        request: Rewards account creation data.
        service: AccountService from dependency injection.
        current_user: Authenticated user context from JWT.

    Returns:
        Created account details.

    Raises:
        HTTPException: On validation or creation failure.
    """
    institution = None
    if request.institution:
        institution = InstitutionDetails(
            name=request.institution.name,
            website=request.institution.website,
            phone=request.institution.phone,
            notes=request.institution.notes,
        )

    result = await service.create_rewards(
        user_id=current_user.user_id,
        name=request.name,
        rewards_balance=RewardsBalance(
            value=request.rewards_balance.value,
            unit=request.rewards_balance.unit,
        ),
        household_id=current_user.household_id,
        institution=institution,
        opening_date=request.opening_date,
        notes=request.notes,
    )

    if isinstance(result, AccountError):
        _handle_error(result)

    return AccountResponse.from_domain(result)


# --- Read Endpoints ---


@router.get(
    "",
    response_model=AccountListResponse,
    summary="List household accounts",
)
async def list_accounts(
    service: AccountServiceDep,
    current_user: CurrentUserDep,
    status_filter: Annotated[
        AccountStatus | None,
        Query(alias="status", description="Filter by status"),
    ] = None,
    type_filter: Annotated[
        AccountType | None,
        Query(alias="type", description="Filter by account type"),
    ] = None,
) -> AccountListResponse:
    """List all accounts for the current user's household.

    Args:
        service: AccountService from dependency injection.
        current_user: Authenticated user context from JWT.
        status_filter: Optional status filter (active, closed).
        type_filter: Optional account type filter.

    Returns:
        List of matching accounts.
    """
    accounts = service.get_household_accounts(
        household_id=current_user.household_id,
        status=status_filter,
        account_type=type_filter,
    )

    return AccountListResponse(
        accounts=[AccountResponse.from_domain(acc) for acc in accounts],
        total=len(accounts),
    )


@router.get(
    "/{account_id}",
    response_model=AccountResponse,
    summary="Get account by ID",
)
async def get_account(
    account_id: str,
    service: AccountServiceDep,
    current_user: CurrentUserDep,
) -> AccountResponse:
    """Get a single account by ID.

    Verifies the account belongs to the user's household.

    Args:
        account_id: The account identifier.
        service: AccountService from dependency injection.
        current_user: Authenticated user context from JWT.

    Returns:
        Account details.

    Raises:
        HTTPException: If account not found or belongs to different household.
    """
    try:
        parsed_id = AccountId.from_string(account_id)
    except (ValueError, SuffixValidationException) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid account ID format: {e}",
        )

    result = service.get_account(parsed_id, household_id=current_user.household_id)

    if isinstance(result, AccountError):
        _handle_error(result)

    return AccountResponse.from_domain(result)


# --- Update Endpoints ---


@router.patch(
    "/{account_id}",
    response_model=AccountResponse,
    summary="Update account",
)
async def update_account(
    account_id: str,
    request: UpdateAccountRequest,
    service: AccountServiceDep,
    current_user: CurrentUserDep,
) -> AccountResponse:
    """Update an account's editable fields.

    Only name, institution, and notes can be updated.
    Opening balance, type, and other core fields are immutable.

    Args:
        account_id: The account identifier.
        request: Fields to update.
        service: AccountService from dependency injection.
        current_user: Authenticated user context from JWT.

    Returns:
        Updated account details.

    Raises:
        HTTPException: If account not found or validation fails.
    """
    try:
        parsed_id = AccountId.from_string(account_id)
    except (ValueError, SuffixValidationException) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid account ID format: {e}",
        )

    # Get account to verify it exists and belongs to household
    account_result = service.get_account(
        parsed_id, household_id=current_user.household_id
    )
    if isinstance(account_result, AccountError):
        _handle_error(account_result)

    # Apply updates (only name is supported via service for now)
    if request.name is not None:
        result = await service.update_account_name(
            parsed_id,
            request.name,
            current_user.user_id,
            household_id=current_user.household_id,
        )
        if isinstance(result, AccountError):
            _handle_error(result)
        account_result = result

    # TODO: Add update_institution and update_notes to AccountService

    return AccountResponse.from_domain(account_result)


# --- Lifecycle Endpoints ---


@router.post(
    "/{account_id}/close",
    response_model=AccountResponse,
    summary="Close account",
)
async def close_account(
    account_id: str,
    service: AccountServiceDep,
    current_user: CurrentUserDep,
) -> AccountResponse:
    """Close an active account.

    Closed accounts retain their data but cannot be used for transactions.
    They can be reopened later if needed.

    Args:
        account_id: The account identifier.
        service: AccountService from dependency injection.
        current_user: Authenticated user context from JWT.

    Returns:
        Closed account details.

    Raises:
        HTTPException: If account not found or already closed.
    """
    try:
        parsed_id = AccountId.from_string(account_id)
    except (ValueError, SuffixValidationException) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid account ID format: {e}",
        )

    result = await service.close_account(
        parsed_id,
        current_user.user_id,
        household_id=current_user.household_id,
    )

    if isinstance(result, AccountError):
        _handle_error(result)

    return AccountResponse.from_domain(result)


@router.post(
    "/{account_id}/reopen",
    response_model=AccountResponse,
    summary="Reopen closed account",
)
async def reopen_account(
    account_id: str,
    service: AccountServiceDep,
    current_user: CurrentUserDep,
) -> AccountResponse:
    """Reopen a closed account.

    Returns the account to active status.

    Args:
        account_id: The account identifier.
        service: AccountService from dependency injection.
        current_user: Authenticated user context from JWT.

    Returns:
        Reopened account details.

    Raises:
        HTTPException: If account not found or not closed.
    """
    try:
        parsed_id = AccountId.from_string(account_id)
    except (ValueError, SuffixValidationException) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid account ID format: {e}",
        )

    result = await service.reopen_account(
        parsed_id,
        current_user.user_id,
        household_id=current_user.household_id,
    )

    if isinstance(result, AccountError):
        _handle_error(result)

    return AccountResponse.from_domain(result)


@router.delete(
    "/{account_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete account",
)
async def delete_account(
    account_id: str,
    service: AccountServiceDep,
    current_user: CurrentUserDep,
) -> None:
    """Delete an account.

    Only accounts without transactions can be deleted.
    Accounts with transaction history should be closed instead.

    Args:
        account_id: The account identifier.
        service: AccountService from dependency injection.
        current_user: Authenticated user context from JWT.

    Raises:
        HTTPException: If account not found or has transactions.
    """
    try:
        parsed_id = AccountId.from_string(account_id)
    except (ValueError, SuffixValidationException) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid account ID format: {e}",
        )

    result = await service.delete_account(
        parsed_id, household_id=current_user.household_id
    )

    if isinstance(result, AccountError):
        _handle_error(result)

    # 204 No Content - no return value
