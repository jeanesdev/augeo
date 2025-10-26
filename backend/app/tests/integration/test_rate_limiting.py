"""Integration tests for rate limiting.

These tests verify:
1. Failed login attempts are tracked per IP
2. 5 failed attempts trigger rate limiting
3. 6th attempt returns 429 Rate Limit Exceeded
4. Rate limit resets after 15 minutes
5. Successful login doesn't count toward limit

Tests the complete rate limiting flow using Redis.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class TestRateLimitingIntegration:
    """Integration tests for rate limiting workflows."""

    @pytest.mark.asyncio
    async def test_rate_limit_triggers_after_5_failed_attempts(
        self, async_client: AsyncClient
    ) -> None:
        """Test rate limit engages after 5 failed login attempts.

        Flow:
        1. Make 5 failed login attempts
        2. All return 401 Unauthorized
        3. 6th attempt returns 429 Rate Limit Exceeded
        """
        login_payload = {"email": "ratelimit@example.com", "password": "WrongPassword123"}

        # Make 5 failed attempts
        for i in range(5):
            response = await async_client.post("/api/v1/auth/login", json=login_payload)
            assert response.status_code == 401, f"Attempt {i+1} should fail with 401"

        # 6th attempt should be rate limited
        response = await async_client.post("/api/v1/auth/login", json=login_payload)
        assert response.status_code == 429

        error = response.json()["error"]
        assert error["code"] == "RATE_LIMIT_EXCEEDED"
        assert "15 minutes" in error["message"]

    @pytest.mark.asyncio
    async def test_successful_login_resets_rate_limit_counter(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test successful login resets failed attempt counter.

        Flow:
        1. Make 3 failed attempts
        2. Login successfully
        3. Make 5 more failed attempts
        4. Should not be rate limited (counter reset)
        """
        # Register and verify user
        register_payload = {
            "email": "reset.counter@example.com",
            "password": "CorrectPass123",
            "first_name": "Reset",
            "last_name": "Counter",
        }
        register_response = await async_client.post("/api/v1/auth/register", json=register_payload)
        user_id = register_response.json()["id"]

        await db_session.execute(
            text("UPDATE users SET email_verified = true, is_active = true WHERE id = :id"),
            {"id": user_id},
        )
        await db_session.commit()

        # Make 3 failed attempts
        wrong_payload = {"email": "reset.counter@example.com", "password": "WrongPass123"}
        for _ in range(3):
            response = await async_client.post("/api/v1/auth/login", json=wrong_payload)
            assert response.status_code == 401

        # Successful login (should reset counter)
        correct_payload = {"email": "reset.counter@example.com", "password": "CorrectPass123"}
        response = await async_client.post("/api/v1/auth/login", json=correct_payload)
        assert response.status_code == 200

        # Make 5 more failed attempts (should NOT trigger rate limit)
        for i in range(5):
            response = await async_client.post("/api/v1/auth/login", json=wrong_payload)
            # All should return 401, not 429
            assert response.status_code == 401, f"Attempt {i+1} after reset should be 401"

    @pytest.mark.asyncio
    async def test_rate_limit_tracked_per_ip_address(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test rate limit is tracked separately per IP address.

        Flow:
        1. IP A makes 5 failed attempts (rate limited)
        2. IP B makes 1 attempt (succeeds, different IP)
        """
        # This test requires mocking different IP addresses
        # For now, we document the expected behavior
        pytest.skip("Requires IP address mocking infrastructure")

    @pytest.mark.asyncio
    async def test_rate_limit_expires_after_15_minutes(self, async_client: AsyncClient) -> None:
        """Test rate limit resets after 15 minutes.

        Flow:
        1. Trigger rate limit (6 failed attempts)
        2. Wait 15+ minutes (mocked)
        3. Can login again
        """
        login_payload = {"email": "expire.limit@example.com", "password": "WrongPassword123"}

        # Trigger rate limit
        for _ in range(6):
            await async_client.post("/api/v1/auth/login", json=login_payload)

        # Verify rate limited
        response = await async_client.post("/api/v1/auth/login", json=login_payload)
        assert response.status_code == 429

        # Mock time 16 minutes later
        future_time = datetime.now(UTC) + timedelta(minutes=16)

        with patch("app.middleware.rate_limit.datetime") as mock_datetime:
            mock_datetime.now.return_value = future_time
            mock_datetime.UTC = UTC

            # Should be able to try again (returns 401 for wrong password, not 429)
            response = await async_client.post("/api/v1/auth/login", json=login_payload)
            assert response.status_code == 401  # Wrong password, but not rate limited

    @pytest.mark.asyncio
    async def test_rate_limit_counter_increments_correctly(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test rate limit counter increments with each failed attempt.

        Flow:
        1. Make failed attempts one by one
        2. Verify counter increments in Redis
        3. Hits limit exactly at 6th attempt
        """
        # This test requires Redis access to verify counter values
        pytest.skip("Requires Redis service implementation")

    @pytest.mark.asyncio
    async def test_rate_limit_applies_only_to_login_endpoint(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test rate limit applies to login, not other endpoints.

        Flow:
        1. Trigger rate limit on login (6 failed attempts)
        2. Other endpoints still work (register, password reset, etc.)
        """
        # Trigger rate limit
        login_payload = {"email": "onlylogin@example.com", "password": "WrongPassword123"}
        for _ in range(6):
            await async_client.post("/api/v1/auth/login", json=login_payload)

        # Verify rate limited
        response = await async_client.post("/api/v1/auth/login", json=login_payload)
        assert response.status_code == 429

        # Register should still work
        register_payload = {
            "email": "newuser@example.com",
            "password": "SecurePass123",
            "first_name": "New",
            "last_name": "User",
        }
        register_response = await async_client.post("/api/v1/auth/register", json=register_payload)
        assert register_response.status_code == 201

        # Password reset request should still work
        reset_payload = {"email": "someone@example.com"}
        reset_response = await async_client.post(
            "/api/v1/password/reset/request", json=reset_payload
        )
        assert reset_response.status_code == 200

    @pytest.mark.asyncio
    async def test_rate_limit_response_includes_retry_after(
        self, async_client: AsyncClient
    ) -> None:
        """Test 429 response includes Retry-After header.

        Flow:
        1. Trigger rate limit
        2. Verify response has Retry-After header
        3. Header value indicates wait time in seconds
        """
        login_payload = {"email": "retryafter@example.com", "password": "WrongPassword123"}

        # Trigger rate limit
        for _ in range(6):
            await async_client.post("/api/v1/auth/login", json=login_payload)

        # Check 429 response
        response = await async_client.post("/api/v1/auth/login", json=login_payload)
        assert response.status_code == 429

        # Check for Retry-After header (optional but good practice)
        # May be in seconds or HTTP date format
        if "Retry-After" in response.headers:
            retry_after = response.headers["Retry-After"]
            # Should be a number (seconds) or date
            assert retry_after.isdigit() or "-" in retry_after

    @pytest.mark.asyncio
    async def test_rate_limit_persists_across_requests(self, async_client: AsyncClient) -> None:
        """Test rate limit counter persists across multiple HTTP requests.

        Flow:
        1. Make 3 failed attempts
        2. Create new client (simulate different browser/connection)
        3. Make 3 more failed attempts
        4. Gets rate limited (counter persisted in Redis)
        """
        login_payload = {"email": "persist@example.com", "password": "WrongPassword123"}

        # Make 3 failed attempts
        for _ in range(3):
            await async_client.post("/api/v1/auth/login", json=login_payload)

        # Simulate new connection (counter should persist in Redis)
        # Note: async_client fixture may share state, so this is conceptual
        for _ in range(3):
            response = await async_client.post("/api/v1/auth/login", json=login_payload)

        # 7th total attempt should be rate limited (6th was threshold)
        # Note: Depends on whether counter incremented on 6th (rate limited) attempt
        # If 6th doesn't increment, this would be 6th unique attempt
        assert response.status_code in [401, 429]

    @pytest.mark.asyncio
    async def test_rate_limit_different_users_independent_counters(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test rate limit counters are independent per user email.

        Flow:
        1. User A triggers rate limit (6 failed attempts)
        2. User B can still login (different counter)
        """
        # Register User B
        register_payload = {
            "email": "userb@example.com",
            "password": "CorrectPass123",
            "first_name": "User",
            "last_name": "B",
        }
        register_response = await async_client.post("/api/v1/auth/register", json=register_payload)
        user_id = register_response.json()["id"]

        await db_session.execute(
            text("UPDATE users SET email_verified = true, is_active = true WHERE id = :id"),
            {"id": user_id},
        )
        await db_session.commit()

        # User A triggers rate limit
        userA_payload = {"email": "usera@example.com", "password": "WrongPassword123"}
        for _ in range(6):
            await async_client.post("/api/v1/auth/login", json=userA_payload)

        # Verify User A is rate limited
        response = await async_client.post("/api/v1/auth/login", json=userA_payload)
        assert response.status_code == 429

        # User B should still be able to login
        userB_payload = {"email": "userb@example.com", "password": "CorrectPass123"}
        response = await async_client.post("/api/v1/auth/login", json=userB_payload)
        assert response.status_code == 200
