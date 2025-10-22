"""Authentication middleware for FastAPI.

Provides dependency injection for protected endpoints that require authentication.
"""

import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User
from app.services.redis_service import RedisService


class HTTPBearerAuth(HTTPBearer):
    """Custom HTTPBearer that returns 401 instead of 403 for missing credentials."""

    async def __call__(self, request: Request) -> HTTPAuthorizationCredentials:
        """Override to return 401 for missing credentials."""
        try:
            return await super().__call__(request)
        except HTTPException as e:
            if e.status_code == 403:
                # Convert 403 (Forbidden) to 401 (Unauthorized) for missing credentials
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            raise


# HTTP Bearer token scheme
security = HTTPBearerAuth()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Extract and validate JWT from Authorization header.

    Flow:
    1. Extract Bearer token from Authorization header
    2. Decode JWT and validate signature
    3. Check if token is blacklisted in Redis
    4. Verify token hasn't expired
    5. Fetch user from database
    6. Verify user is active

    Args:
        credentials: HTTP Bearer credentials from Authorization header
        db: Database session

    Returns:
        Authenticated User object

    Raises:
        HTTPException 401: Invalid, expired, or blacklisted token
        HTTPException 403: User account deactivated

    Usage:
        @router.get("/protected")
        async def protected_route(
            current_user: Annotated[User, Depends(get_current_user)]
        ):
            return {"user_id": current_user.id}
    """
    token = credentials.credentials

    try:
        # Decode and validate JWT
        payload = decode_token(token)
        user_id_str = payload.get("sub")
        token_jti = payload.get("jti")

        if (
            not user_id_str
            or not token_jti
            or not isinstance(user_id_str, str)
            or not isinstance(token_jti, str)
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "INVALID_TOKEN",
                        "message": "Token missing required claims",
                    }
                },
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_id = uuid.UUID(user_id_str)

        # Check if token is blacklisted
        redis_service = RedisService()
        is_blacklisted = await redis_service.is_token_blacklisted(token_jti)
        if is_blacklisted:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "TOKEN_REVOKED",
                        "message": "Token has been revoked",
                    }
                },
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Fetch user from database
        from sqlalchemy import select

        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "USER_NOT_FOUND",
                        "message": "User not found",
                    }
                },
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check if user account is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": {
                        "code": "ACCOUNT_DEACTIVATED",
                        "message": "Account has been deactivated",
                    }
                },
            )

        # Fetch role name from roles table and attach to user object
        from sqlalchemy import text

        role_stmt = text("SELECT name FROM roles WHERE id = :role_id")
        role_result = await db.execute(role_stmt, {"role_id": user.role_id})
        role_name = role_result.scalar_one_or_none()

        # Attach role name to user object for permission checks
        user.role = role_name if role_name else "unknown"

        return user

    except ValueError as e:
        # Token decode errors (invalid signature, expired, etc.)
        error_msg = str(e)
        if "expired" in error_msg.lower():
            code = "TOKEN_EXPIRED"
            message = "Token has expired"
        else:
            code = "INVALID_TOKEN"
            message = "Invalid authentication token"

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": code, "message": message}},
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


async def get_current_active_user(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    """Get current user and verify email is verified.

    This is a stricter version of get_current_user that also checks email verification.

    Args:
        current_user: User from get_current_user dependency

    Returns:
        Authenticated User with verified email

    Raises:
        HTTPException 403: Email not verified

    Usage:
        @router.get("/protected")
        async def protected_route(
            current_user: Annotated[User, Depends(get_current_active_user)]
        ):
            # User is authenticated AND email verified
            return {"user_id": current_user.id}
    """
    if not current_user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "code": "EMAIL_NOT_VERIFIED",
                    "message": "Email verification required",
                }
            },
        )

    return current_user
