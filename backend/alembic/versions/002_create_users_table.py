"""create users table

Revision ID: 002
Revises: 001
Create Date: 2025-10-20

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create users table with foreign key to roles."""
    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        # Identity
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        # Profile
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("phone", sa.String(20), nullable=True),
        # Authentication
        sa.Column("email_verified", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="false"),
        # Role & Scope
        sa.Column(
            "role_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("roles.id"),
            nullable=False,
        ),
        sa.Column(
            "npo_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),  # FK to organizations table (will be added when that table exists)
        # Audit timestamps
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
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        # Check constraints
        sa.CheckConstraint("email = LOWER(email)", name="email_lowercase"),
        sa.CheckConstraint("LENGTH(password_hash) > 0", name="password_not_empty"),
    )

    # Create indexes
    op.create_index("idx_users_email", "users", ["email"])
    op.create_index("idx_users_role_id", "users", ["role_id"])
    op.create_index(
        "idx_users_npo_id",
        "users",
        ["npo_id"],
        postgresql_where=sa.text("npo_id IS NOT NULL"),
    )
    op.create_index(
        "idx_users_email_verified",
        "users",
        ["email_verified"],
        postgresql_where=sa.text("email_verified = false"),
    )
    op.create_index(
        "idx_users_created_at",
        "users",
        [sa.text("created_at DESC")],
    )


def downgrade() -> None:
    """Drop users table and all indexes."""
    op.drop_index("idx_users_created_at", table_name="users")
    op.drop_index("idx_users_email_verified", table_name="users")
    op.drop_index("idx_users_npo_id", table_name="users")
    op.drop_index("idx_users_role_id", table_name="users")
    op.drop_index("idx_users_email", table_name="users")
    op.drop_table("users")
