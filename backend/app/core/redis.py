"""Redis client configuration and connection pooling."""

import asyncio
from typing import TYPE_CHECKING

import redis.asyncio as redis  # noqa: F401
from redis.asyncio import Redis  # noqa: F401
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import RedisError
from redis.exceptions import TimeoutError as RedisTimeoutError

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.metrics import REDIS_FAILURES_TOTAL

if TYPE_CHECKING:
    from redis.asyncio import Redis as RedisType
else:
    RedisType = Redis

settings = get_settings()
logger = get_logger(__name__)

# Redis connection pool (singleton pattern)
_redis_client: RedisType | None = None  # type: ignore[type-arg]


async def get_redis() -> RedisType:  # type: ignore[type-arg]
    """Get Redis client with connection pooling and error handling.

    Returns:
        Redis: Async Redis client

    Raises:
        RedisConnectionError: Failed to connect to Redis after retries
        RedisTimeoutError: Redis operation timed out

    Example:
        redis_client = await get_redis()
        await redis_client.set("key", "value", ex=3600)
        value = await redis_client.get("key")
    """
    global _redis_client

    if _redis_client is None:
        max_retries = 3
        retry_delay = 1.0

        for attempt in range(max_retries):
            try:
                _redis_client = redis.from_url(
                    str(settings.redis_url),
                    encoding="utf-8",
                    decode_responses=True,
                    max_connections=10,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                )
                # Test connection
                await _redis_client.ping()
                logger.info("Redis connection established")
                break

            except (RedisConnectionError, RedisTimeoutError) as e:
                # Increment failure counter
                REDIS_FAILURES_TOTAL.inc()

                if attempt < max_retries - 1:
                    logger.warning(
                        "Redis connection failed, retrying",
                        extra={
                            "error": str(e),
                            "attempt": attempt + 1,
                            "max_retries": max_retries,
                            "retry_delay": retry_delay,
                        },
                    )
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error(
                        "Redis connection failed after all retries",
                        extra={
                            "error": str(e),
                            "max_retries": max_retries,
                        },
                    )
                    raise

            except RedisError as e:
                logger.error("Redis error during initialization", extra={"error": str(e)})
                raise

    # Type narrowing: _redis_client is not None here
    assert _redis_client is not None, "Redis client should be initialized"
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
