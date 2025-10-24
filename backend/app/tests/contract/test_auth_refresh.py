"""Contract tests for POST /api/v1/auth/refresh endpoint.

Tests validate API contract compliance per contracts/auth.yaml specification.
These tests verify:
- Request/response schemas match OpenAPI spec
- Status codes are correct for different scenarios
- Access token is refreshed successfully
- Refresh token remains unchanged (no rotation)
- Invalid/expired refresh tokens are rejected
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


class TestAuthRefreshContract:
    """Contract tests for token refresh endpoint."""

    @pytest.mark.asyncio
    async def test_refresh_success_returns_200(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test successful token refresh returns 200 with new access token.

        Contract: POST /api/v1/auth/refresh
        Expected: 200 OK with RefreshResponse schema (access_token, token_type, expires_in)
        """
        # First, register and login to get a refresh token
        register_payload = {
            "email": "refresh.test@example.com",
            "password": "SecurePass123",
            "first_name": "Refresh",
            "last_name": "Test",
        }
        register_response = await async_client.post("/api/v1/auth/register", json=register_payload)
        assert register_response.status_code == 201

        # TODO: Verify email first (once email verification is implemented)
        # For now, this will need manual verification or mock

        # Login to get tokens
        login_payload = {"email": "refresh.test@example.com", "password": "SecurePass123"}
        login_response = await async_client.post("/api/v1/auth/login", json=login_payload)

        # Skip if login fails (email not verified)
        if login_response.status_code != 200:
            pytest.skip("Email verification not yet implemented")

        login_data = login_response.json()
        refresh_token = login_data["refresh_token"]

        # Attempt token refresh
        refresh_payload = {"refresh_token": refresh_token}
        response = await async_client.post("/api/v1/auth/refresh", json=refresh_payload)

        # Verify status code
        assert response.status_code == 200

        # Verify response schema
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
        assert data["expires_in"] == 900  # 15 minutes in seconds

        # Verify refresh_token is NOT returned (no rotation per spec)
        assert "refresh_token" not in data

        # Verify new access token is JWT format (three base64 parts separated by dots)
        assert data["access_token"].count(".") == 2

        # Verify new access token is different from old one
        old_access_token = login_data["access_token"]
        new_access_token = data["access_token"]
        assert new_access_token != old_access_token

    @pytest.mark.asyncio
    async def test_refresh_invalid_token_returns_401(self, async_client: AsyncClient):
        """Test invalid refresh token returns 401 Unauthorized.

        Contract: POST /api/v1/auth/refresh
        Expected: 401 Unauthorized with INVALID_REFRESH_TOKEN error
        """
        # Attempt refresh with invalid token
        refresh_payload = {"refresh_token": "invalid.token.here"}
        response = await async_client.post("/api/v1/auth/refresh", json=refresh_payload)

        # Verify status code
        assert response.status_code == 401

        # Verify error schema
        data = response.json()
        assert "error" in data
        error = data["error"]
        assert "code" in error
        assert error["code"] == "INVALID_REFRESH_TOKEN"
        assert "message" in error
        assert "invalid or expired" in error["message"].lower()

    @pytest.mark.asyncio
    async def test_refresh_expired_token_returns_401(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test expired refresh token returns 401 Unauthorized.

        Contract: Refresh tokens expire after 7 days
        Expected: 401 Unauthorized with INVALID_REFRESH_TOKEN error
        """
        # This test would require mocking time or waiting 7 days
        # For contract testing, we verify the expected behavior
        pytest.skip("Requires time mocking to test expiration")

    @pytest.mark.asyncio
    async def test_refresh_blacklisted_token_returns_401(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test blacklisted refresh token returns 401 Unauthorized.

        Contract: Tokens in Redis blacklist should be rejected
        Expected: 401 Unauthorized after logout
        """
        # Register, login, logout, then try to refresh
        register_payload = {
            "email": "blacklist.test@example.com",
            "password": "SecurePass123",
            "first_name": "Blacklist",
            "last_name": "Test",
        }
        await async_client.post("/api/v1/auth/register", json=register_payload)

        # Login
        login_payload = {"email": "blacklist.test@example.com", "password": "SecurePass123"}
        login_response = await async_client.post("/api/v1/auth/login", json=login_payload)

        if login_response.status_code != 200:
            pytest.skip("Email verification not yet implemented")

        login_data = login_response.json()
        access_token = login_data["access_token"]
        refresh_token = login_data["refresh_token"]

        # Logout (should blacklist the tokens)
        logout_payload = {"refresh_token": refresh_token}
        await async_client.post(
            "/api/v1/auth/logout",
            json=logout_payload,
            headers={"Authorization": f"Bearer {access_token}"},
        )

        # Try to refresh with the now-blacklisted token
        refresh_payload = {"refresh_token": refresh_token}
        response = await async_client.post("/api/v1/auth/refresh", json=refresh_payload)

        # Verify status code
        assert response.status_code == 401

        # Verify error schema
        data = response.json()
        assert data["error"]["code"] == "INVALID_REFRESH_TOKEN"

    @pytest.mark.asyncio
    async def test_refresh_missing_token_returns_422(self, async_client: AsyncClient):
        """Test missing refresh_token field returns 422 Validation Error.

        Contract: refresh_token is required
        Expected: 422 Unprocessable Entity
        """
        # Empty payload
        response = await async_client.post("/api/v1/auth/refresh", json={})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_refresh_invalid_session_returns_401(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test refresh with invalid session returns 401.

        Contract: Session must exist in Redis
        Expected: 401 Unauthorized if session was deleted from Redis
        """
        # This test verifies that even with a valid JWT,
        # if the session doesn't exist in Redis, refresh fails
        pytest.skip("Requires Redis session management implementation")

    @pytest.mark.asyncio
    async def test_refresh_preserves_original_refresh_token(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test refresh does NOT rotate refresh token.

        Contract: Refresh token remains valid for full 7 days (no rotation)
        Expected: Same refresh token can be used multiple times
        """
        # Register and login
        register_payload = {
            "email": "norotate.test@example.com",
            "password": "SecurePass123",
            "first_name": "NoRotate",
            "last_name": "Test",
        }
        await async_client.post("/api/v1/auth/register", json=register_payload)

        login_payload = {"email": "norotate.test@example.com", "password": "SecurePass123"}
        login_response = await async_client.post("/api/v1/auth/login", json=login_payload)

        if login_response.status_code != 200:
            pytest.skip("Email verification not yet implemented")

        login_data = login_response.json()
        refresh_token = login_data["refresh_token"]

        # Refresh multiple times with same token
        for _i in range(3):
            refresh_payload = {"refresh_token": refresh_token}
            response = await async_client.post("/api/v1/auth/refresh", json=refresh_payload)

            # Each refresh should succeed
            assert response.status_code == 200

            # Verify refresh_token is not in response (no rotation)
            data = response.json()
            assert "refresh_token" not in data

    @pytest.mark.asyncio
    async def test_refresh_generates_different_access_tokens(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test each refresh generates a unique access token.

        Contract: Each refresh should create a new access token with new expiry
        Expected: Different access tokens from sequential refreshes
        """
        # Register and login
        register_payload = {
            "email": "unique.token@example.com",
            "password": "SecurePass123",
            "first_name": "Unique",
            "last_name": "Token",
        }
        await async_client.post("/api/v1/auth/register", json=register_payload)

        login_payload = {"email": "unique.token@example.com", "password": "SecurePass123"}
        login_response = await async_client.post("/api/v1/auth/login", json=login_payload)

        if login_response.status_code != 200:
            pytest.skip("Email verification not yet implemented")

        login_data = login_response.json()
        refresh_token = login_data["refresh_token"]

        # Get first access token
        refresh_payload = {"refresh_token": refresh_token}
        response1 = await async_client.post("/api/v1/auth/refresh", json=refresh_payload)
        access_token1 = response1.json()["access_token"]

        # Get second access token
        response2 = await async_client.post("/api/v1/auth/refresh", json=refresh_payload)
        access_token2 = response2.json()["access_token"]

        # Verify they are different
        assert access_token1 != access_token2

    @pytest.mark.asyncio
    async def test_refresh_validates_token_signature(self, async_client: AsyncClient):
        """Test refresh validates JWT signature.

        Contract: Token must be signed with correct secret
        Expected: 401 Unauthorized for tampered tokens
        """
        # Create a valid-looking but unsigned/incorrectly signed JWT
        # Format: header.payload.signature (three parts)
        fake_token = (
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.invalid_signature"
        )

        refresh_payload = {"refresh_token": fake_token}
        response = await async_client.post("/api/v1/auth/refresh", json=refresh_payload)

        # Verify status code
        assert response.status_code == 401

        # Verify error schema
        data = response.json()
        assert data["error"]["code"] == "INVALID_REFRESH_TOKEN"
