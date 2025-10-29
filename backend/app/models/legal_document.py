"""Legal document models for Terms of Service and Privacy Policy."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.consent import UserConsent


class LegalDocumentType(str, enum.Enum):
    """Legal document types."""

    TERMS_OF_SERVICE = "terms_of_service"
    PRIVACY_POLICY = "privacy_policy"


class LegalDocumentStatus(str, enum.Enum):
    """Legal document statuses."""

    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class LegalDocument(Base, UUIDMixin, TimestampMixin):
    """Legal document model for versioned Terms of Service and Privacy Policy.

    Business Rules:
    - Each document has a unique combination of type + version
    - Semantic versioning (major.minor, e.g., "1.0", "1.1", "2.0")
    - Only one document per type can be published at a time
    - Draft documents can be edited; published/archived are immutable
    - published_at is set when status changes to "published"

    GDPR Compliance:
    - All versions retained for 7+ years for audit purposes
    - Versioning enables tracking user consent to specific versions
    """

    __tablename__ = "legal_documents"

    # Document identification
    document_type: Mapped[LegalDocumentType] = mapped_column(
        Enum(
            LegalDocumentType,
            name="legal_document_type",
            native_enum=True,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        index=True,
    )

    version: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    # Content
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # Status tracking
    status: Mapped[LegalDocumentStatus] = mapped_column(
        Enum(
            LegalDocumentStatus,
            name="legal_document_status",
            native_enum=True,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=LegalDocumentStatus.DRAFT,
        server_default="draft",
        index=True,
    )

    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    # Relationships
    tos_consents: Mapped[list["UserConsent"]] = relationship(
        "UserConsent",
        foreign_keys="UserConsent.tos_document_id",
        back_populates="tos_document",
    )

    privacy_consents: Mapped[list["UserConsent"]] = relationship(
        "UserConsent",
        foreign_keys="UserConsent.privacy_document_id",
        back_populates="privacy_document",
    )

    __table_args__ = (
        # Unique constraint on type + version
        CheckConstraint(
            "document_type IN ('terms_of_service', 'privacy_policy')",
            name="valid_document_type",
        ),
        CheckConstraint(
            "status IN ('draft', 'published', 'archived')",
            name="valid_status",
        ),
        CheckConstraint(
            "version ~ '^[0-9]+\\.[0-9]+$'",
            name="valid_semantic_version",
        ),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<LegalDocument {self.document_type} v{self.version} ({self.status})>"
