"""Pydantic schemas for Authentication API endpoints.

Provides request/response schemas for auth operations:
- RegisterRequest: User registration with password complexity validation
- TokenResponse: OAuth2-compatible token response
- VerifyEmailResponse: Email verification result
- UserProfileResponse: Authenticated user profile with household info
- ErrorResponse: Structured error response

Password complexity rules:
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number
- At least one symbol (!@#$%^&*...)
"""

import re
from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

if TYPE_CHECKING:
    from src.domain.model.household import Household
    from src.domain.model.user import User


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


class HouseholdResponse(BaseModel):
    """Nested household info in user profile response."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Household ID (hh_xxx format)")
    name: str = Field(..., description="Household display name")
    is_owner: bool = Field(..., description="Whether user owns this household")


class UserProfileResponse(BaseModel):
    """User profile with household info.

    Returned by GET /auth/me for displaying user context (welcome message,
    household info) in the frontend. Prepares is_owner flag for Phase 25
    (Multi-User Households).
    """

    model_config = ConfigDict(from_attributes=True)

    user_id: str = Field(..., description="User ID (user_xxx format)")
    email: str = Field(..., description="User email address")
    display_name: str = Field(..., description="User display name")
    email_verified: bool = Field(..., description="Whether email is verified")
    created_at: datetime = Field(..., description="Account creation timestamp (member since)")
    household: HouseholdResponse = Field(..., description="User's household info")

    @classmethod
    def from_domain(
        cls,
        user: "User",
        household: "Household",
    ) -> "UserProfileResponse":
        """Construct response from domain objects.

        Args:
            user: User domain entity.
            household: Household domain entity.

        Returns:
            UserProfileResponse with nested HouseholdResponse.
        """
        return cls(
            user_id=str(user.id),
            email=user.email,
            display_name=user.display_name,
            email_verified=user.email_verified,
            created_at=user.created_at,
            household=HouseholdResponse(
                id=str(household.id),
                name=household.name,
                is_owner=(user.role == "owner"),
            ),
        )
