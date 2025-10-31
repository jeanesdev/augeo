"""Legal document management endpoints."""

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import get_current_user, require_role
from app.models.legal_document import LegalDocumentStatus, LegalDocumentType
from app.models.user import User
from app.schemas.legal_documents import (
    LegalDocumentCreateRequest,
    LegalDocumentListResponse,
    LegalDocumentPublicResponse,
    LegalDocumentResponse,
    LegalDocumentUpdateRequest,
)
from app.services.legal_document_service import LegalDocumentService

logger = logging.getLogger(__name__)
router = APIRouter()
service = LegalDocumentService()


@router.get("/documents", response_model=list[LegalDocumentPublicResponse])
async def get_current_documents(
    db: AsyncSession = Depends(get_db),
) -> list[LegalDocumentPublicResponse]:
    """Get all currently published legal documents (public endpoint).

    Returns the latest published version of Terms of Service and Privacy Policy.
    No authentication required.

    Returns:
        List of published documents
    """
    try:
        documents = await service.get_all_current_published(db=db)
        return documents
    except Exception as e:
        logger.error(f"Error fetching current documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch documents",
        )


@router.get("/documents/{document_type}", response_model=LegalDocumentPublicResponse)
async def get_document_by_type(
    document_type: str,
    db: AsyncSession = Depends(get_db),
) -> LegalDocumentPublicResponse:
    """Get current published document by type (public endpoint).

    Args:
        document_type: 'terms_of_service' or 'privacy_policy'

    Returns:
        Published document

    Raises:
        HTTPException 400: Invalid document type
        HTTPException 404: Document not found
    """
    # Validate document type
    try:
        doc_type = LegalDocumentType(document_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document type. Must be 'terms_of_service' or 'privacy_policy'",
        )

    try:
        document = await service.get_current_published(db=db, document_type=doc_type)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No published {document_type} found",
            )

        return LegalDocumentPublicResponse.model_validate(document)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching document {document_type}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch document",
        )


@router.get(
    "/documents/{document_type}/version/{version}",
    response_model=LegalDocumentPublicResponse,
)
async def get_document_by_version(
    document_type: str,
    version: str,
    db: AsyncSession = Depends(get_db),
) -> LegalDocumentPublicResponse:
    """Get specific document version (public endpoint).

    Args:
        document_type: 'terms_of_service' or 'privacy_policy'
        version: Semantic version (e.g., '1.0', '2.1')

    Returns:
        Document at specified version

    Raises:
        HTTPException 400: Invalid document type or version format
        HTTPException 404: Document not found
    """
    # Validate document type
    try:
        doc_type = LegalDocumentType(document_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document type. Must be 'terms_of_service' or 'privacy_policy'",
        )

    try:
        document = await service.get_by_type_and_version(
            db=db, document_type=doc_type, version=version
        )
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_type} v{version} not found",
            )

        return LegalDocumentPublicResponse.model_validate(document)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching document {document_type} v{version}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch document",
        )


# ================================
# Admin Endpoints
# ================================


@router.post(
    "/admin/documents",
    status_code=status.HTTP_201_CREATED,
    response_model=LegalDocumentResponse,
)
@require_role("super_admin")
async def create_document(
    request: LegalDocumentCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LegalDocumentResponse:
    """Create a new legal document (admin only).

    Creates a new document in DRAFT status.

    Args:
        request: Document creation data

    Returns:
        Created document

    Raises:
        HTTPException 400: Document with same type+version exists
        HTTPException 401: Not authenticated
        HTTPException 403: Not super admin
    """
    try:
        document = await service.create_document(db=db, request=request)
        logger.info(
            f"Admin {current_user.email} created document {document.document_type} v{document.version}"
        )
        return LegalDocumentResponse.model_validate(document)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error creating document: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create document",
        )


@router.patch(
    "/admin/documents/{document_id}",
    response_model=LegalDocumentResponse,
)
@require_role("super_admin")
async def update_draft_document(
    document_id: uuid.UUID,
    request: LegalDocumentUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LegalDocumentResponse:
    """Update a draft legal document (admin only).

    Only DRAFT documents can be updated.

    Args:
        document_id: Document ID
        request: Update data

    Returns:
        Updated document

    Raises:
        HTTPException 400: Document not in draft status
        HTTPException 404: Document not found
        HTTPException 401: Not authenticated
        HTTPException 403: Not super admin
    """
    try:
        document = await service.update_document(db=db, document_id=document_id, request=request)
        logger.info(
            f"Admin {current_user.email} updated document {document.document_type} v{document.version}"
        )
        return LegalDocumentResponse.model_validate(document)
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error updating document {document_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update document",
        )


@router.post(
    "/admin/documents/{document_id}/publish",
    response_model=LegalDocumentResponse,
)
@require_role("super_admin")
async def publish_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LegalDocumentResponse:
    """Publish a draft legal document (admin only).

    Publishing archives any existing published document of the same type.

    Args:
        document_id: Document ID

    Returns:
        Published document

    Raises:
        HTTPException 400: Document not in draft status
        HTTPException 404: Document not found
        HTTPException 401: Not authenticated
        HTTPException 403: Not super admin
    """
    try:
        document = await service.publish_document(db=db, document_id=document_id)
        logger.info(
            f"Admin {current_user.email} published document {document.document_type} v{document.version}"
        )
        return LegalDocumentResponse.model_validate(document)
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error publishing document {document_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to publish document",
        )


@router.get(
    "/admin/documents",
    response_model=LegalDocumentListResponse,
)
@require_role("super_admin")
async def list_all_documents(
    document_type: str | None = None,
    status_filter: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LegalDocumentListResponse:
    """List all legal documents with filtering (admin only).

    Args:
        document_type: Filter by type (optional)
        status_filter: Filter by status (optional)

    Returns:
        List of documents

    Raises:
        HTTPException 400: Invalid filter values
        HTTPException 401: Not authenticated
        HTTPException 403: Not super admin
    """
    # Validate filters
    doc_type = None
    doc_status = None

    if document_type:
        try:
            doc_type = LegalDocumentType(document_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid document type",
            )

    if status_filter:
        try:
            doc_status = LegalDocumentStatus(status_filter)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid status",
            )

    try:
        documents = await service.list_documents(db=db, document_type=doc_type, status=doc_status)
        return documents
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list documents",
        )
