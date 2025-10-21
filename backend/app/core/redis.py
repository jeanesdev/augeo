"""Redis client configuration and connection pooling."""

from typing import Any

import redis.asyncio as redis  # noqa: F401
from redis.asyncio import Redis  # noqa: F401

from app.core.config import get_settings

settings = get_settings()

# Redis connection pool (singleton pattern)
_redis_client: Redis[Any] | None = None


async def get_redis() -> Redis[Any]:
    """Get Redis client with connection pooling.

    Returns:
        Redis: Async Redis client

    Example:
        redis_client = await get_redis()
        await redis_client.set("key", "value", ex=3600)
        value = await redis_client.get("key")
    """
    global _redis_client

    if _redis_client is None:
        _redis_client = redis.from_url(
            str(settings.redis_url),
            encoding="utf-8",
            decode_responses=True,
            max_connections=10,
        )

    return _redis_client


async def close_redis() -> None:
    """Close Redis connection pool.

    Call this on application shutdown.
    """
    global _redis_client

    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None


# Redis key prefixes for namespacing
class RedisKeys:
    """Redis key prefixes for different data types."""

    SESSION = "session:"
    REFRESH_TOKEN = "refresh:"
    JWT_BLACKLIST = "jwt:blacklist:"
    EMAIL_VERIFY = "email:verify:"
    PASSWORD_RESET = "password:reset:"
    RATE_LIMIT = "rate:limit:"

    @staticmethod
    def session(user_id: str) -> str:
        """Generate session key for user."""
        return f"{RedisKeys.SESSION}{user_id}"

    @staticmethod
    def refresh_token(token_id: str) -> str:
        """Generate refresh token key."""
        return f"{RedisKeys.REFRESH_TOKEN}{token_id}"

    @staticmethod
    def jwt_blacklist(jti: str) -> str:
        """Generate JWT blacklist key."""
        return f"{RedisKeys.JWT_BLACKLIST}{jti}"

    @staticmethod
    def email_verify(token: str) -> str:
        """Generate email verification key."""
        return f"{RedisKeys.EMAIL_VERIFY}{token}"

    @staticmethod
    def password_reset(token: str) -> str:
        """Generate password reset key."""
        return f"{RedisKeys.PASSWORD_RESET}{token}"

    @staticmethod
    def rate_limit(identifier: str, action: str) -> str:
        """Generate rate limit key."""
        return f"{RedisKeys.RATE_LIMIT}{action}:{identifier}"
