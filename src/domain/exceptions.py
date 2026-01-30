"""Domain exceptions for error handling.

This module defines the exception hierarchy for domain-level errors.
These exceptions represent problems in the domain logic, not infrastructure
failures.

Exception hierarchy:
- DomainException: Base for all domain errors
  - EntityNotFoundError: Entity lookup failed
  - ValidationError: Domain validation failed
  - BusinessRuleViolationError: Business rule was violated

Usage guidelines:
- Use exceptions for unexpected errors and bugs
- Consider Result type for expected failures (validation in APIs)
- Include context dict for debugging information
"""

from typing import Any


class DomainException(Exception):
    """Base exception for all domain errors.

    All domain-specific exceptions should inherit from this class.
    Provides a message and optional context dict for additional info.

    Attributes:
        message: Human-readable error message.
        context: Optional dictionary with additional error context.
    """

    def __init__(self, message: str, context: dict[str, Any] | None = None) -> None:
        """Initialize the exception.

        Args:
            message: Human-readable error message.
            context: Optional dictionary with additional context for debugging.
        """
        super().__init__(message)
        self.message = message
        self.context = context or {}

    def __str__(self) -> str:
        """Return string representation including context if present."""
        if self.context:
            return f"{self.message} (context: {self.context})"
        return self.message


class EntityNotFoundError(DomainException):
    """Raised when an entity lookup fails.

    Use this when an expected entity doesn't exist in the repository.

    Example:
        raise EntityNotFoundError(
            "Account not found",
            context={"account_id": str(account_id)}
        )
    """

    def __init__(
        self,
        message: str = "Entity not found",
        context: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the exception.

        Args:
            message: Human-readable error message.
            context: Optional dictionary with entity identifier info.
        """
        super().__init__(message, context)


class ValidationError(DomainException):
    """Raised when domain validation fails.

    Use this for validation of domain invariants that can't be
    expressed through the type system.

    Example:
        raise ValidationError(
            "Account balance cannot be negative",
            context={"balance": str(balance), "account_id": str(account_id)}
        )
    """

    def __init__(
        self,
        message: str = "Validation failed",
        context: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the exception.

        Args:
            message: Human-readable error message.
            context: Optional dictionary with validation failure details.
        """
        super().__init__(message, context)


class BusinessRuleViolationError(DomainException):
    """Raised when a business rule is violated.

    Use this for violations of business rules that go beyond simple
    validation, such as insufficient funds, unauthorized operations,
    or state transition violations.

    Example:
        raise BusinessRuleViolationError(
            "Insufficient funds for withdrawal",
            context={
                "available": str(available),
                "requested": str(requested),
                "account_id": str(account_id)
            }
        )
    """

    def __init__(
        self,
        message: str = "Business rule violated",
        context: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the exception.

        Args:
            message: Human-readable error message.
            context: Optional dictionary with rule violation details.
        """
        super().__init__(message, context)
