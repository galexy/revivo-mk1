"""FastAPI dependency injection providers.

Provides shared dependencies for API routes:
- Settings and encryption from environment/secrets
- Unit of Work for database transactions
- Service layer factories for domain operations
- Current user resolution via JWT authentication
- Auth service factory

Dependencies:
- get_current_user: Extracts and validates JWT, returns CurrentUser dataclass
- get_auth_service: Creates AuthService with UnitOfWork
"""

import os
from dataclasses import dataclass
from functools import lru_cache

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from domain.model.entity_id import HouseholdId, UserId
from src.adapters.logging import get_logger
from src.adapters.persistence.database import create_sync_session_factory
from src.adapters.persistence.unit_of_work import SqlAlchemyUnitOfWork
from src.adapters.security.encryption import FieldEncryption
from src.adapters.security.jwt import TokenError, decode_access_token
from src.application.services.auth_service import AuthService
from src.application.services.category_service import CategoryService
from src.application.services.transaction_service import TransactionService

logger = get_logger(__name__)


# OAuth2 scheme for extracting Bearer token from Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


@dataclass(frozen=True, slots=True)
class CurrentUser:
    """Authenticated user context extracted from JWT.

    Attributes:
        user_id: The authenticated user's ID.
        household_id: The user's household ID for data scoping.
    """

    user_id: UserId
    household_id: HouseholdId


@lru_cache
def get_settings() -> dict[str, str]:
    """
    Application settings from environment.
    Cached for performance.
    """
    return {
        "environment": os.getenv("ENVIRONMENT", "development"),
        "database_url": os.getenv(
            "DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/finance"
        ),
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
    }


def get_encryption() -> FieldEncryption:
    """
    Provide encryption service.
    Attempts Docker secrets first, falls back to env var.
    """
    try:
        return FieldEncryption.from_docker_secret()
    except FileNotFoundError:
        logger.warning("docker_secret_not_found", fallback="environment_variable")
        return FieldEncryption.from_env()


def get_unit_of_work() -> SqlAlchemyUnitOfWork:
    """Provide Unit of Work for the request.

    Creates a new UnitOfWork with a sync session factory.
    The UnitOfWork manages its own transaction lifecycle.

    Returns:
        SqlAlchemyUnitOfWork instance.
    """
    session_factory = create_sync_session_factory()
    return SqlAlchemyUnitOfWork(session_factory)


def get_current_user(
    token: str = Depends(oauth2_scheme),
) -> CurrentUser:
    """Extract and validate current user from JWT access token.

    Decodes the JWT, extracts user_id and household_id claims,
    and returns a CurrentUser dataclass.

    Args:
        token: JWT access token from Authorization header.

    Returns:
        CurrentUser with user_id and household_id.

    Raises:
        HTTPException: 401 if token is invalid, expired, or missing claims.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        user_id_str: str | None = payload.get("sub")
        household_id_str: str | None = payload.get("household_id")

        if user_id_str is None or household_id_str is None:
            raise credentials_exception

        return CurrentUser(
            user_id=UserId.from_string(user_id_str),
            household_id=HouseholdId.from_string(household_id_str),
        )
    except TokenError as exc:
        raise credentials_exception from exc
    except (ValueError, Exception) as exc:
        raise credentials_exception from exc


def get_auth_service(
    uow: SqlAlchemyUnitOfWork = Depends(get_unit_of_work),
) -> AuthService:
    """Provide AuthService with UnitOfWork.

    Args:
        uow: Unit of Work from dependency injection.

    Returns:
        AuthService configured with the UnitOfWork.
    """
    return AuthService(uow)


def get_category_service(
    uow: SqlAlchemyUnitOfWork = Depends(get_unit_of_work),
) -> CategoryService:
    """Provide CategoryService with UnitOfWork.

    Args:
        uow: Unit of Work from dependency injection.

    Returns:
        CategoryService configured with the UnitOfWork.
    """
    return CategoryService(uow)


def get_transaction_service(
    uow: SqlAlchemyUnitOfWork = Depends(get_unit_of_work),
) -> TransactionService:
    """Provide TransactionService with UnitOfWork.

    Args:
        uow: Unit of Work from dependency injection.

    Returns:
        TransactionService configured with the UnitOfWork.
    """
    return TransactionService(uow)
