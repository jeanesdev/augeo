"""Unit tests for JWT blacklist logic.

These tests verify:
1. Tokens can be added to blacklist
2. Blacklisted tokens are correctly identified
3. Non-blacklisted tokens pass validation
4. Blacklist entries have correct TTL (Time To Live)
5. Redis key patterns are correct
6. Expired blacklist entries are cleaned up

Tests the Redis blacklist service in isolation.
"""

from unittest.mock import AsyncMock

import pytest

from app.services.redis_service import RedisService


class TestJWTBlacklistUnit:
    """Unit tests for JWT blacklist functionality."""

    @pytest.fixture
    def mock_redis_client(self):
        """Create a mock Redis client."""
        mock_client = AsyncMock()
        return mock_client

    @pytest.fixture
    def redis_service(self, mock_redis_client):
        """Create RedisService with mocked Redis client."""
        service = RedisService()
        # Mock the internal redis client (this will need adjustment based on actual implementation)
        service._redis = mock_redis_client  # noqa: SLF001
        return service

    @pytest.mark.asyncio
    async def test_blacklist_token_stores_jti_in_redis(self, redis_service, mock_redis_client):
        """Test blacklisting a token stores its JTI in Redis.

        Flow:
        1. Call blacklist_token(jti, ttl)
        2. Verify Redis SET command called with correct key and TTL
        """
        jti = "550e8400-e29b-41d4-a716-446655440000"
        ttl_seconds = 900  # 15 minutes

        await redis_service.blacklist_token(jti, ttl_seconds)

        # Verify Redis SET was called with correct parameters
        expected_key = f"blacklist:token:{jti}"
        mock_redis_client.setex.assert_called_once_with(
            expected_key,
            ttl_seconds,
            "1",  # Value is just "1" (presence check)
        )

    @pytest.mark.asyncio
    async def test_is_token_blacklisted_returns_true_for_blacklisted_token(
        self, redis_service, mock_redis_client
    ):
        """Test checking a blacklisted token returns True.

        Flow:
        1. Token is in blacklist (Redis returns value)
        2. is_token_blacklisted() returns True
        """
        jti = "550e8400-e29b-41d4-a716-446655440000"

        # Mock Redis GET to return "1" (token is blacklisted)
        mock_redis_client.get.return_value = "1"

        result = await redis_service.is_token_blacklisted(jti)

        # Verify result is True
        assert result is True

        # Verify Redis GET was called with correct key
        expected_key = f"blacklist:token:{jti}"
        mock_redis_client.get.assert_called_once_with(expected_key)

    @pytest.mark.asyncio
    async def test_is_token_blacklisted_returns_false_for_valid_token(
        self, redis_service, mock_redis_client
    ):
        """Test checking a non-blacklisted token returns False.

        Flow:
        1. Token not in blacklist (Redis returns None)
        2. is_token_blacklisted() returns False
        """
        jti = "650e8400-e29b-41d4-a716-446655440000"

        # Mock Redis GET to return None (token not blacklisted)
        mock_redis_client.get.return_value = None

        result = await redis_service.is_token_blacklisted(jti)

        # Verify result is False
        assert result is False

        # Verify Redis GET was called
        expected_key = f"blacklist:token:{jti}"
        mock_redis_client.get.assert_called_once_with(expected_key)

    @pytest.mark.asyncio
    async def test_blacklist_token_with_access_token_ttl(self, redis_service, mock_redis_client):
        """Test blacklist TTL matches access token expiry (15 minutes).

        Flow:
        1. Blacklist token with 900 second TTL
        2. Verify Redis sets TTL correctly
        """
        jti = "750e8400-e29b-41d4-a716-446655440000"
        ttl_seconds = 900  # Access token expiry time

        await redis_service.blacklist_token(jti, ttl_seconds)

        # Verify TTL is correct
        mock_redis_client.setex.assert_called_once()
        call_args = mock_redis_client.setex.call_args
        assert call_args[0][1] == ttl_seconds

    @pytest.mark.asyncio
    async def test_blacklist_token_with_zero_ttl_not_stored(self, redis_service, mock_redis_client):
        """Test token with 0 or negative TTL is not blacklisted.

        Flow:
        1. Attempt to blacklist expired token (TTL <= 0)
        2. Redis SET not called (no point storing expired entry)
        """
        jti = "850e8400-e29b-41d4-a716-446655440000"
        ttl_seconds = 0

        await redis_service.blacklist_token(jti, ttl_seconds)

        # Redis SET should not be called for expired tokens
        mock_redis_client.setex.assert_not_called()

    @pytest.mark.asyncio
    async def test_blacklist_uses_correct_redis_key_pattern(self, redis_service, mock_redis_client):
        """Test blacklist keys follow pattern: blacklist:token:{jti}.

        Flow:
        1. Blacklist multiple tokens
        2. Verify all use correct key pattern
        """
        jtis = [
            "111e8400-e29b-41d4-a716-446655440000",
            "222e8400-e29b-41d4-a716-446655440000",
            "333e8400-e29b-41d4-a716-446655440000",
        ]

        for jti in jtis:
            await redis_service.blacklist_token(jti, 900)

        # Verify all calls used correct key pattern
        assert mock_redis_client.setex.call_count == 3
        for i, jti in enumerate(jtis):
            call_args = mock_redis_client.setex.call_args_list[i]
            expected_key = f"blacklist:token:{jti}"
            assert call_args[0][0] == expected_key

    @pytest.mark.asyncio
    async def test_blacklist_token_handles_redis_connection_error(
        self, redis_service, mock_redis_client
    ):
        """Test graceful handling of Redis connection errors.

        Flow:
        1. Redis connection fails
        2. Blacklist operation raises appropriate error
        """
        jti = "950e8400-e29b-41d4-a716-446655440000"

        # Mock Redis to raise connection error
        mock_redis_client.setex.side_effect = ConnectionError("Redis unavailable")

        # Should raise error (don't silently fail on blacklist)
        with pytest.raises(ConnectionError):
            await redis_service.blacklist_token(jti, 900)

    @pytest.mark.asyncio
    async def test_is_token_blacklisted_handles_redis_connection_error(
        self, redis_service, mock_redis_client
    ):
        """Test checking blacklist when Redis is unavailable.

        Flow:
        1. Redis connection fails
        2. Return False or raise error (fail open vs fail closed)
        """
        jti = "a50e8400-e29b-41d4-a716-446655440000"

        # Mock Redis to raise connection error
        mock_redis_client.get.side_effect = ConnectionError("Redis unavailable")

        # Should either raise error or return False (fail closed = more secure)
        try:
            result = await redis_service.is_token_blacklisted(jti)
            # If it doesn't raise, it should fail closed (reject token)
            assert result is True  # Fail closed: treat as blacklisted
        except ConnectionError:
            # Raising error is also acceptable
            pass

    @pytest.mark.asyncio
    async def test_blacklist_entry_expires_after_ttl(self, redis_service, mock_redis_client):
        """Test blacklist entries automatically expire after TTL.

        Flow:
        1. Blacklist token with 900s TTL
        2. Wait > 900s (mocked)
        3. Token no longer blacklisted (Redis returns None)
        """
        jti = "b50e8400-e29b-41d4-a716-446655440000"
        ttl_seconds = 900

        # Blacklist the token
        await redis_service.blacklist_token(jti, ttl_seconds)

        # Mock Redis to simulate expiration (GET returns None after TTL)
        mock_redis_client.get.return_value = None

        # Check if blacklisted (should be expired)
        result = await redis_service.is_token_blacklisted(jti)
        assert result is False

    @pytest.mark.asyncio
    async def test_blacklist_multiple_tokens_independently(self, redis_service, mock_redis_client):
        """Test multiple tokens can be blacklisted independently.

        Flow:
        1. Blacklist token A
        2. Blacklist token B
        3. Check token A is blacklisted
        4. Check token B is blacklisted
        5. Check token C is not blacklisted
        """
        jti_a = "aa0e8400-e29b-41d4-a716-446655440000"
        jti_b = "bb0e8400-e29b-41d4-a716-446655440000"
        jti_c = "cc0e8400-e29b-41d4-a716-446655440000"

        # Blacklist A and B
        await redis_service.blacklist_token(jti_a, 900)
        await redis_service.blacklist_token(jti_b, 900)

        # Mock Redis to return correct values
        def get_side_effect(key):
            if key == f"blacklist:token:{jti_a}" or key == f"blacklist:token:{jti_b}":
                return "1"
            return None

        mock_redis_client.get.side_effect = get_side_effect

        # Verify A and B are blacklisted, C is not
        assert await redis_service.is_token_blacklisted(jti_a) is True
        assert await redis_service.is_token_blacklisted(jti_b) is True
        assert await redis_service.is_token_blacklisted(jti_c) is False

    @pytest.mark.asyncio
    async def test_blacklist_token_idempotent(self, redis_service, mock_redis_client):
        """Test blacklisting same token multiple times is idempotent.

        Flow:
        1. Blacklist token
        2. Blacklist same token again
        3. Both operations succeed
        4. Token is blacklisted once
        """
        jti = "dd0e8400-e29b-41d4-a716-446655440000"

        # Blacklist twice
        await redis_service.blacklist_token(jti, 900)
        await redis_service.blacklist_token(jti, 900)

        # Both calls should succeed
        assert mock_redis_client.setex.call_count == 2

        # Both set the same key
        call1_key = mock_redis_client.setex.call_args_list[0][0][0]
        call2_key = mock_redis_client.setex.call_args_list[1][0][0]
        assert call1_key == call2_key == f"blacklist:token:{jti}"
