"""Consent management endpoints for GDPR compliance."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.consent import (
    ConsentAcceptRequest,
    ConsentHistoryResponse,
    ConsentResponse,
    ConsentStatusResponse,
    DataDeletionRequest,
    DataExportRequest,
)
from app.services.consent_service import ConsentService

logger = logging.getLogger(__name__)
router = APIRouter()
service = ConsentService()


@router.post("/accept", status_code=status.HTTP_201_CREATED, response_model=ConsentResponse)
async def accept_consent(
    request_data: ConsentAcceptRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ConsentResponse:
    """Accept legal documents (authenticated users).

    Records user's acceptance of Terms of Service and Privacy Policy.
    Supersedes any existing active consent.

    Args:
        request_data: Document IDs to accept
        request: FastAPI request for IP extraction
        current_user: Authenticated user

    Returns:
        Created consent record

    Raises:
        HTTPException 400: Invalid document IDs or not published
        HTTPException 401: Not authenticated
    """
    # Extract IP and user agent
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent")

    try:
        consent = await service.accept_consent(
            db=db,
            user=current_user,
            request=request_data,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        logger.info(f"User {current_user.email} accepted consent")
        return consent
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error accepting consent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to accept consent",
        )


@router.get("/status", response_model=ConsentStatusResponse)
async def get_consent_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ConsentStatusResponse:
    """Get user's current consent status.

    Returns whether user has active consent and if re-consent is required
    (when documents have been updated).

    Args:
        current_user: Authenticated user

    Returns:
        Consent status with version information

    Raises:
        HTTPException 401: Not authenticated
    """
    try:
        status_response = await service.get_consent_status(db=db, user=current_user)
        return status_response
    except Exception as e:
        logger.error(f"Error fetching consent status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch consent status",
        )


@router.get("/history", response_model=ConsentHistoryResponse)
async def get_consent_history(
    page: int = 1,
    per_page: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ConsentHistoryResponse:
    """Get user's consent history with pagination.

    Args:
        page: Page number (1-indexed)
        per_page: Items per page (default 20)
        current_user: Authenticated user

    Returns:
        Paginated consent history

    Raises:
        HTTPException 400: Invalid pagination parameters
        HTTPException 401: Not authenticated
    """
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page must be >= 1",
        )
    if per_page < 1 or per_page > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Per page must be between 1 and 100",
        )

    try:
        history = await service.get_consent_history(
            db=db, user=current_user, page=page, per_page=per_page
        )
        return history
    except Exception as e:
        logger.error(f"Error fetching consent history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch consent history",
        )


@router.post("/withdraw", response_model=MessageResponse)
async def withdraw_consent(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    """Withdraw consent (GDPR right to withdraw).

    Marks user's account as inactive. User will need to re-consent to reactivate.

    Args:
        request: FastAPI request for IP extraction
        current_user: Authenticated user

    Returns:
        Success message

    Raises:
        HTTPException 400: No active consent found
        HTTPException 401: Not authenticated
    """
    # Extract IP and user agent
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent")

    try:
        await service.withdraw_consent(
            db=db,
            user=current_user,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        logger.info(f"User {current_user.email} withdrew consent")
        return MessageResponse(
            message="Consent withdrawn successfully. Your account has been deactivated."
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error withdrawing consent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to withdraw consent",
        )


@router.post("/data-export", status_code=status.HTTP_202_ACCEPTED, response_model=MessageResponse)
async def request_data_export(
    request_data: DataExportRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    """Request GDPR data export (async job).

    Triggers an async job to generate a complete export of user's data.

    Args:
        request_data: Export request (optional email override)
        request: FastAPI request for IP extraction
        current_user: Authenticated user

    Returns:
        Acknowledgment message

    Raises:
        HTTPException 401: Not authenticated
    """
    # Extract IP and user agent
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent")

    try:
        await service.request_data_export(
            db=db,
            user=current_user,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        logger.info(f"User {current_user.email} requested data export")
        return MessageResponse(
            message="Data export request received. You will receive an email when ready."
        )
    except Exception as e:
        logger.error(f"Error requesting data export: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to request data export",
        )


@router.post("/data-deletion", status_code=status.HTTP_202_ACCEPTED, response_model=MessageResponse)
async def request_data_deletion(
    request_data: DataDeletionRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    """Request GDPR data deletion (30-day grace period).

    Schedules user account and data for deletion in 30 days.
    Account is immediately deactivated.

    Args:
        request_data: Deletion confirmation
        request: FastAPI request for IP extraction
        current_user: Authenticated user

    Returns:
        Acknowledgment message

    Raises:
        HTTPException 400: Confirmation not true
        HTTPException 401: Not authenticated
    """
    # Extract IP and user agent
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent")

    try:
        await service.request_data_deletion(
            db=db,
            user=current_user,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        logger.info(f"User {current_user.email} requested data deletion")
        return MessageResponse(
            message="Data deletion request received. Your account will be deleted in 30 days. "
            "Contact support to cancel this request."
        )
    except Exception as e:
        logger.error(f"Error requesting data deletion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to request data deletion",
        )
