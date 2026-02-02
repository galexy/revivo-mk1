"""FastAPI application factory."""

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.adapters.logging import configure_logging, get_logger
from src.adapters.persistence.orm.mappers import start_mappers

from .routes import accounts, categories, health, transactions

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan events.
    Startup: Configure logging, start mappers
    Shutdown: Cleanup resources
    """
    # Startup
    environment = os.getenv("ENVIRONMENT", "development")
    log_level = os.getenv("LOG_LEVEL", "INFO")
    configure_logging(
        environment=environment,  # type: ignore[arg-type]
        log_level=log_level,
    )

    logger.info("application_starting", environment=environment)

    # Initialize ORM mappers
    start_mappers()
    logger.info("orm_mappers_initialized")

    yield

    # Shutdown
    logger.info("application_shutting_down")


def create_app() -> FastAPI:
    """
    Create FastAPI application instance.

    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title="Personal Finance API",
        description="Personal finance management with data sovereignty",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS middleware for web frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],  # React dev server
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health.router)
    app.include_router(accounts.router, prefix="/api/v1")
    app.include_router(categories.router, prefix="/api/v1")
    app.include_router(transactions.router, prefix="/api/v1")

    return app


# Application instance for uvicorn
app = create_app()
