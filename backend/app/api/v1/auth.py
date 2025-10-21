"""Authentication endpoints."""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    MessageResponse,
    UserCreate,
    UserPublic,
    UserRegisterResponse,
)
from app.services.auth_service import AuthService
from app.services.redis_service import RedisService

router = APIRouter()


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserRegisterResponse)
async def register(
    user_data: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> UserRegisterResponse:
    """Register a new user.

    Flow:
    1. Validates email uniqueness and password strength
    2. Creates user with email_verified=false, is_active=false
    3. Generates verification token (24-hour expiry)
    4. Returns user details and success message

    Business Rules:
    - Email must be unique (case-insensitive)
    - Password must be 8-100 chars with at least 1 letter and 1 number
    - Default role: "donor"
    - Account cannot login until email verified

    Args:
        user_data: User registration data (email, password, name, phone)
        request: FastAPI request object for IP tracking
        db: Database session

    Returns:
        UserRegisterResponse with user data and verification message

    Raises:
        HTTPException 409: Email already registered
        HTTPException 422: Validation errors (handled by Pydantic)
    """
    try:
        # Register user and get verification token
        user, verification_token = await AuthService.register(db, user_data)

        # TODO: Send verification email (EmailService in User Story 2)
        # For now, token would need to be logged or returned in dev mode

        # Build response
        user_public = UserPublic(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            phone=user.phone,
            email_verified=user.email_verified,
            is_active=user.is_active,
            role="donor",  # Hardcoded until Role model exists
            npo_id=user.npo_id,
            created_at=user.created_at,
        )

        return UserRegisterResponse(
            user=user_public,
            message=f"Verification email sent to {user.email}",
        )

    except ValueError as e:
        if "Email already registered" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": {
                        "code": "DUPLICATE_EMAIL",
                        "message": "Email already registered",
                        "details": {"email": user_data.email},
                    }
                },
            ) from e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "REGISTRATION_FAILED", "message": str(e)}},
        ) from e


@router.post("/login", status_code=status.HTTP_200_OK, response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    """Authenticate user and create session.

    Flow:
    1. Check rate limit (5 attempts per 15 min per IP)
    2. Validate credentials (email + password)
    3. Enforce email verification requirement
    4. Create session with device fingerprint
    5. Generate JWT tokens (15-min access, 7-day refresh)
    6. Return tokens and user details

    Business Rules:
    - Rate limit: 5 failed attempts per 15 minutes per IP
    - Account must have email_verified=true
    - Account must have is_active=true
    - Session tracks IP, user-agent, expires after 7 days
    - Refresh token includes JTI for revocation

    Args:
        login_data: Login credentials (email, password)
        request: FastAPI request object for IP and user-agent
        db: Database session

    Returns:
        LoginResponse with access_token, refresh_token, user data

    Raises:
        HTTPException 400: Email not verified
        HTTPException 401: Invalid credentials
        HTTPException 403: Account deactivated
        HTTPException 429: Rate limit exceeded
    """
    # Extract client info
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("User-Agent", "unknown")

    # Check rate limit (5 attempts per 15 min per IP)
    redis_service = RedisService()
    rate_limit_key = f"login_attempt:{ip_address}"
    if await redis_service.check_rate_limit(rate_limit_key, max_attempts=5, window_seconds=900):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": {
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": "Too many login attempts. Please try again in 15 minutes.",
                    "details": {"retry_after_seconds": 900},
                }
            },
        )

    try:
        # Authenticate and create session
        login_response = await AuthService.login(
            db=db,
            email=login_data.email,
            password=login_data.password,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return login_response

    except ValueError as e:
        error_msg = str(e)

        if "Invalid email or password" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "INVALID_CREDENTIALS",
                        "message": "Invalid email or password",
                    }
                },
            ) from e
        elif "Email not verified" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": {
                        "code": "EMAIL_NOT_VERIFIED",
                        "message": "Please verify your email before logging in",
                        "details": {"email": login_data.email},
                    }
                },
            ) from e
        elif "Account deactivated" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": {
                        "code": "ACCOUNT_DEACTIVATED",
                        "message": "Your account has been deactivated. Please contact support.",
                    }
                },
            ) from e

        # Fallback for unexpected errors
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "LOGIN_FAILED", "message": error_msg}},
        ) from e


@router.post("/refresh", status_code=status.HTTP_200_OK)
async def refresh_token(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """
    Refresh access token using refresh token.

    TODO: Implement token refresh logic.
    """
    return {"message": "Token refresh endpoint - to be implemented"}


@router.post("/logout", status_code=status.HTTP_200_OK, response_model=MessageResponse)
async def logout(
    logout_data: LogoutRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Logout user and invalidate tokens.

    Flow:
    1. Extract Authorization header to get access token
    2. Decode access token to extract user_id and jti
    3. Revoke refresh token (blacklist in Redis)
    4. Revoke active session in PostgreSQL (soft delete)
    5. Return success message

    Business Rules:
    - Access token must be valid (not expired, not blacklisted)
    - Refresh token gets blacklisted for remaining TTL
    - Session record gets revoked_at timestamp
    - Redis cache invalidated for session

    Args:
        logout_data: Contains refresh_token
        request: FastAPI request for Authorization header
        db: Database session

    Returns:
        MessageResponse with success confirmation

    Raises:
        HTTPException 401: Invalid or expired tokens
        HTTPException 400: Missing Authorization header
    """
    # Extract access token from Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "MISSING_TOKEN",
                    "message": "Authorization header required",
                }
            },
        )

    access_token = auth_header.replace("Bearer ", "")

    try:
        # Decode access token to get user_id and jti
        payload = decode_token(access_token)
        user_id = payload["sub"]
        access_token_jti = payload["jti"]

        # Logout and invalidate tokens
        await AuthService.logout(
            db=db,
            user_id=user_id,
            refresh_token=logout_data.refresh_token,
            access_token_jti=access_token_jti,
        )

        return MessageResponse(message="Logged out successfully")

    except ValueError as e:
        error_msg = str(e)

        if "Invalid" in error_msg or "expired" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "INVALID_TOKEN",
                        "message": "Invalid or expired token",
                    }
                },
            ) from e

        # Fallback for unexpected errors
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "LOGOUT_FAILED", "message": error_msg}},
        ) from e


@router.post("/verify-email", status_code=status.HTTP_200_OK)
async def verify_email(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """
    Verify email address with token.

    TODO: Implement email verification logic.
    """
    return {"message": "Email verification endpoint - to be implemented"}


@router.post("/password-reset/request", status_code=status.HTTP_200_OK)
async def request_password_reset(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """
    Request password reset email.

    TODO: Implement password reset request logic.
    """
    return {"message": "Password reset request endpoint - to be implemented"}


@router.post("/password-reset/confirm", status_code=status.HTTP_200_OK)
async def confirm_password_reset(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """
    Confirm password reset with token and new password.

    TODO: Implement password reset confirmation logic.
    """
    return {"message": "Password reset confirmation endpoint - to be implemented"}
