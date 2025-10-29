"""Cookie consent endpoints for EU Cookie Law compliance."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import get_current_user_optional
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.cookies import (
    CookieConsentRequest,
    CookieConsentResponse,
    CookieConsentStatusResponse,
    CookieConsentUpdateRequest,
)
from app.services.cookie_consent_service import CookieConsentService

logger = logging.getLogger(__name__)
router = APIRouter()
service = CookieConsentService()


@router.get("/consent", response_model=CookieConsentStatusResponse)
async def get_cookie_consent(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> CookieConsentStatusResponse:
    """Get cookie consent status (public endpoint).

    Works for both authenticated and anonymous users.
    For anonymous users, uses session_id from cookie/header.

    Args:
        request: FastAPI request
        current_user: Optional authenticated user

    Returns:
        Cookie consent status
    """
    # Get session ID from cookie or header (for anonymous users)
    session_id = None
    if not current_user:
        session_id = request.cookies.get("session_id") or request.headers.get("X-Session-ID")
        if not session_id:
            # No consent recorded - return defaults
            return CookieConsentStatusResponse(
                essential=True,
                analytics=False,
                marketing=False,
                has_consent=False,
            )

    try:
        status_response = await service.get_cookie_consent(
            db=db, user=current_user, session_id=session_id
        )
        return status_response
    except Exception as e:
        logger.error(f"Error fetching cookie consent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch cookie consent",
        )


@router.post("/consent", status_code=status.HTTP_201_CREATED, response_model=CookieConsentResponse)
async def set_cookie_consent(
    request_data: CookieConsentRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> CookieConsentResponse:
    """Set cookie consent preferences (public endpoint).

    Works for both authenticated and anonymous users.
    For anonymous users, requires session_id in cookie/header.

    Args:
        request_data: Cookie preferences
        request: FastAPI request for IP extraction
        current_user: Optional authenticated user

    Returns:
        Created cookie consent

    Raises:
        HTTPException 400: Missing session_id for anonymous user
    """
    # Get session ID for anonymous users
    session_id = None
    if not current_user:
        session_id = request.cookies.get("session_id") or request.headers.get("X-Session-ID")
        if not session_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session ID required for anonymous users",
            )

    # Extract IP and user agent
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent")

    try:
        consent = await service.set_cookie_consent(
            db=db,
            request=request_data,
            ip_address=ip_address,
            user_agent=user_agent,
            user=current_user,
            session_id=session_id,
        )
        user_id = current_user.email if current_user else session_id
        logger.info(f"Cookie consent set for {user_id}")
        return consent
    except Exception as e:
        logger.error(f"Error setting cookie consent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set cookie consent",
        )


@router.put("/consent", response_model=CookieConsentResponse)
async def update_cookie_consent(
    request_data: CookieConsentUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> CookieConsentResponse:
    """Update cookie consent preferences (public endpoint).

    Works for both authenticated and anonymous users.

    Args:
        request_data: Updated cookie preferences
        request: FastAPI request for IP extraction
        current_user: Optional authenticated user

    Returns:
        Updated cookie consent

    Raises:
        HTTPException 400: Missing session_id for anonymous user
    """
    # Get session ID for anonymous users
    session_id = None
    if not current_user:
        session_id = request.cookies.get("session_id") or request.headers.get("X-Session-ID")
        if not session_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session ID required for anonymous users",
            )

    # Extract IP and user agent
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent")

    try:
        consent = await service.update_cookie_consent(
            db=db,
            request=request_data,
            ip_address=ip_address,
            user_agent=user_agent,
            user=current_user,
            session_id=session_id,
        )
        user_id = current_user.email if current_user else session_id
        logger.info(f"Cookie consent updated for {user_id}")
        return consent
    except Exception as e:
        logger.error(f"Error updating cookie consent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update cookie consent",
        )


@router.delete("/consent", response_model=MessageResponse)
async def revoke_cookie_consent(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> MessageResponse:
    """Revoke cookie consent (reject all non-essential).

    Sets analytics and marketing to false.

    Args:
        request: FastAPI request for IP extraction
        current_user: Optional authenticated user

    Returns:
        Success message

    Raises:
        HTTPException 400: Missing session_id for anonymous user
    """
    # Get session ID for anonymous users
    session_id = None
    if not current_user:
        session_id = request.cookies.get("session_id") or request.headers.get("X-Session-ID")
        if not session_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session ID required for anonymous users",
            )

    # Extract IP and user agent
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent")

    try:
        await service.revoke_cookie_consent(
            db=db,
            ip_address=ip_address,
            user_agent=user_agent,
            user=current_user,
            session_id=session_id,
        )
        user_id = current_user.email if current_user else session_id
        logger.info(f"Cookie consent revoked for {user_id}")
        return MessageResponse(message="Cookie consent revoked successfully")
    except Exception as e:
        logger.error(f"Error revoking cookie consent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke cookie consent",
        )
