"""create sessions table

Revision ID: 003
Revises: 002
Create Date: 2025-10-20

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: str | None = "002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create sessions table for audit trail of user sessions.

    This table serves as a write-only audit log. Active session validation
    uses Redis as the source of truth.
    """
    op.create_table(
        "sessions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        # Foreign Keys
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # Session Details
        sa.Column("refresh_token_jti", sa.String(255), unique=True, nullable=False),
        sa.Column("device_info", sa.String(500), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=False),  # IPv6 max length
        sa.Column("user_agent", sa.String, nullable=True),
        # Lifecycle timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        # Check constraints
        sa.CheckConstraint("expires_at > created_at", name="expires_after_creation"),
    )

    # Create indexes
    op.create_index("idx_sessions_user_id", "sessions", ["user_id"])
    op.create_index("idx_sessions_jti", "sessions", ["refresh_token_jti"])
    op.create_index(
        "idx_sessions_created_at",
        "sessions",
        [sa.text("created_at DESC")],
    )
    op.create_index(
        "idx_sessions_active",
        "sessions",
        ["user_id", "revoked_at"],
        postgresql_where=sa.text("revoked_at IS NULL"),
    )


def downgrade() -> None:
    """Drop sessions table and all indexes."""
    op.drop_index("idx_sessions_active", table_name="sessions")
    op.drop_index("idx_sessions_created_at", table_name="sessions")
    op.drop_index("idx_sessions_jti", table_name="sessions")
    op.drop_index("idx_sessions_user_id", table_name="sessions")
    op.drop_table("sessions")
