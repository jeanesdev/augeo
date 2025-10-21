"""Unit tests for security utilities (Phase 2 smoke tests)."""

import pytest

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_verification_token,
    hash_password,
    verify_password,
)


@pytest.mark.unit
class TestPasswordHashing:
    """Test password hashing and verification."""

    def test_hash_password_returns_string(self) -> None:
        """Test that hash_password returns a string."""
        password = "SecurePassword123!"
        hashed = hash_password(password)
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_verify_password_success(self) -> None:
        """Test password verification with correct password."""
        password = "SecurePassword123!"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_failure(self) -> None:
        """Test password verification with incorrect password."""
        password = "SecurePassword123!"
        hashed = hash_password(password)
        assert verify_password("WrongPassword!", hashed) is False

    def test_hash_password_different_hashes(self) -> None:
        """Test that same password produces different hashes (due to salt)."""
        password = "SecurePassword123!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        assert hash1 != hash2  # Different salts
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)

    def test_hash_long_password(self) -> None:
        """Test password hashing with long password (72+ bytes)."""
        # bcrypt has 72-byte limit
        long_password = "A" * 100
        hashed = hash_password(long_password)
        assert verify_password(long_password, hashed)

    def test_hash_unicode_password(self) -> None:
        """Test password hashing with unicode characters."""
        password = "Pāsswörd123!🔒"
        hashed = hash_password(password)
        assert verify_password(password, hashed)


@pytest.mark.unit
class TestJWTTokens:
    """Test JWT token creation and verification."""

    def test_create_access_token(self) -> None:
        """Test creating an access token."""
        data = {"sub": "user123", "email": "test@example.com"}
        token = create_access_token(data)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_access_token(self) -> None:
        """Test decoding an access token."""
        data = {"sub": "user123", "email": "test@example.com"}
        token = create_access_token(data)
        decoded = decode_token(token)
        assert decoded["sub"] == "user123"
        assert decoded["email"] == "test@example.com"
        assert "exp" in decoded  # Expiration should be added

    def test_create_refresh_token(self) -> None:
        """Test creating a refresh token."""
        data = {"sub": "user123"}
        token = create_refresh_token(data)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_refresh_token(self) -> None:
        """Test decoding a refresh token."""
        data = {"sub": "user123"}
        token = create_refresh_token(data)
        decoded = decode_token(token)
        assert decoded["sub"] == "user123"
        assert "exp" in decoded

    def test_decode_invalid_token(self) -> None:
        """Test decoding an invalid token raises error."""
        from jose import JWTError

        with pytest.raises(JWTError):
            decode_token("invalid.token.here")

    def test_token_with_custom_expiry(self) -> None:
        """Test creating token with custom expiry."""
        from datetime import timedelta

        data = {"sub": "user123"}
        token = create_access_token(data, expires_delta=timedelta(seconds=60))
        decoded = decode_token(token)
        assert decoded["sub"] == "user123"


@pytest.mark.unit
class TestVerificationToken:
    """Test verification token generation."""

    def test_generate_verification_token(self) -> None:
        """Test generating a verification token."""
        token = generate_verification_token()
        assert isinstance(token, str)
        assert len(token) > 0

    def test_verification_tokens_unique(self) -> None:
        """Test that verification tokens are unique."""
        token1 = generate_verification_token()
        token2 = generate_verification_token()
        assert token1 != token2

    def test_verification_token_length(self) -> None:
        """Test verification token has reasonable length."""
        token = generate_verification_token()
        # URL-safe base64 encoding of 32 bytes should be ~43 chars
        assert len(token) > 40
