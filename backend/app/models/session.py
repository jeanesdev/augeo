"""Session model for audit trail of user sessions."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User


class Session(Base, UUIDMixin):
    """Session model for immutable audit trail of user sessions.

    This table serves as a write-only audit log for compliance and security
    investigations. Active session validation uses Redis as the source of truth.

    Business Rules:
    - Immutable: No UPDATE or DELETE operations (only INSERT and soft revoke)
    - Redis is source of truth for active sessions (this is audit trail only)
    - expires_at set to 7 days from created_at
    - Logout sets revoked_at but doesn't delete record
    - Each session tracks refresh token JTI for Redis lookup
    """

    __tablename__ = "sessions"

    # Foreign Keys
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Session Details
    refresh_token_jti: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    device_info: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)  # IPv6 max length
    user_agent: Mapped[str | None] = mapped_column(String, nullable=True)

    # Lifecycle timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="NOW()",
        index=True,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="sessions")

    # Check constraints
    __table_args__ = (CheckConstraint("expires_at > created_at", name="expires_after_creation"),)

    def __repr__(self) -> str:
        """Return string representation of session."""
        return (
            f"<Session(id={self.id}, user_id={self.user_id}, "
            f"jti={self.refresh_token_jti[:8]}..., revoked={self.revoked_at is not None})>"
        )
