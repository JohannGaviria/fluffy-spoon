from __future__ import annotations

import redis.asyncio as redis
from redis.asyncio import Redis

from src.config import settings
from src.shared.infrastructure.logging.structlog_logger import StructlogLogger

_logger = StructlogLogger(__name__)


class RedisClient:
    def __init__(self) -> None:
        self._pool: redis.ConnectionPool | None = None
        self._client: Redis | None = None

    def connect(self) -> None:
        if self._client is not None:
            _logger.debug("Redis already connected.")
            return

        _logger.debug("Connecting to Redis...")

        self._pool = redis.ConnectionPool.from_url(
            settings.REDIS_URL,
            max_connections=settings.REDIS_MAX_CONNECTIONS,
            decode_responses=settings.REDIS_DECODE_RESPONSES,
        )
        self._client = redis.Redis(connection_pool=self._pool)
        _logger.debug("Redis connected.")

    async def disconnect(self) -> None:
        if self._client is not None:
            _logger.debug("Disconnecting from Redis...")
            await self._client.aclose()
        if self._pool is not None:
            _logger.debug("Closing Redis connection pool...")
            await self._pool.disconnect()
        self._client = None
        self._pool = None
        _logger.debug("Redis disconnected.")

    async def ping(self) -> bool:
        _logger.debug("Pinging Redis...")
        return bool(await self.client.ping())

    @property
    def client(self) -> Redis:
        if self._client is None:
            _logger.debug("Redis not connected. Calling connect()...")
            raise RuntimeError("Redis not connected. Call connect() first.")
        return self._client


redis_client = RedisClient()
