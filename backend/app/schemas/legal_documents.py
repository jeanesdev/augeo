"""Pydantic schemas for legal document endpoints."""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

# ================================
# Request Schemas
# ================================


class LegalDocumentCreateRequest(BaseModel):
    """Request schema for creating a new legal document (admin only)."""

    document_type: Literal["terms_of_service", "privacy_policy"]
    version: str = Field(
        pattern=r"^\d+\.\d+$",
        description="Semantic version (e.g., '1.0', '2.1')",
    )
    content: str = Field(min_length=1, description="Document content in Markdown")

    @field_validator("content")
    @classmethod
    def validate_content_not_empty(cls, v: str) -> str:
        """Ensure content is not just whitespace."""
        if not v.strip():
            raise ValueError("Content cannot be empty or whitespace only")
        return v


class LegalDocumentUpdateRequest(BaseModel):
    """Request schema for updating a draft legal document (admin only)."""

    content: str = Field(min_length=1, description="Updated document content")

    @field_validator("content")
    @classmethod
    def validate_content_not_empty(cls, v: str) -> str:
        """Ensure content is not just whitespace."""
        if not v.strip():
            raise ValueError("Content cannot be empty or whitespace only")
        return v


# ================================
# Response Schemas
# ================================


class LegalDocumentResponse(BaseModel):
    """Response schema for a single legal document."""

    id: uuid.UUID
    document_type: str
    version: str
    content: str
    status: str
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LegalDocumentListResponse(BaseModel):
    """Response schema for list of legal documents."""

    documents: list[LegalDocumentResponse]
    total: int


class LegalDocumentPublicResponse(BaseModel):
    """Public response schema (no sensitive fields)."""

    id: uuid.UUID
    document_type: str
    version: str
    content: str
    published_at: datetime | None

    model_config = {"from_attributes": True}
