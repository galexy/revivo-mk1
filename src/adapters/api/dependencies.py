"""FastAPI dependency injection providers.

Provides shared dependencies for API routes:
- Settings and encryption from environment/secrets
- Unit of Work for database transactions
- Service layer factories for domain operations
- Current user resolution (placeholder until Phase 4 auth)
"""

import os
from functools import lru_cache

from fastapi import Depends

from src.adapters.logging import get_logger
from src.adapters.persistence.database import create_sync_session_factory
from src.adapters.persistence.unit_of_work import SqlAlchemyUnitOfWork
from src.adapters.security.encryption import FieldEncryption
from src.application.services.category_service import CategoryService
from src.application.services.transaction_service import TransactionService
from src.domain.model.entity_id import UserId

logger = get_logger(__name__)


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


def get_current_user_id() -> UserId:
    """Provide current user ID.

    TODO (Phase 4): Replace with actual authentication.
    For now, returns a placeholder user ID for development.

    Returns:
        UserId for the current user.
    """
    # Placeholder user for development - will be replaced with auth in Phase 4
    return UserId.from_string("user_01h455vb4pex5vsknk084sn02q")


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
