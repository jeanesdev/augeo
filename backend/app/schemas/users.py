"""Pydantic schemas for user management endpoints."""
import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator

# ================================
# Request Schemas
# ================================


class UserCreateRequest(BaseModel):
    """Request schema for creating a new user (admin only)."""

    email: EmailStr
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    phone: str | None = Field(None, max_length=20)
    role: Literal["super_admin", "npo_admin", "event_coordinator", "staff", "donor"]
    npo_id: uuid.UUID | None = None

    @field_validator("email")
    @classmethod
    def email_must_be_lowercase(cls, v: str) -> str:
        """Ensure email is lowercase."""
        return v.lower()


class RoleUpdateRequest(BaseModel):
    """Request schema for updating a user's role."""

    role: Literal["super_admin", "npo_admin", "event_coordinator", "staff", "donor"]
    npo_id: uuid.UUID | None = None


class UserUpdateRequest(BaseModel):
    """Request schema for updating user profile."""

    first_name: str | None = Field(None, min_length=1, max_length=100)
    last_name: str | None = Field(None, min_length=1, max_length=100)
    phone: str | None = Field(None, max_length=20)


# ================================
# Response Schemas
# ================================


class UserPublicWithRole(BaseModel):
    """Public user information with role details."""

    id: uuid.UUID
    email: str
    first_name: str
    last_name: str
    phone: str | None
    role: str
    npo_id: uuid.UUID | None
    email_verified: bool
    is_active: bool
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    """Paginated response for user list."""

    items: list[UserPublicWithRole]
    total: int
    page: int
    per_page: int
    total_pages: int


class UserActivateRequest(BaseModel):
    """Request schema for activating a user account."""

    is_active: bool
