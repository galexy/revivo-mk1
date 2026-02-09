"""Health check endpoint."""

from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from src.adapters.api.dependencies import get_settings

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Health check response."""

    status: Literal["healthy", "unhealthy"]
    environment: str
    version: str = "0.1.0"


@router.get("/health", response_model=HealthResponse)
async def health_check(
    settings: dict[str, str] = Depends(get_settings),
) -> HealthResponse:
    """
    Health check endpoint.

    Returns:
        Health status with environment info
    """
    return HealthResponse(
        status="healthy",
        environment=settings["environment"],
    )


@router.get("/ready")
async def readiness_check() -> dict[str, bool]:
    """
    Readiness check for Kubernetes.
    Checks if app is ready to receive traffic.

    TODO: Add database connectivity check in Phase 4
    """
    return {"ready": True}
