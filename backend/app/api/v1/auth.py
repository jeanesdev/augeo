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
from app.schemas.password import (
    PasswordChangeRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
)
from app.services.auth_service import AuthService
from app.services.password_service import PasswordService
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


@router.post(
    "/password/reset/request", status_code=status.HTTP_200_OK, response_model=MessageResponse
)
async def request_password_reset(
    reset_data: PasswordResetRequest,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Request password reset email.

    Flow:
    1. Validates email format (Pydantic)
    2. Looks up user by email (case-insensitive)
    3. Generates secure reset token (32 bytes)
    4. Stores hashed token in Redis (1-hour expiry)
    5. Sends reset email with link
    6. Always returns success (prevent email enumeration)

    Business Rules:
    - Always returns 200 OK, even if email doesn't exist (security)
    - Token is URL-safe, one-time use, expires in 1 hour
    - Previous reset tokens are invalidated
    - Email contains reset link: {frontend_url}/reset-password?token=xxx

    Args:
        reset_data: Contains email address
        db: Database session

    Returns:
        MessageResponse confirming email sent (always success)
    """
    try:
        await PasswordService.request_reset(reset_data.email, db)
        return MessageResponse(message="If that email exists, a password reset link has been sent.")
    except Exception:
        # Always return success to prevent email enumeration
        return MessageResponse(message="If that email exists, a password reset link has been sent.")


@router.post(
    "/password/reset/confirm", status_code=status.HTTP_200_OK, response_model=MessageResponse
)
async def confirm_password_reset(
    confirm_data: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Confirm password reset with token.

    Flow:
    1. Validates token format and password strength (Pydantic)
    2. Looks up user by hashed token in Redis
    3. Validates token exists and hasn't expired
    4. Updates user password (bcrypt hash)
    5. Deletes token from Redis (one-time use)
    6. Revokes ALL active sessions (force re-login)
    7. Returns success message

    Business Rules:
    - Token is one-time use (deleted after consumption)
    - Token expires after 1 hour
    - Password must be 8-100 chars with 1 letter and 1 number
    - All sessions are revoked (user must login with new password)

    Args:
        confirm_data: Contains token and new_password
        db: Database session

    Returns:
        MessageResponse confirming password reset

    Raises:
        HTTPException 400: Invalid or expired token
    """
    try:
        await PasswordService.confirm_reset(confirm_data.token, confirm_data.new_password, db)
        return MessageResponse(
            message="Password reset successfully. Please login with your new password."
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_TOKEN",
                "message": str(e) or "Invalid or expired reset token",
            },
        ) from e


@router.post("/password/change", status_code=status.HTTP_200_OK, response_model=MessageResponse)
async def change_password(
    change_data: PasswordChangeRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Change password for authenticated user.

    Flow:
    1. Extract and validate access token from Authorization header
    2. Decode token to get user_id and jti
    3. Validate current password matches
    4. Update to new password (bcrypt hash)
    5. Revoke all sessions EXCEPT current one (no forced logout)
    6. Returns success message

    Business Rules:
    - Must be authenticated (valid access token required)
    - Current password must be correct
    - New password must be 8-100 chars with 1 letter and 1 number
    - All OTHER sessions are revoked (current session preserved)
    - Current session remains valid with same tokens

    Args:
        change_data: Contains current_password and new_password
        request: FastAPI request for Authorization header
        db: Database session

    Returns:
        MessageResponse confirming password change

    Raises:
        HTTPException 401: Missing or invalid token
        HTTPException 400: Current password incorrect
    """
    # Extract access token from Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "MISSING_TOKEN",
                "message": "Authorization header required",
            },
        )

    access_token = auth_header.replace("Bearer ", "")

    try:
        # Decode access token to get user_id and jti
        payload = decode_token(access_token)
        user_id = payload["sub"]
        current_jti = payload["jti"]

        # Change password (validates current password internally)
        await PasswordService.change_password(
            user_id=user_id,
            current_password=change_data.current_password,
            new_password=change_data.new_password,
            current_jti=current_jti,
            db=db,
        )

        return MessageResponse(message="Password changed successfully.")

    except ValueError as e:
        error_msg = str(e)

        if "incorrect" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "INVALID_PASSWORD",
                    "message": "Current password is incorrect",
                },
            ) from e

        # Fallback for unexpected errors
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "PASSWORD_CHANGE_FAILED", "message": error_msg},
        ) from e
    except Exception as e:
        # Handle token decode errors
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "INVALID_TOKEN",
                "message": "Invalid or expired token",
            },
        ) from e
