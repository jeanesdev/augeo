"""Pydantic schemas for consent management endpoints."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

# ================================
# Request Schemas
# ================================


class ConsentAcceptRequest(BaseModel):
    """Request schema for accepting legal documents."""

    tos_document_id: uuid.UUID = Field(description="Terms of Service document ID")
    privacy_document_id: uuid.UUID = Field(description="Privacy Policy document ID")


class DataExportRequest(BaseModel):
    """Request schema for GDPR data export."""

    email: str | None = Field(
        None,
        description="Email to send export to (defaults to user's email)",
    )


class DataDeletionRequest(BaseModel):
    """Request schema for GDPR data deletion."""

    confirmation: bool = Field(description="Must be true to confirm deletion request")

    def model_post_init(self, __context: object) -> None:
        """Validate confirmation after init."""
        if not self.confirmation:
            raise ValueError("Confirmation must be true to proceed with deletion")


# ================================
# Response Schemas
# ================================


class ConsentResponse(BaseModel):
    """Response schema for a single consent record."""

    id: uuid.UUID
    user_id: uuid.UUID
    tos_document_id: uuid.UUID
    privacy_document_id: uuid.UUID
    status: str
    ip_address: str
    user_agent: str | None
    withdrawn_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConsentStatusResponse(BaseModel):
    """Response schema for user's current consent status."""

    has_active_consent: bool
    current_tos_version: str | None
    current_privacy_version: str | None
    latest_tos_version: str
    latest_privacy_version: str
    consent_required: bool  # True if documents updated and user needs to re-consent


class ConsentHistoryResponse(BaseModel):
    """Response schema for consent history with pagination."""

    consents: list[ConsentResponse]
    total: int
    page: int
    per_page: int


class ConsentAuditLogResponse(BaseModel):
    """Response schema for consent audit log entry."""

    id: uuid.UUID
    user_id: uuid.UUID | None
    action: str
    details: dict[str, object] | None
    ip_address: str
    user_agent: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
