"""Authentication API routes.

Provides REST endpoints for authentication:
- POST /auth/register: Register new user (returns 202)
- POST /auth/token: OAuth2-compatible login (returns access token + refresh cookie)
- POST /auth/refresh: Rotate refresh token and get new access token
- GET /auth/verify: Verify email address via signed token
- POST /auth/logout: Clear refresh token cookie
- GET /auth/me: Get current user profile with household info

Design decisions:
- Registration always returns 202 (even on duplicate email) for enumeration protection
- Refresh tokens are stored in HttpOnly secure cookies (not in body)
- OAuth2PasswordRequestForm for /auth/token (standard OAuth2 flow)
- Generic error messages for all auth failures
- Cookie secure flag is environment-aware (True in production, False in development/test)
"""

import os
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Query, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from src.application.services.auth_service import AuthError, AuthService

from ..dependencies import CurrentUser, get_auth_service, get_current_user
from ..schemas.auth import (
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
    UserProfileResponse,
    VerifyEmailResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


# Type aliases
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]


# --- Cookie Configuration ---

REFRESH_TOKEN_COOKIE = "refresh_token"
REFRESH_TOKEN_MAX_AGE = 7 * 24 * 60 * 60  # 7 days in seconds


def _is_secure_cookies() -> bool:
    """Determine if cookies should use secure flag.

    Returns True in production (HTTPS), False in development/test (HTTP).
    """
    return os.getenv("ENVIRONMENT", "development") == "production"


def _set_refresh_cookie(response: Response, token: str) -> None:
    """Set refresh token as HttpOnly cookie.

    Secure flag is environment-aware: True in production (HTTPS required),
    False in development/test (allows HTTP for TestClient).

    Args:
        response: FastAPI response to set cookie on.
        token: Raw refresh token value.
    """
    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE,
        value=token,
        httponly=True,
        secure=_is_secure_cookies(),
        samesite="strict",
        path="/auth/refresh",
        max_age=REFRESH_TOKEN_MAX_AGE,
    )


def _clear_refresh_cookie(response: Response) -> None:
    """Clear refresh token cookie.

    Args:
        response: FastAPI response to clear cookie on.
    """
    response.delete_cookie(
        key=REFRESH_TOKEN_COOKIE,
        path="/auth/refresh",
        httponly=True,
        secure=_is_secure_cookies(),
        samesite="strict",
    )


# --- Endpoints ---


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Register new user",
)
async def register(
    request: RegisterRequest,
    service: AuthServiceDep,
) -> RegisterResponse:
    """Register a new user.

    Always returns 202 to prevent email enumeration attacks.
    On duplicate email, returns 202 with a generic user_id.

    Args:
        request: Registration data (email, password, display_name).
        service: AuthService from dependency injection.

    Returns:
        RegisterResponse with user_id and confirmation message.
    """
    result = await service.register(
        email=request.email,
        password=request.password,
        display_name=request.display_name,
    )

    if isinstance(result, AuthError):
        # Return 202 even on duplicate email (enumeration protection)
        return RegisterResponse(
            message="Registration successful. Please verify your email.",
            user_id="user_00000000000000000000000000",  # Generic placeholder
            email=request.email,
        )

    return RegisterResponse(
        message="Registration successful. Please verify your email.",
        user_id=str(result.user.id),
        email=result.user.email,
    )


@router.post(
    "/token",
    response_model=TokenResponse,
    summary="Login (OAuth2 compatible)",
)
async def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Authenticate user and return tokens.

    OAuth2-compatible endpoint. Uses username field for email.
    Access token returned in response body, refresh token set as HttpOnly cookie.

    Args:
        response: FastAPI response for setting cookies.
        form_data: OAuth2 form with username (email) and password.
        service: AuthService from dependency injection.

    Returns:
        TokenResponse with access_token.

    Raises:
        HTTPException: 401 if credentials are invalid.
    """
    result = await service.login(
        email=form_data.username,
        password=form_data.password,
    )

    if isinstance(result, AuthError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Set refresh token as HttpOnly cookie
    _set_refresh_cookie(response, result.refresh_token)

    return TokenResponse(
        access_token=result.access_token,
        token_type=result.token_type,
        expires_in=900,  # 15 minutes
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
)
async def refresh_token(
    response: Response,
    service: AuthService = Depends(get_auth_service),
    refresh_token: str | None = Cookie(default=None),
) -> TokenResponse:
    """Exchange refresh token for new access token.

    Reads refresh token from HttpOnly cookie. Rotates the refresh token
    (old token invalidated, new token issued in cookie).

    Args:
        response: FastAPI response for setting new cookie.
        service: AuthService from dependency injection.
        refresh_token: Refresh token from cookie.

    Returns:
        TokenResponse with new access_token.

    Raises:
        HTTPException: 401 if refresh token is missing, invalid, or expired.
    """
    if refresh_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token required",
        )

    result = await service.refresh(refresh_token)

    if isinstance(result, AuthError):
        _clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # Set new refresh token cookie (rotation)
    _set_refresh_cookie(response, result.refresh_token)

    return TokenResponse(
        access_token=result.access_token,
        token_type=result.token_type,
        expires_in=900,
    )


@router.get(
    "/verify",
    response_model=VerifyEmailResponse,
    summary="Verify email address",
)
async def verify_email(
    token: str = Query(..., description="Email verification token"),
    service: AuthService = Depends(get_auth_service),
) -> VerifyEmailResponse:
    """Verify a user's email address using a signed token.

    Args:
        token: The verification token from the email link.
        service: AuthService from dependency injection.

    Returns:
        VerifyEmailResponse with user info.

    Raises:
        HTTPException: 400 if token is invalid or expired.
    """
    result = await service.verify_email(token)

    if isinstance(result, AuthError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.message,
        )

    return VerifyEmailResponse(
        message="Email verified successfully",
        user_id=str(result.id),
        email=result.email,
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout (clear refresh token)",
)
async def logout(response: Response) -> None:
    """Clear refresh token cookie.

    Args:
        response: FastAPI response for clearing cookie.
    """
    _clear_refresh_cookie(response)


@router.get(
    "/me",
    response_model=UserProfileResponse,
    summary="Get current user profile",
)
async def get_current_user_profile(
    service: AuthServiceDep,
    current_user: CurrentUserDep,
) -> UserProfileResponse:
    """Get authenticated user's profile with household info.

    Returns user metadata (email, display_name, email_verified, created_at)
    and nested household object (id, name, is_owner flag).

    Args:
        service: AuthService from dependency injection.
        current_user: CurrentUser extracted from JWT.

    Returns:
        UserProfileResponse with user profile and household info.

    Raises:
        HTTPException: 404 if user not found (should not happen with valid JWT).
    """
    result = service.get_user_profile(current_user.user_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    user, household = result
    return UserProfileResponse.from_domain(user, household)
