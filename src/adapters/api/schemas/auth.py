"""Pydantic schemas for Authentication API endpoints.

Provides request/response schemas for auth operations:
- RegisterRequest: User registration with password complexity validation
- TokenResponse: OAuth2-compatible token response
- VerifyEmailResponse: Email verification result
- ErrorResponse: Structured error response

Password complexity rules:
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number
- At least one symbol (!@#$%^&*...)
"""

import re

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    """Request schema for user registration.

    Validates email format, password complexity, and display name.
    """

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="Password (8+ chars, mixed case, number, symbol)")
    display_name: str = Field(..., description="User display name")
    household_name: str | None = Field(
        default=None, description="Household name (defaults to '{display_name}'s Household')"
    )

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        """Validate password meets complexity requirements."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one number")
        if not re.search(r"[^A-Za-z0-9]", v):
            raise ValueError("Password must contain at least one symbol")
        return v

    @field_validator("display_name")
    @classmethod
    def validate_display_name(cls, v: str) -> str:
        """Validate display name is not empty after stripping."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("Display name must not be empty")
        return stripped


class RegisterResponse(BaseModel):
    """Response schema for successful registration."""

    model_config = ConfigDict(from_attributes=True)

    message: str = Field(..., description="Success message")
    user_id: str = Field(..., description="Created user ID")
    email: str = Field(..., description="Registered email")


class TokenResponse(BaseModel):
    """OAuth2-compatible token response."""

    model_config = ConfigDict(from_attributes=True)

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(default=900, description="Token lifetime in seconds")


class VerifyEmailResponse(BaseModel):
    """Response schema for email verification."""

    model_config = ConfigDict(from_attributes=True)

    message: str = Field(..., description="Verification message")
    user_id: str = Field(..., description="Verified user ID")
    email: str = Field(..., description="Verified email address")


class ErrorResponse(BaseModel):
    """Structured error response."""

    detail: str = Field(..., description="Error message")
    code: str = Field(..., description="Machine-readable error code")
