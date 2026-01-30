"""FastAPI dependency injection providers."""

import os
from functools import lru_cache

from src.adapters.logging import get_logger
from src.adapters.security.encryption import FieldEncryption

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


# Add more dependencies as needed in later phases:
# - get_unit_of_work() -> UnitOfWork
# - get_account_repository() -> AccountRepository
