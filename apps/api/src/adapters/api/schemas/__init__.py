"""API schema modules for request/response validation."""

from .auth import (  # noqa: F401
    ErrorResponse,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
    VerifyEmailResponse,
)
