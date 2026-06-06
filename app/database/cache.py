# application/database.py

import redis.asyncio as redis
from ..core.config import settings
from ..core.log import logger


class RedisClient:
    """Redis client wrapper with connection management"""

    def __init__(self):
        self._client: redis.Redis | None = None

    async def connect(self) -> None:
        """Connect to Redis with connection pool"""
        try:
            self._client = redis.from_url(
                settings.REDIS_DB,
                decode_responses=True,
                max_connections=settings.REDIS_MAX_CONNECTIONS,
                socket_connect_timeout=5,
                socket_keepalive=True,
                health_check_interval=30,
            )

            # Test connection
            await self._client.ping()
            logger.info(f"✅ Redis connected: {settings.REDIS_DB}")

        except redis.ConnectionError as e:
            logger.error(f"❌ Redis connection failed: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error connecting to Redis: {e}")
            raise

    async def disconnect(self) -> None:
        """Close Redis connection"""
        if self._client:
            try:
                await self._client.aclose()
                logger.info("🧹 Redis connection closed")
            except Exception as e:
                logger.error(f"Error closing Redis: {e}")

    @property
    def client(self) -> redis.Redis:
        """Get Redis client instance"""
        if self._client is None:
            raise RuntimeError("Redis client not initialized. Call connect() first.")
        return self._client

    async def is_connected(self) -> bool:
        """Check if Redis is connected"""
        try:
            if self._client:
                await self._client.ping()
                return True
        except Exception:
            pass
        return False


# Singleton instance
cache = RedisClient()


def redis_cache():
    return RedisClient().client