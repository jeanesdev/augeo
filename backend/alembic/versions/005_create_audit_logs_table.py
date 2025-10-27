"""create audit_logs table

Revision ID: 005
Revises: 004
Create Date: 2025-10-24

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "005"
down_revision: str | None = "004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create audit_logs table for security auditing.

    This table is immutable (write-only) and logs all authentication
    and authorization events.
    """
    op.create_table(
        "audit_logs",
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
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,  # NULL for failed login attempts or anonymous events
        ),
        # Event Details
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("resource_type", sa.String(50), nullable=True),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=True),
        # Request Context
        sa.Column("ip_address", sa.String(45), nullable=False),  # IPv6 max length
        sa.Column("user_agent", sa.String, nullable=True),
        # Metadata (JSONB for flexibility)
        sa.Column("metadata", postgresql.JSONB, nullable=True),
        # Timestamp (immutable, indexed)
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )

    # Create indexes
    op.create_index("idx_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("idx_audit_logs_action", "audit_logs", ["action"])
    op.create_index(
        "idx_audit_logs_created_at",
        "audit_logs",
        [sa.text("created_at DESC")],
    )
    op.create_index("idx_audit_logs_ip_address", "audit_logs", ["ip_address"])
    # GIN index for JSONB queries
    op.create_index(
        "idx_audit_logs_metadata_gin",
        "audit_logs",
        ["metadata"],
        postgresql_using="gin",
    )


def downgrade() -> None:
    """Drop audit_logs table and all indexes."""
    op.drop_index("idx_audit_logs_metadata_gin", table_name="audit_logs")
    op.drop_index("idx_audit_logs_ip_address", table_name="audit_logs")
    op.drop_index("idx_audit_logs_created_at", table_name="audit_logs")
    op.drop_index("idx_audit_logs_action", table_name="audit_logs")
    op.drop_index("idx_audit_logs_user_id", table_name="audit_logs")
    op.drop_table("audit_logs")
