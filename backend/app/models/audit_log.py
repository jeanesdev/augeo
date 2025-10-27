"""AuditLog model for security auditing."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User


class AuditLog(Base, UUIDMixin):
    """Immutable log of all authentication and authorization events.

    Logged Actions:
    - login: Successful login
    - logout: User logout
    - failed_login: Failed login attempt
    - password_reset_requested: Password reset email sent
    - password_reset_completed: Password successfully reset
    - password_changed: Password changed via settings
    - role_changed: User role modified by admin
    - email_verified: Email verification completed
    - session_revoked: Session manually revoked
    - account_created: New user registration
    - account_deactivated: Account deactivated
    - account_reactivated: Account reactivated
    - user_created: User created by admin
    - user_updated: User updated by admin
    - user_deleted: User deleted by admin
    - token_refreshed: Access token refreshed
    - unauthorized_access_attempt: Attempt to access unauthorized resource

    Business Rules:
    - Immutable: No UPDATE or DELETE operations
    - Retention: 90 days in hot storage, archive to Azure Blob after 90 days
    - user_id is NULL for failed login attempts or anonymous events
    """

    __tablename__ = "audit_logs"

    # Foreign Keys
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Event Details
    action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    resource_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    resource_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    # Request Context
    ip_address: Mapped[str] = mapped_column(
        String(45),
        nullable=False,
        index=True,
    )
    user_agent: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    # Metadata (JSONB for flexibility)
    # Note: Using 'event_metadata' in Python because 'metadata' is reserved by SQLAlchemy
    event_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata",  # Column name in database
        JSONB,
        nullable=True,
    )

    # Timestamp (immutable, indexed)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="audit_logs")
