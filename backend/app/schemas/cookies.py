"""Pydantic schemas for cookie consent endpoints."""

import uuid
from datetime import datetime

from pydantic import BaseModel

# ================================
# Request Schemas
# ================================


class CookieConsentRequest(BaseModel):
    """Request schema for setting cookie preferences."""

    analytics: bool = False
    marketing: bool = False
    # Note: essential is always True and not configurable


class CookieConsentUpdateRequest(BaseModel):
    """Request schema for updating cookie preferences."""

    analytics: bool
    marketing: bool


# ================================
# Response Schemas
# ================================


class CookieConsentResponse(BaseModel):
    """Response schema for cookie consent."""

    id: uuid.UUID
    user_id: uuid.UUID | None
    session_id: str | None
    essential: bool
    analytics: bool
    marketing: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CookieConsentStatusResponse(BaseModel):
    """Response schema for cookie consent status (public)."""

    essential: bool
    analytics: bool
    marketing: bool
    has_consent: bool  # True if user has set preferences
