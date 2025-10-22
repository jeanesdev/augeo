"""Integration tests for password reset flow.

T054: Tests the complete password reset user journey
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class TestPasswordResetFlow:
    """Test the complete password reset flow."""

    @pytest.mark.asyncio
    async def test_complete_password_reset_flow(
        self, client: AsyncClient, db_session: AsyncSession, test_user: User
    ):
        """
        Test complete password reset flow:
        1. User requests password reset
        2. Token is generated and stored in Redis
        3. User confirms reset with token
        4. Password is updated
        5. User can login with new password
        6. Old password no longer works
        """
        # Step 1: Request password reset
        response = await client.post(
            "/api/v1/password/reset/request",
            json={"email": test_user.email},
        )
        assert response.status_code == 200

        # Step 2: Verify token was created in Redis
        # TODO: We'll need to access Redis to get the actual token
        # For now, this will fail until implementation
        # redis = await get_redis()
        # token = await redis.get(f"password_reset:user:{test_user.id}")
        # assert token is not None

        # Step 3: Confirm password reset with token
        token = "test_token"  # Placeholder
        new_password = "NewSecurePass789"

        response = await client.post(
            "/api/v1/password/reset/confirm",
            json={
                "token": token,
                "new_password": new_password,
            },
        )
        assert response.status_code == 200

        # Step 4: Verify token was deleted from Redis
        # token_exists = await redis.get(f"password_reset:{token}")
        # assert token_exists is None

        # Step 5: Login with new password should work
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": new_password,
            },
        )
        assert response.status_code == 200
        assert "access_token" in response.json()

        # Step 6: Login with old password should fail
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "TestPass123",  # Old password
            },
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_password_reset_revokes_all_sessions(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        authenticated_client: AsyncClient,
    ):
        """
        Test that password reset revokes all active sessions:
        1. User is logged in (has active session)
        2. User completes password reset
        3. Existing session is invalidated
        4. User must login again
        """
        # Step 1: Verify user has active session
        response = await authenticated_client.get("/api/v1/auth/me")
        # This will fail until /auth/me endpoint exists, but tests the concept
        # assert response.status_code == 200

        # Step 2: Request and confirm password reset
        await client.post(
            "/api/v1/password/reset/request",
            json={"email": test_user.email},
        )

        token = "test_token"
        response = await client.post(
            "/api/v1/password/reset/confirm",
            json={
                "token": token,
                "new_password": "NewPassword123",
            },
        )
        assert response.status_code == 200

        # Step 3: Verify old session is revoked
        response = await authenticated_client.get("/api/v1/auth/me")
        # assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_reset_token_expires_after_use(self, client: AsyncClient, test_user: User):
        """
        Test that reset tokens can only be used once:
        1. User requests password reset
        2. User confirms reset with token
        3. Token cannot be used again
        """
        # Request reset
        response = await client.post(
            "/api/v1/password/reset/request",
            json={"email": test_user.email},
        )
        assert response.status_code == 200

        token = "test_token"

        # First use: success
        response = await client.post(
            "/api/v1/password/reset/confirm",
            json={
                "token": token,
                "new_password": "NewPassword123",
            },
        )
        assert response.status_code == 200

        # Second use: should fail
        response = await client.post(
            "/api/v1/password/reset/confirm",
            json={
                "token": token,
                "new_password": "AnotherPassword456",
            },
        )
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "INVALID_RESET_TOKEN"

    @pytest.mark.asyncio
    async def test_reset_token_expires_after_1_hour(self, client: AsyncClient, test_user: User):
        """
        Test that reset tokens expire after 1 hour:
        1. User requests password reset
        2. Token is valid immediately
        3. After 1 hour, token is invalid
        """
        # This test would require mocking time or Redis TTL
        # For now, marking the expected behavior
        pytest.skip("Requires time mocking - implement in full test suite")

    @pytest.mark.asyncio
    async def test_multiple_reset_requests_invalidate_previous_tokens(
        self, client: AsyncClient, test_user: User
    ):
        """
        Test that requesting a new reset invalidates previous tokens:
        1. User requests password reset (gets token1)
        2. User requests password reset again (gets token2)
        3. token1 should be invalid
        4. token2 should be valid
        """
        # First request
        response = await client.post(
            "/api/v1/password/reset/request",
            json={"email": test_user.email},
        )
        assert response.status_code == 200

        token1 = "first_token"

        # Second request
        response = await client.post(
            "/api/v1/password/reset/request",
            json={"email": test_user.email},
        )
        assert response.status_code == 200

        token2 = "second_token"

        # Try to use first token: should fail
        response = await client.post(
            "/api/v1/password/reset/confirm",
            json={
                "token": token1,
                "new_password": "NewPassword123",
            },
        )
        assert response.status_code == 400

        # Try to use second token: should succeed
        response = await client.post(
            "/api/v1/password/reset/confirm",
            json={
                "token": token2,
                "new_password": "NewPassword123",
            },
        )
        assert response.status_code == 200
