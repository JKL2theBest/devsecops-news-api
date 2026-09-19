from collections.abc import AsyncGenerator

import redis.asyncio as aioredis
from redis.asyncio import ConnectionPool

from app.core.config import settings

redis_pool: ConnectionPool | None = None


async def init_redis_pool() -> None:
    """Инициализирует глобальный пул соединений Redis."""
    global redis_pool  # noqa: PLW0603
    if redis_pool is None:
        redis_pool = aioredis.ConnectionPool.from_url(
            f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0",
            decode_responses=True,
        )


async def get_redis_client() -> AsyncGenerator[aioredis.Redis]:
    """Предоставляет клиент Redis."""
    if redis_pool is None:
        await init_redis_pool()

    if not redis_pool:
        msg = "Redis connection pool could not be initialized"
        raise ConnectionError(msg)

    async with aioredis.Redis(connection_pool=redis_pool) as client:
        yield client


async def close_redis_pool() -> None:
    """Закрывает пул соединений Redis."""
    global redis_pool  # noqa: PLW0603
    if redis_pool:
        await redis_pool.disconnect()
        redis_pool = None
