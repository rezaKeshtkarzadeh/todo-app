from contextlib import asynccontextmanager
from redis.asyncio import Redis, ConnectionPool
from app.core.config import settings


_pool: ConnectionPool | None = None
_client: Redis | None = None


def get_redis_pool() -> ConnectionPool:
    global _pool
    if _pool is None:
        _pool = ConnectionPool.from_url(
            settings.redis.url,
            max_connections=50,
            decode_responses=True,
        )
    return _pool


def get_redis_client() -> Redis:
    global _client
    if _client is None:
        _client = Redis(connection_pool=get_redis_pool())
    return _client


@asynccontextmanager
async def redis_client():
    client = get_redis_client()
    try:
        yield client
    finally:
        pass


async def close_redis() -> None:
    global _client, _pool
    if _client:
        await _client.aclose()
        _client = None
    if _pool:
        await _pool.disconnect()
        _pool = None