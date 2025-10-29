"""Legal document service for Terms of Service and Privacy Policy management.

This service provides methods for creating, updating, publishing, and
retrieving legal documents with version control.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.legal_document import (
    LegalDocument,
    LegalDocumentStatus,
    LegalDocumentType,
)
from app.schemas.legal_documents import (
    LegalDocumentCreateRequest,
    LegalDocumentListResponse,
    LegalDocumentPublicResponse,
    LegalDocumentResponse,
    LegalDocumentUpdateRequest,
)


class LegalDocumentService:
    """Service for legal document management operations."""

    async def create_document(
        self,
        db: AsyncSession,
        request: LegalDocumentCreateRequest,
    ) -> LegalDocument:
        """Create a new legal document (draft status).

        Args:
            db: Database session
            request: Document creation request

        Returns:
            Created document

        Raises:
            ValueError: If document with same type + version already exists
        """
        # Check if document with same type + version exists
        existing = await self.get_by_type_and_version(
            db=db,
            document_type=LegalDocumentType(request.document_type),
            version=request.version,
        )
        if existing:
            raise ValueError(f"Document {request.document_type} v{request.version} already exists")

        # Create document
        document = LegalDocument(
            document_type=LegalDocumentType(request.document_type),
            version=request.version,
            content=request.content,
            status=LegalDocumentStatus.DRAFT,
        )

        db.add(document)
        await db.commit()
        await db.refresh(document)

        return document

    async def update_document(
        self,
        db: AsyncSession,
        document_id: uuid.UUID,
        request: LegalDocumentUpdateRequest,
    ) -> LegalDocument:
        """Update a draft legal document.

        Args:
            db: Database session
            document_id: Document ID
            request: Update request

        Returns:
            Updated document

        Raises:
            ValueError: If document not found or not in draft status
        """
        document = await self.get_by_id(db=db, document_id=document_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")

        if document.status != LegalDocumentStatus.DRAFT:
            raise ValueError(
                f"Cannot update document in {document.status} status. "
                "Only DRAFT documents can be edited."
            )

        # Update content
        document.content = request.content
        document.updated_at = datetime.now(UTC)

        await db.commit()
        await db.refresh(document)

        return document

    async def publish_document(
        self,
        db: AsyncSession,
        document_id: uuid.UUID,
    ) -> LegalDocument:
        """Publish a draft legal document.

        When publishing, archives any existing published document of the same type.

        Args:
            db: Database session
            document_id: Document ID

        Returns:
            Published document

        Raises:
            ValueError: If document not found or not in draft status
        """
        document = await self.get_by_id(db=db, document_id=document_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")

        if document.status != LegalDocumentStatus.DRAFT:
            raise ValueError(
                f"Cannot publish document in {document.status} status. "
                "Only DRAFT documents can be published."
            )

        # Archive any existing published document of the same type
        stmt = select(LegalDocument).where(
            LegalDocument.document_type == document.document_type,
            LegalDocument.status == LegalDocumentStatus.PUBLISHED,
        )
        result = await db.execute(stmt)
        existing_published = result.scalar_one_or_none()

        if existing_published:
            existing_published.status = LegalDocumentStatus.ARCHIVED
            existing_published.updated_at = datetime.now(UTC)

        # Publish the document
        document.status = LegalDocumentStatus.PUBLISHED
        document.published_at = datetime.now(UTC)
        document.updated_at = datetime.now(UTC)

        await db.commit()
        await db.refresh(document)

        return document

    async def get_by_id(
        self,
        db: AsyncSession,
        document_id: uuid.UUID,
    ) -> LegalDocument | None:
        """Get document by ID.

        Args:
            db: Database session
            document_id: Document ID

        Returns:
            Document or None if not found
        """
        stmt = select(LegalDocument).where(LegalDocument.id == document_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_type_and_version(
        self,
        db: AsyncSession,
        document_type: LegalDocumentType,
        version: str,
    ) -> LegalDocument | None:
        """Get document by type and version.

        Args:
            db: Database session
            document_type: Document type
            version: Version string

        Returns:
            Document or None if not found
        """
        stmt = select(LegalDocument).where(
            LegalDocument.document_type == document_type,
            LegalDocument.version == version,
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_current_published(
        self,
        db: AsyncSession,
        document_type: LegalDocumentType,
    ) -> LegalDocument | None:
        """Get currently published document of a type.

        Args:
            db: Database session
            document_type: Document type

        Returns:
            Published document or None if no published document exists
        """
        stmt = (
            select(LegalDocument)
            .where(
                LegalDocument.document_type == document_type,
                LegalDocument.status == LegalDocumentStatus.PUBLISHED,
            )
            .order_by(LegalDocument.published_at.desc())
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_documents(
        self,
        db: AsyncSession,
        document_type: LegalDocumentType | None = None,
        status: LegalDocumentStatus | None = None,
    ) -> LegalDocumentListResponse:
        """List legal documents with optional filtering.

        Args:
            db: Database session
            document_type: Filter by document type (optional)
            status: Filter by status (optional)

        Returns:
            List of documents
        """
        stmt = select(LegalDocument)

        if document_type:
            stmt = stmt.where(LegalDocument.document_type == document_type)

        if status:
            stmt = stmt.where(LegalDocument.status == status)

        stmt = stmt.order_by(
            LegalDocument.document_type,
            LegalDocument.published_at.desc().nullslast(),
            LegalDocument.created_at.desc(),
        )

        result = await db.execute(stmt)
        documents = result.scalars().all()

        return LegalDocumentListResponse(
            documents=[LegalDocumentResponse.model_validate(doc) for doc in documents],
            total=len(documents),
        )

    async def get_all_current_published(
        self,
        db: AsyncSession,
    ) -> list[LegalDocumentPublicResponse]:
        """Get all currently published documents (public endpoint).

        Returns:
            List of published documents (TOS and Privacy Policy)
        """
        tos = await self.get_current_published(
            db=db,
            document_type=LegalDocumentType.TERMS_OF_SERVICE,
        )
        privacy = await self.get_current_published(
            db=db,
            document_type=LegalDocumentType.PRIVACY_POLICY,
        )

        documents = []
        if tos:
            documents.append(LegalDocumentPublicResponse.model_validate(tos))
        if privacy:
            documents.append(LegalDocumentPublicResponse.model_validate(privacy))

        return documents
