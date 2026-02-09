"""API schema modules for request/response validation."""

from .auth import (  # noqa: F401
    ErrorResponse as ErrorResponse,
    RegisterRequest as RegisterRequest,
    RegisterResponse as RegisterResponse,
    TokenResponse as TokenResponse,
    VerifyEmailResponse as VerifyEmailResponse,
)
