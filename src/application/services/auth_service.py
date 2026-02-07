"""AuthService application service for authentication use case orchestration.

This service coordinates authentication use cases: registration, login,
token refresh, and email verification through the Unit of Work pattern.

Key responsibilities:
- Register new users with email, password, display name
- Authenticate users with email/password and issue JWT tokens
- Refresh access tokens using refresh tokens
- Verify email addresses via signed tokens
- Session management (logout all)

Design decisions:
- Uses UnitOfWork for transaction boundaries
- Returns AuthError for failures instead of raising exceptions
- Generic error messages for auth failures (prevent user enumeration)
- Password hashing delegated to security adapter (infrastructure)
- JWT creation delegated to security adapter (infrastructure)
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.adapters.security.jwt import create_access_token
from src.adapters.security.password import hash_password, verify_password
from src.adapters.security.tokens import generate_verification_token, verify_email_token
from src.domain.model.entity_id import UserId
from src.domain.model.household import Household
from src.domain.model.user import User

if TYPE_CHECKING:
    from src.domain.ports.unit_of_work import UnitOfWork


@dataclass(frozen=True, slots=True)
class AuthError:
    """Error result for authentication operations.

    Used instead of exceptions for expected failures.
    The API layer can convert these to appropriate HTTP responses.

    Attributes:
        code: Machine-readable error code (e.g., "INVALID_CREDENTIALS", "REGISTRATION_FAILED")
        message: Human-readable error message
    """

    code: str
    message: str


@dataclass(frozen=True, slots=True)
class AuthTokens:
    """Token pair returned on successful authentication.

    Attributes:
        access_token: Short-lived JWT for API access
        refresh_token: Long-lived token for obtaining new access tokens
        token_type: Token type (always "bearer")
    """

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


@dataclass(frozen=True, slots=True)
class RegistrationResult:
    """Result of successful user registration.

    Attributes:
        user: The newly created User
        household: The newly created Household
        verification_token: Email verification token to send to user
    """

    user: User
    household: Household
    verification_token: str


class AuthService:
    """Application service for authentication use cases.

    Coordinates domain operations, transaction boundaries, and event collection
    for registration, login, token refresh, and email verification.

    Example:
        service = AuthService(uow)
        result = service.register("user@example.com", "password", "User")
        if isinstance(result, RegistrationResult):
            # Success - send verification email
        else:
            # Handle AuthError

    Attributes:
        _uow: Unit of Work for transaction management.
    """

    def __init__(self, uow: "UnitOfWork") -> None:
        """Initialize AuthService with Unit of Work.

        Args:
            uow: Unit of Work for transaction management.
        """
        self._uow = uow

    async def register(
        self,
        email: str,
        password: str,
        display_name: str,
    ) -> RegistrationResult | AuthError:
        """Register a new user with email, password, and display name.

        Creates a User and Household atomically. The user's email is normalized
        to lowercase. Password is hashed using Argon2 before storage.

        Args:
            email: User's email address (will be normalized to lowercase).
            password: Plaintext password (will be hashed).
            display_name: User's display name.

        Returns:
            RegistrationResult on success, AuthError if email already exists.
        """
        normalized_email = email.lower().strip()

        with self._uow:
            # Check for existing email
            existing = self._uow.users.get_by_email(normalized_email)
            if existing is not None:
                return AuthError(
                    code="REGISTRATION_FAILED",
                    message="Registration failed",
                )

            # Hash password (infrastructure concern)
            password_hash = hash_password(password)

            # Create household and user (no circular FK dependency)
            household = Household.create(name=f"{display_name}'s Household")
            user = User.create(
                email=normalized_email,
                display_name=display_name,
                password_hash=password_hash,
                household_id=household.id,
                role="owner",
            )

            # Persist
            self._uow.households.add(household)
            self._uow.users.add(user)

            # Collect events from user (UserRegistered)
            events = user.collect_events()
            self._uow.collect_events(events)

            await self._uow.commit()

            # Generate verification token (outside transaction - stateless)
            verification_token = generate_verification_token(user.email)

            return RegistrationResult(
                user=user,
                household=household,
                verification_token=verification_token,
            )

    async def login(
        self,
        email: str,
        password: str,
    ) -> AuthTokens | AuthError:
        """Authenticate user with email and password.

        Returns JWT access token and refresh token on success.
        Uses generic error message for both nonexistent email and wrong password
        to prevent user enumeration.

        Args:
            email: User's email address.
            password: Plaintext password to verify.

        Returns:
            AuthTokens on success, AuthError on failure.
        """
        normalized_email = email.lower().strip()

        with self._uow:
            # Look up user by email
            user = self._uow.users.get_by_email(normalized_email)

            # Generic error for nonexistent email (prevent user enumeration)
            if user is None:
                return AuthError(
                    code="INVALID_CREDENTIALS",
                    message="Invalid credentials",
                )

            # Verify password
            if not verify_password(password, user.password_hash):
                return AuthError(
                    code="INVALID_CREDENTIALS",
                    message="Invalid credentials",
                )

            # Check email verification
            if not user.email_verified:
                return AuthError(
                    code="EMAIL_NOT_VERIFIED",
                    message="Email not verified. Please check your inbox.",
                )

            # Create access token (JWT)
            access_token = create_access_token(
                user_id=str(user.id),
                household_id=str(user.household_id),
            )

            # Create refresh token (stored in database)
            raw_refresh_token, _token_record = self._uow.refresh_tokens.create_token(
                user_id=user.id,
            )

            await self._uow.commit()

            return AuthTokens(
                access_token=access_token,
                refresh_token=raw_refresh_token,
            )

    async def refresh(
        self,
        refresh_token: str,
    ) -> AuthTokens | AuthError:
        """Exchange a refresh token for new access and refresh tokens.

        Validates the refresh token, rotates it (old token invalidated),
        and issues new token pair.

        Args:
            refresh_token: The refresh token to validate and rotate.

        Returns:
            AuthTokens on success, AuthError if token is invalid/expired.
        """
        with self._uow:
            # Validate and rotate refresh token
            result = self._uow.refresh_tokens.validate_and_rotate(refresh_token)

            if result is None:
                return AuthError(
                    code="INVALID_REFRESH_TOKEN",
                    message="Invalid or expired refresh token",
                )

            new_raw_token, token_record = result

            # Look up user to get household_id for access token
            user = self._uow.users.get_by_id(token_record.user_id)
            if user is None:
                return AuthError(
                    code="INVALID_REFRESH_TOKEN",
                    message="Invalid or expired refresh token",
                )

            # Create new access token
            access_token = create_access_token(
                user_id=str(user.id),
                household_id=str(user.household_id),
            )

            await self._uow.commit()

            return AuthTokens(
                access_token=access_token,
                refresh_token=new_raw_token,
            )

    async def verify_email(
        self,
        token: str,
    ) -> User | AuthError:
        """Verify a user's email using a verification token.

        Args:
            token: The email verification token.

        Returns:
            Updated User on success, AuthError if token is invalid.
        """
        # Validate token (stateless - no DB lookup needed)
        email = verify_email_token(token)
        if email is None:
            return AuthError(
                code="INVALID_VERIFICATION_TOKEN",
                message="Invalid or expired verification token",
            )

        with self._uow:
            # Look up user by email from token
            user = self._uow.users.get_by_email(email)
            if user is None:
                return AuthError(
                    code="INVALID_VERIFICATION_TOKEN",
                    message="Invalid or expired verification token",
                )

            # Mark email as verified (idempotent)
            user.verify_email()

            # Collect events
            events = user.collect_events()
            self._uow.collect_events(events)

            await self._uow.commit()

            return user

    async def logout_all_sessions(
        self,
        user_id: UserId,
    ) -> bool:
        """Revoke all refresh tokens for a user.

        Args:
            user_id: The user whose sessions to revoke.

        Returns:
            True on success.
        """
        with self._uow:
            self._uow.refresh_tokens.revoke_all_for_user(user_id)
            await self._uow.commit()
            return True

    def get_user_by_id(
        self,
        user_id: UserId,
    ) -> User | None:
        """Look up a user by their ID.

        Args:
            user_id: The user identifier.

        Returns:
            User if found, None otherwise.
        """
        with self._uow:
            return self._uow.users.get_by_id(user_id)

    def get_user_profile(
        self,
        user_id: UserId,
    ) -> tuple[User, Household] | None:
        """Load user and household for profile endpoint.

        Used by GET /auth/me to return user metadata with nested household info.

        Args:
            user_id: The user identifier.

        Returns:
            Tuple of (User, Household) if found, None if user not found.
        """
        with self._uow:
            user = self._uow.users.get_by_id(user_id)
            if user is None:
                return None
            household = self._uow.households.get_by_id(user.household_id)
            if household is None:
                return None  # Should not happen if FK constraint enforced
            return (user, household)
