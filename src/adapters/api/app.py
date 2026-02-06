"""FastAPI application factory."""

import asyncio
import contextlib
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typeid.core.errors import TypeIDException

from src.adapters.logging import configure_logging, get_logger
from src.adapters.persistence.orm.mappers import start_mappers
from src.application.handlers import register_all_handlers

from .routes import accounts, auth, categories, health, transactions

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan events.
    Startup: Configure logging, start mappers, register handlers, start worker
    Shutdown: Stop worker, cleanup resources
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

    # Register event handlers
    register_all_handlers()
    logger.info("event_handlers_registered")

    # Start job queue worker in background (if job queue database available)
    worker_task: asyncio.Task[None] | None = None
    job_queue_enabled = os.getenv("JOB_QUEUE_ENABLED", "true").lower() == "true"

    if job_queue_enabled:
        try:
            from src.adapters.jobs import job_queue

            async with job_queue.open_async():
                worker_task = asyncio.create_task(
                    job_queue.run_worker_async(install_signal_handlers=False)
                )
                logger.info("job_queue_worker_started")

                yield

                # Shutdown: cancel worker
                if worker_task:
                    worker_task.cancel()
                    with contextlib.suppress(TimeoutError, asyncio.CancelledError):
                        await asyncio.wait_for(worker_task, timeout=10)
                    logger.info("job_queue_worker_stopped")
        except Exception as e:
            logger.warning("job_queue_failed_to_start", error=str(e))
            yield
    else:
        logger.info("job_queue_disabled")
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

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
        """Convert ValueError to 400 Bad Request.

        Handles:
        - Domain validation errors (invalid split configuration)
        - Empty string validation errors
        """
        return JSONResponse(
            status_code=400,
            content={
                "detail": {
                    "code": "VALIDATION_ERROR",
                    "message": str(exc),
                }
            },
        )

    @app.exception_handler(TypeIDException)
    async def typeid_error_handler(
        request: Request, exc: TypeIDException
    ) -> JSONResponse:
        """Convert TypeIDException to 400 Bad Request.

        Handles:
        - TypeID parsing failures (invalid format, wrong prefix)
        - Invalid ID formats in request
        """
        return JSONResponse(
            status_code=400,
            content={
                "detail": {
                    "code": "INVALID_ID_FORMAT",
                    "message": str(exc),
                }
            },
        )

    # Include routers
    app.include_router(health.router)
    app.include_router(auth.router)  # Auth routes at /auth (no API version prefix)
    app.include_router(accounts.router, prefix="/api/v1")
    app.include_router(categories.router, prefix="/api/v1")
    app.include_router(transactions.router, prefix="/api/v1")

    return app


# Application instance for uvicorn
app = create_app()
