"""add legal compliance tables

Revision ID: 007
Revises: 006
Create Date: 2025-10-28

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "007"
down_revision: str | None = "006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create legal compliance tables for GDPR and cookie consent management."""

    # 1. Create legal_documents table
    op.create_table(
        "legal_documents",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "document_type",
            sa.Enum("terms_of_service", "privacy_policy", name="legal_document_type"),
            nullable=False,
        ),
        sa.Column("version", sa.String(20), nullable=False),  # Semantic versioning
        sa.Column("content", sa.Text, nullable=False),
        sa.Column(
            "status",
            sa.Enum("draft", "published", "archived", name="legal_document_status"),
            nullable=False,
            server_default="draft",
        ),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )

    # Create unique constraint for type + version
    op.create_index(
        "idx_legal_documents_type_version",
        "legal_documents",
        ["document_type", "version"],
        unique=True,
    )
    op.create_index(
        "idx_legal_documents_status",
        "legal_documents",
        ["status"],
    )
    op.create_index(
        "idx_legal_documents_published_at",
        "legal_documents",
        [sa.text("published_at DESC")],
    )

    # 2. Create user_consents table
    op.create_table(
        "user_consents",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "tos_document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("legal_documents.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "privacy_document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("legal_documents.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("ip_address", sa.String(45), nullable=False),
        sa.Column("user_agent", sa.String, nullable=True),
        sa.Column(
            "status",
            sa.Enum("active", "withdrawn", "superseded", name="consent_status"),
            nullable=False,
            server_default="active",
        ),
        sa.Column("withdrawn_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )

    # Create indexes for user_consents
    op.create_index(
        "idx_user_consents_user_id",
        "user_consents",
        ["user_id"],
    )
    op.create_index(
        "idx_user_consents_status",
        "user_consents",
        ["status"],
    )
    op.create_index(
        "idx_user_consents_created_at",
        "user_consents",
        [sa.text("created_at DESC")],
    )

    # 3. Create cookie_consents table
    op.create_table(
        "cookie_consents",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=True,  # NULL for anonymous users
        ),
        sa.Column("session_id", sa.String(255), nullable=True),  # For anonymous users
        sa.Column("essential", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("analytics", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("marketing", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("ip_address", sa.String(45), nullable=False),
        sa.Column("user_agent", sa.String, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )

    # Create indexes for cookie_consents
    op.create_index(
        "idx_cookie_consents_user_id",
        "cookie_consents",
        ["user_id"],
    )
    op.create_index(
        "idx_cookie_consents_session_id",
        "cookie_consents",
        ["session_id"],
    )
    op.create_index(
        "idx_cookie_consents_created_at",
        "cookie_consents",
        [sa.text("created_at DESC")],
    )

    # 4. Create consent_audit_logs table (immutable)
    op.create_table(
        "consent_audit_logs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "action",
            sa.Enum(
                "consent_given",
                "consent_withdrawn",
                "consent_updated",
                "data_export_requested",
                "data_deletion_requested",
                "cookie_consent_updated",
                name="consent_action",
            ),
            nullable=False,
        ),
        sa.Column("details", postgresql.JSONB, nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=False),
        sa.Column("user_agent", sa.String, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )

    # Create indexes for consent_audit_logs
    op.create_index(
        "idx_consent_audit_logs_user_id",
        "consent_audit_logs",
        ["user_id"],
    )
    op.create_index(
        "idx_consent_audit_logs_action",
        "consent_audit_logs",
        ["action"],
    )
    op.create_index(
        "idx_consent_audit_logs_created_at",
        "consent_audit_logs",
        [sa.text("created_at DESC")],
    )
    # GIN index for JSONB queries
    op.create_index(
        "idx_consent_audit_logs_details_gin",
        "consent_audit_logs",
        ["details"],
        postgresql_using="gin",
    )

    # 5. Create trigger to prevent modifications to consent_audit_logs
    op.execute(
        """
        CREATE OR REPLACE FUNCTION prevent_audit_modification()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'Audit logs are immutable. Modifications are not allowed.';
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    op.execute(
        """
        CREATE TRIGGER prevent_consent_audit_update
        BEFORE UPDATE OR DELETE ON consent_audit_logs
        FOR EACH ROW
        EXECUTE FUNCTION prevent_audit_modification();
        """
    )


def downgrade() -> None:
    """Drop legal compliance tables and triggers."""

    # Drop trigger and function
    op.execute("DROP TRIGGER IF EXISTS prevent_consent_audit_update ON consent_audit_logs")
    op.execute("DROP FUNCTION IF EXISTS prevent_audit_modification()")

    # Drop consent_audit_logs table
    op.drop_index("idx_consent_audit_logs_details_gin", table_name="consent_audit_logs")
    op.drop_index("idx_consent_audit_logs_created_at", table_name="consent_audit_logs")
    op.drop_index("idx_consent_audit_logs_action", table_name="consent_audit_logs")
    op.drop_index("idx_consent_audit_logs_user_id", table_name="consent_audit_logs")
    op.drop_table("consent_audit_logs")

    # Drop cookie_consents table
    op.drop_index("idx_cookie_consents_created_at", table_name="cookie_consents")
    op.drop_index("idx_cookie_consents_session_id", table_name="cookie_consents")
    op.drop_index("idx_cookie_consents_user_id", table_name="cookie_consents")
    op.drop_table("cookie_consents")

    # Drop user_consents table
    op.drop_index("idx_user_consents_created_at", table_name="user_consents")
    op.drop_index("idx_user_consents_status", table_name="user_consents")
    op.drop_index("idx_user_consents_user_id", table_name="user_consents")
    op.drop_table("user_consents")

    # Drop legal_documents table
    op.drop_index("idx_legal_documents_published_at", table_name="legal_documents")
    op.drop_index("idx_legal_documents_status", table_name="legal_documents")
    op.drop_index("idx_legal_documents_type_version", table_name="legal_documents")
    op.drop_table("legal_documents")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS consent_action")
    op.execute("DROP TYPE IF EXISTS consent_status")
    op.execute("DROP TYPE IF EXISTS legal_document_status")
    op.execute("DROP TYPE IF EXISTS legal_document_type")
