"""Pydantic schemas for authentication endpoints."""

import re
import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    """Schema for user registration request.

    Business Rules:
    - Email must be unique (case-insensitive, normalized to lowercase)
    - Password must be 8-100 chars with at least 1 letter and 1 number
    - First/last names required (1-100 chars)
    - Phone optional (max 20 chars)
    - Organization name and address optional (for business/organization users)
    """

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: str | None = Field(None, max_length=20)
    organization_name: str | None = Field(None, max_length=255)
    organization_address: str | None = None

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password contains at least one letter and one number."""
        if not re.search(r"[A-Za-z]", v):
            raise ValueError("Password must contain at least one letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one number")
        return v

    @field_validator("email")
    @classmethod
    def lowercase_email(cls, v: str) -> str:
        """Normalize email to lowercase for case-insensitive storage."""
        return v.lower()


class UserPublic(BaseModel):
    """Public user information (safe to return in API responses).

    This schema excludes sensitive fields like password_hash.
    """

    id: uuid.UUID
    email: EmailStr
    first_name: str
    last_name: str
    phone: str | None = None
    organization_name: str | None = None
    organization_address: str | None = None
    email_verified: bool
    is_active: bool
    role: str  # Role name (e.g., "donor", "npo_admin")
    npo_id: uuid.UUID | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    """Schema for login request."""

    email: EmailStr
    password: str

    @field_validator("email")
    @classmethod
    def lowercase_email(cls, v: str) -> str:
        """Normalize email to lowercase for lookup."""
        return v.lower()


class LoginResponse(BaseModel):
    """Schema for successful login response.

    Returns JWT tokens and user information.
    """

    access_token: str = Field(..., description="JWT access token (15-minute expiry)")
    refresh_token: str = Field(..., description="JWT refresh token (7-day expiry)")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiry in seconds (900)")
    user: UserPublic


class RefreshRequest(BaseModel):
    """Schema for token refresh request."""

    refresh_token: str = Field(..., description="Valid refresh token")


class RefreshResponse(BaseModel):
    """Schema for token refresh response.

    Returns new access token (refresh token unchanged).
    """

    access_token: str = Field(..., description="New JWT access token (15-minute expiry)")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiry in seconds (900)")


class LogoutRequest(BaseModel):
    """Schema for logout request."""

    refresh_token: str = Field(..., description="Refresh token to revoke")


class MessageResponse(BaseModel):
    """Generic message response schema."""

    message: str


class UserRegisterResponse(BaseModel):
    """Schema for user registration response."""

    user: UserPublic
    message: str
    verification_token: str | None = Field(
        None, description="Verification token (only included in development/test environments)"
    )


class EmailVerifyRequest(BaseModel):
    """Schema for email verification request.

    Business Rules:
    - Token is required (generated during registration)
    - Token must be valid and not expired (24h TTL)
    - User must not already be verified
    """

    token: str = Field(..., description="Email verification token from registration email")


class EmailVerifyResponse(BaseModel):
    """Schema for email verification response."""

    message: str = Field(..., description="Success or error message")


class EmailResendRequest(BaseModel):
    """Schema for resend verification email request.

    Business Rules:
    - Email must match an existing user
    - User must not already be verified
    - Generates new token, invalidates old one
    """

    email: EmailStr = Field(..., description="Email address to resend verification to")

    @field_validator("email")
    @classmethod
    def lowercase_email(cls, v: str) -> str:
        """Normalize email to lowercase for consistency."""
        return v.lower()
