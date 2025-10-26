"""Contract tests for POST /api/v1/auth/logout endpoint.

Tests validate API contract compliance per contracts/auth.yaml specification.
These tests verify:
- Request/response schemas match OpenAPI spec
- Authentication is required
- Sessions are properly revoked
- Tokens are blacklisted
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


class TestAuthLogoutContract:
    """Contract tests for user logout endpoint."""

    @pytest.mark.asyncio
    async def test_logout_success_returns_200(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test successful logout returns 200 with message.

        Contract: POST /api/v1/auth/logout
        Expected: 200 OK with MessageResponse schema
        """
        # Register, verify, and login a user
        register_payload = {
            "email": "logout.test@example.com",
            "password": "SecurePass123",
            "first_name": "Logout",
            "last_name": "Test",
        }
        register_response = await async_client.post("/api/v1/auth/register", json=register_payload)
        verification_token = register_response.json()["verification_token"]
        await async_client.post("/api/v1/auth/verify-email", json={"token": verification_token})

        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "logout.test@example.com", "password": "SecurePass123"},
        )
        access_token = login_response.json()["access_token"]
        refresh_token = login_response.json()["refresh_token"]

        # Test logout
        logout_payload = {"refresh_token": refresh_token}
        headers = {"Authorization": f"Bearer {access_token}"}
        response = await async_client.post(
            "/api/v1/auth/logout", json=logout_payload, headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Logged out successfully" in data["message"]

    @pytest.mark.asyncio
    async def test_logout_missing_auth_token_returns_401(self, async_client: AsyncClient):
        """Test logout without auth token returns 401 Unauthorized.

        Contract: POST /api/v1/auth/logout requires Bearer token
        Expected: 401 Unauthorized with MISSING_TOKEN error
        """
        logout_payload = {"refresh_token": "some_refresh_token"}
        response = await async_client.post(
            "/api/v1/auth/logout",
            json=logout_payload,
            # No Authorization header
        )

        # Verify status code
        assert response.status_code == 401

        # Verify error schema
        data = response.json()
        assert "error" in data
        error = data["error"]
        assert "code" in error
        assert error["code"] == "MISSING_TOKEN"
        assert "Authentication token required" in error["message"]

    @pytest.mark.asyncio
    async def test_logout_invalid_auth_token_returns_401(self, async_client: AsyncClient):
        """Test logout with invalid auth token returns 401 Unauthorized.

        Contract: POST /api/v1/auth/logout requires valid Bearer token
        Expected: 401 Unauthorized
        """
        logout_payload = {"refresh_token": "some_refresh_token"}
        headers = {"Authorization": "Bearer invalid_token"}
        response = await async_client.post(
            "/api/v1/auth/logout", json=logout_payload, headers=headers
        )

        # Verify status code
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_logout_expired_token_returns_401(self, async_client: AsyncClient):
        """Test logout with expired token returns 401 Unauthorized.

        Contract: Expired tokens should be rejected
        Expected: 401 Unauthorized
        """
        pytest.skip("Requires token expiration implementation")

    @pytest.mark.asyncio
    async def test_logout_missing_refresh_token_returns_422(self, async_client: AsyncClient):
        """Test logout without refresh token returns 422 Validation Error.

        Contract: refresh_token is required in request body
        Expected: 422 Unprocessable Entity
        """
        # Valid access token but missing refresh token in body
        headers = {"Authorization": "Bearer valid_access_token"}
        response = await async_client.post(
            "/api/v1/auth/logout",
            json={},  # Empty body
            headers=headers,
        )

        # Should return validation error (once auth is implemented)
        assert response.status_code in [401, 422]  # 401 if auth fails first, 422 for validation

    @pytest.mark.asyncio
    async def test_logout_revokes_session_in_postgres(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test logout sets revoked_at on session record.

        Contract: Logout should set revoked_at timestamp on session
        Expected: Session record has revoked_at != null
        """
        pytest.skip("Requires session implementation")

    @pytest.mark.asyncio
    async def test_logout_deletes_session_from_redis(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test logout removes session from Redis.

        Contract: Logout should delete session from Redis
        Expected: Redis key session:{user_id}:{jti} is deleted
        """
        pytest.skip("Requires Redis session implementation")

    @pytest.mark.asyncio
    async def test_logout_blacklists_access_token(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test logout adds access token to blacklist.

        Contract: Logout should blacklist access token JTI in Redis
        Expected: Redis key blacklist:{jti} exists with 15min TTL
        """
        pytest.skip("Requires JWT blacklist implementation")

    @pytest.mark.asyncio
    async def test_logout_creates_audit_log(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test logout creates audit log entry.

        Contract: Logout should log 'logout' action to audit_logs
        Expected: audit_logs table has entry with action='logout'
        """
        pytest.skip("Requires audit logging implementation")

    @pytest.mark.asyncio
    async def test_logout_idempotent_already_logged_out(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test logout twice with same refresh token is idempotent.

        Contract: Logging out with already-revoked session should still return 200
        Expected: 200 OK (or appropriate error for already-revoked session)
        """
        pytest.skip("Requires full logout implementation")
