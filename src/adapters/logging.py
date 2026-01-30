"""Structured logging configuration."""

import logging
import sys
from typing import Literal

import structlog


def configure_logging(
    environment: Literal["development", "production"] = "development",
    log_level: str = "INFO",
) -> None:
    """
    Configure structlog for structured logging.

    Args:
        environment: "development" for pretty output, "production" for JSON
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    In development:
        - Colored, human-readable output
        - Easy to scan in terminal

    In production:
        - JSON output for log aggregation (ELK, Datadog, etc.)
        - Structured fields for querying
    """
    shared_processors: list[structlog.types.Processor] = [
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.contextvars.merge_contextvars,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if environment == "development":
        # Human-readable output for development
        processors = [
            *shared_processors,
            structlog.dev.ConsoleRenderer(colors=True),
        ]
    else:
        # JSON output for production log aggregation
        processors = [
            *shared_processors,
            structlog.processors.JSONRenderer(),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging to use structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """
    Get a logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Structlog bound logger

    Usage:
        logger = get_logger(__name__)
        logger.info("user_created", user_id="user_xxx", email="test@example.com")
    """
    return structlog.get_logger(name)
