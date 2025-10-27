"""Integration tests for token refresh flow.

These tests verify the complete workflow of:
1. User logs in and receives tokens
2. Access token expires or needs refresh
3. User refreshes access token with refresh token
4. New access token is used successfully
5. Proper handling of expired/invalid refresh tokens

Integration tests verify the complete token lifecycle across services.
"""

import time
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings

settings = get_settings()


class TestTokenRefreshIntegration:
    """Integration tests for complete token refresh workflows."""

    @pytest.fixture
    async def verified_user_with_tokens(
        self, async_client: AsyncClient, db_session: AsyncSession
    ) -> dict[str, str]:
        """Create a verified user and return their login tokens."""
        # Register user
        register_payload = {
            "email": "refresh.integration@example.com",
            "password": "SecurePass123",
            "first_name": "Refresh",
            "last_name": "Integration",
        }
        register_response = await async_client.post("/api/v1/auth/register", json=register_payload)
        assert register_response.status_code == 201
        user_data = register_response.json()
        user_id = user_data["user"]["id"]

        # Manually verify email
        await db_session.execute(
            text("UPDATE users SET email_verified = true, is_active = true WHERE id = :id"),
            {"id": user_id},
        )
        await db_session.commit()

        # Login to get tokens
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "refresh.integration@example.com", "password": "SecurePass123"},
        )
        assert login_response.status_code == 200
        tokens = login_response.json()

        return {
            "user_id": user_id,
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "email": "refresh.integration@example.com",
        }

    @pytest.mark.asyncio
    async def test_complete_token_refresh_flow(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        verified_user_with_tokens: dict[str, str],
    ) -> None:
        """Test complete flow: login → refresh token → use new access token.

        Flow:
        1. User logs in successfully
        2. Access token needs refresh
        3. User refreshes with refresh token
        4. New access token works for authenticated endpoint
        5. Old access token still works (until expiry)
        """
        tokens = verified_user_with_tokens
        refresh_token = tokens["refresh_token"]

        # Step 1: Verify initial access token works
        async_client.headers["Authorization"] = f"Bearer {tokens['access_token']}"
        profile_response = await async_client.get("/api/v1/users/me")
        assert profile_response.status_code == 200

        # Step 2: Refresh the access token
        refresh_payload = {"refresh_token": refresh_token}
        refresh_response = await async_client.post("/api/v1/auth/refresh", json=refresh_payload)
        assert refresh_response.status_code == 200

        refresh_data = refresh_response.json()
        assert "access_token" in refresh_data
        assert "token_type" in refresh_data
        assert refresh_data["token_type"] == "bearer"
        assert "expires_in" in refresh_data
        assert refresh_data["expires_in"] == 900

        new_access_token = refresh_data["access_token"]

        # Verify new access token is different from old
        assert new_access_token != tokens["access_token"]

        # Step 3: Use new access token successfully
        async_client.headers["Authorization"] = f"Bearer {new_access_token}"
        profile_response2 = await async_client.get("/api/v1/users/me")
        assert profile_response2.status_code == 200
        assert profile_response2.json()["email"] == tokens["email"]

        # Step 4: Verify old access token still works (not blacklisted on refresh)
        async_client.headers["Authorization"] = f"Bearer {tokens['access_token']}"
        profile_response3 = await async_client.get("/api/v1/users/me")
        assert profile_response3.status_code == 200

    @pytest.mark.asyncio
    async def test_multiple_refreshes_with_same_refresh_token(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        verified_user_with_tokens: dict[str, str],
    ) -> None:
        """Test refresh token can be used multiple times (no rotation).

        Flow:
        1. User logs in
        2. Refreshes token 3 times with same refresh token
        3. All refreshes succeed
        4. Each returns a unique access token
        """
        tokens = verified_user_with_tokens
        refresh_token = tokens["refresh_token"]

        access_tokens = []

        # Refresh 3 times
        for i in range(3):
            refresh_payload = {"refresh_token": refresh_token}
            response = await async_client.post("/api/v1/auth/refresh", json=refresh_payload)

            assert response.status_code == 200, f"Refresh {i + 1} failed"
            data = response.json()
            access_tokens.append(data["access_token"])

            # Verify each access token works
            async_client.headers["Authorization"] = f"Bearer {data['access_token']}"
            profile_response = await async_client.get("/api/v1/users/me")
            assert profile_response.status_code == 200

        # Verify all access tokens are unique
        assert len(set(access_tokens)) == 3, "Access tokens should all be different"

    @pytest.mark.asyncio
    async def test_refresh_fails_after_logout(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        verified_user_with_tokens: dict[str, str],
    ) -> None:
        """Test refresh token becomes invalid after logout.

        Flow:
        1. User logs in
        2. User logs out (blacklists tokens)
        3. Attempt to refresh with blacklisted refresh token
        4. Refresh fails with 401
        """
        tokens = verified_user_with_tokens

        # Logout
        async_client.headers["Authorization"] = f"Bearer {tokens['access_token']}"
        logout_payload = {"refresh_token": tokens["refresh_token"]}
        logout_response = await async_client.post("/api/v1/auth/logout", json=logout_payload)
        assert logout_response.status_code == 200

        # Try to refresh with now-blacklisted token
        refresh_payload = {"refresh_token": tokens["refresh_token"]}
        refresh_response = await async_client.post("/api/v1/auth/refresh", json=refresh_payload)

        # Should be rejected
        assert refresh_response.status_code == 401
        assert refresh_response.json()["detail"]["code"] == "INVALID_REFRESH_TOKEN"

    @pytest.mark.asyncio
    async def test_refresh_with_expired_token_fails(
        self, async_client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test refresh with expired refresh token fails.

        Flow:
        1. Create an expired refresh token manually
        2. Attempt to refresh with it
        3. Refresh fails with 401
        """
        # Create an expired refresh token (expired 1 hour ago)
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        session_id = "650e8400-e29b-41d4-a716-446655440000"

        payload = {
            "sub": user_id,
            "type": "refresh",
            "jti": session_id,
            "exp": int((datetime.now(UTC) - timedelta(hours=1)).timestamp()),
            "iat": int((datetime.now(UTC) - timedelta(days=7, hours=1)).timestamp()),
        }

        expired_token = jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")

        # Try to refresh with expired token
        refresh_payload = {"refresh_token": expired_token}
        response = await async_client.post("/api/v1/auth/refresh", json=refresh_payload)

        # Should be rejected
        assert response.status_code == 401
        assert response.json()["detail"]["code"] == "INVALID_REFRESH_TOKEN"

    @pytest.mark.asyncio
    async def test_refresh_with_tampered_token_fails(self, async_client: AsyncClient) -> None:
        """Test refresh with tampered token fails signature validation.

        Flow:
        1. Create a token with invalid signature
        2. Attempt to refresh
        3. Refresh fails with 401
        """
        # Create a token with wrong signature
        tampered_token = (
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
            "eyJzdWIiOiIxMjM0NTY3ODkwIiwidHlwZSI6InJlZnJlc2gifQ."
            "invalid_signature_here"
        )

        refresh_payload = {"refresh_token": tampered_token}
        response = await async_client.post("/api/v1/auth/refresh", json=refresh_payload)

        # Should be rejected
        assert response.status_code == 401
        assert response.json()["detail"]["code"] == "INVALID_REFRESH_TOKEN"

    @pytest.mark.asyncio
    async def test_refresh_with_access_token_fails(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        verified_user_with_tokens: dict[str, str],
    ) -> None:
        """Test refresh fails when providing access token instead of refresh token.

        Flow:
        1. User logs in
        2. Attempt to refresh using access token (wrong token type)
        3. Refresh fails with 401
        """
        tokens = verified_user_with_tokens

        # Try to use access token for refresh (should fail - wrong type)
        refresh_payload = {"refresh_token": tokens["access_token"]}
        response = await async_client.post("/api/v1/auth/refresh", json=refresh_payload)

        # Should be rejected (access tokens have type="access", not "refresh")
        assert response.status_code == 401
        assert response.json()["detail"]["code"] == "INVALID_REFRESH_TOKEN"

    @pytest.mark.asyncio
    async def test_refresh_creates_new_jwt_with_updated_claims(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        verified_user_with_tokens: dict[str, str],
    ) -> None:
        """Test refreshed access token has updated timestamps and same user info.

        Flow:
        1. User logs in
        2. Wait a moment
        3. Refresh token
        4. Decode both tokens and verify timestamps differ but user_id same
        """
        tokens = verified_user_with_tokens
        old_access_token = tokens["access_token"]

        # Decode old token (without verification for inspection)
        old_claims = jwt.decode(old_access_token, options={"verify_signature": False})

        # Wait a moment to ensure different timestamp
        time.sleep(1)

        # Refresh
        refresh_payload = {"refresh_token": tokens["refresh_token"]}
        refresh_response = await async_client.post("/api/v1/auth/refresh", json=refresh_payload)
        assert refresh_response.status_code == 200

        new_access_token = refresh_response.json()["access_token"]

        # Decode new token
        new_claims = jwt.decode(new_access_token, options={"verify_signature": False})

        # Verify user_id (sub) is same
        assert old_claims["sub"] == new_claims["sub"]

        # Verify type is same
        assert old_claims["type"] == new_claims["type"] == "access"

        # Verify timestamps are different (issued at different times)
        assert old_claims["iat"] < new_claims["iat"], "New token should have later iat"
        assert old_claims["exp"] < new_claims["exp"], "New token should have later exp"

    @pytest.mark.asyncio
    async def test_refresh_without_session_in_redis_fails(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        verified_user_with_tokens: dict[str, str],
    ) -> None:
        """Test refresh fails if session was deleted from Redis.

        Flow:
        1. User logs in (creates session)
        2. Session is manually deleted from Redis
        3. Attempt to refresh
        4. Refresh fails even though JWT is valid
        """
        # This test requires Redis service implementation
        # For now, we document the expected behavior
        pytest.skip("Requires Redis session management implementation")

    @pytest.mark.asyncio
    async def test_refreshed_token_works_for_all_endpoints(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        verified_user_with_tokens: dict[str, str],
    ) -> None:
        """Test refreshed access token works for all authenticated endpoints.

        Flow:
        1. User logs in
        2. Refreshes token
        3. Uses new token for multiple endpoints
        4. All succeed
        """
        tokens = verified_user_with_tokens

        # Refresh
        refresh_payload = {"refresh_token": tokens["refresh_token"]}
        refresh_response = await async_client.post("/api/v1/auth/refresh", json=refresh_payload)
        assert refresh_response.status_code == 200

        new_access_token = refresh_response.json()["access_token"]

        # Test new token on multiple endpoints
        async_client.headers["Authorization"] = f"Bearer {new_access_token}"

        # Profile endpoint
        profile_response = await async_client.get("/api/v1/users/me")
        assert profile_response.status_code == 200

        # Logout endpoint
        logout_payload = {"refresh_token": tokens["refresh_token"]}
        logout_response = await async_client.post("/api/v1/auth/logout", json=logout_payload)
        assert logout_response.status_code == 200
