"""Consent models for GDPR compliance."""

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.legal_document import LegalDocument
    from app.models.user import User


class ConsentStatus(str, enum.Enum):
    """User consent statuses."""

    ACTIVE = "active"
    WITHDRAWN = "withdrawn"
    SUPERSEDED = "superseded"


class ConsentAction(str, enum.Enum):
    """Consent audit log action types."""

    CONSENT_GIVEN = "consent_given"
    CONSENT_WITHDRAWN = "consent_withdrawn"
    CONSENT_UPDATED = "consent_updated"
    DATA_EXPORT_REQUESTED = "data_export_requested"
    DATA_DELETION_REQUESTED = "data_deletion_requested"
    COOKIE_CONSENT_UPDATED = "cookie_consent_updated"


class UserConsent(Base, UUIDMixin, TimestampMixin):
    """User consent model for tracking agreement to legal documents.

    Business Rules:
    - Each user can have only one ACTIVE consent at a time
    - When user accepts new documents, old consent is marked SUPERSEDED
    - Withdrawal sets status to WITHDRAWN and sets withdrawn_at
    - IP address and user agent tracked for audit compliance

    GDPR Compliance:
    - Tracks specific document versions user consented to
    - Immutable audit trail via consent_audit_logs
    - 7-year retention for compliance
    """

    __tablename__ = "user_consents"

    # Foreign keys
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    tos_document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("legal_documents.id", ondelete="RESTRICT"),
        nullable=False,
    )

    privacy_document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("legal_documents.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # Audit context
    ip_address: Mapped[str] = mapped_column(
        String(45),  # IPv6 max length
        nullable=False,
    )

    user_agent: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    # Status tracking
    status: Mapped[ConsentStatus] = mapped_column(
        Enum(
            ConsentStatus,
            name="consent_status",
            native_enum=True,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=ConsentStatus.ACTIVE,
        server_default="active",
        index=True,
    )

    withdrawn_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="consents",
    )

    tos_document: Mapped["LegalDocument"] = relationship(
        "LegalDocument",
        foreign_keys=[tos_document_id],
        back_populates="tos_consents",
    )

    privacy_document: Mapped["LegalDocument"] = relationship(
        "LegalDocument",
        foreign_keys=[privacy_document_id],
        back_populates="privacy_consents",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<UserConsent user_id={self.user_id} status={self.status}>"


class CookieConsent(Base, UUIDMixin, TimestampMixin):
    """Cookie consent model for tracking user preferences.

    Business Rules:
    - Essential cookies always enabled (cannot be disabled)
    - Anonymous users tracked by session_id (user_id is NULL)
    - Authenticated users tracked by user_id (session_id optional)
    - Latest preference always used (no versioning, just updates)

    EU Cookie Law Compliance:
    - Explicit consent required for non-essential cookies
    - Granular categories: Essential, Analytics, Marketing
    - IP address and user agent tracked for audit
    """

    __tablename__ = "cookie_consents"

    # Identity (user_id XOR session_id)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    session_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )

    # Cookie categories
    essential: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    analytics: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    marketing: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    # Audit context
    ip_address: Mapped[str] = mapped_column(
        String(45),
        nullable=False,
    )

    user_agent: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    # Relationships
    user: Mapped["User | None"] = relationship(
        "User",
        back_populates="cookie_consents",
    )

    def __repr__(self) -> str:
        """String representation."""
        identifier = f"user_id={self.user_id}" if self.user_id else f"session={self.session_id}"
        return f"<CookieConsent {identifier} analytics={self.analytics} marketing={self.marketing}>"


class ConsentAuditLog(Base, UUIDMixin):
    """Immutable audit log for all consent-related actions.

    Business Rules:
    - Write-only (INSERT only, no UPDATE/DELETE)
    - PostgreSQL trigger prevents modifications
    - All consent actions logged with full context

    GDPR Compliance:
    - Immutable audit trail for 7+ years
    - Tracks all data subject rights requests
    - IP address and timestamp for legal compliance
    """

    __tablename__ = "consent_audit_logs"

    # Foreign key
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Action tracking
    action: Mapped[ConsentAction] = mapped_column(
        Enum(
            ConsentAction,
            name="consent_action",
            native_enum=True,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        index=True,
    )

    details: Mapped[dict[str, object] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Audit context
    ip_address: Mapped[str] = mapped_column(
        String(45),
        nullable=False,
    )

    user_agent: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    # Timestamp (no updated_at for immutable logs)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="NOW()",
        index=True,
    )

    # Relationships
    user: Mapped["User | None"] = relationship(
        "User",
        back_populates="consent_audit_logs",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<ConsentAuditLog action={self.action} user_id={self.user_id}>"
