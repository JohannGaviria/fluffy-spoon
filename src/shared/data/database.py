from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.config import settings
from src.shared.infrastructure.logging.structlog_logger import StructlogLogger

_logger = StructlogLogger(__name__)


class Database:
    def __init__(self) -> None:
        self._engine: AsyncEngine | None = None
        self._sessionmaker: async_sessionmaker[AsyncSession] | None = None

    def connect(self) -> None:
        if self._engine is not None:
            _logger.debug("Database already connected.")
            return

        _logger.debug("Connecting to database...")

        self._engine = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.DB_ECHO,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_timeout=settings.DB_POOL_TIMEOUT,
            pool_pre_ping=True,
        )
        self._sessionmaker = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
        _logger.debug("Database connected.")

    async def disconnect(self) -> None:
        if self._engine is not None:
            _logger.debug("Disconnecting from database...")
            await self._engine.dispose()
        self._engine = None
        self._sessionmaker = None
        _logger.debug("Database disconnected.")

    async def ping(self) -> bool:
        if self._engine is None:
            _logger.debug("Database not connected. Calling connect()...")
            raise RuntimeError("Database not connected. Call connect() first.")

        async with self._engine.connect() as conn:
            _logger.debug("Pinging database...")
            await conn.execute(text("SELECT 1"))
        _logger.debug("Database ping successful.")
        return True

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        """Context manager that provides a session and ensures its closure.

        It does not automatically commit: the caller (use case / unit of work)
        decides when to commit the transaction. In the event of an exception,
        a rollback is performed before propagating it.
        """
        if self._sessionmaker is None:
            _logger.debug("Database not connected. Calling connect()...")
            raise RuntimeError("Database not connected. Call connect() first.")

        async with self._sessionmaker() as session:
            try:
                _logger.debug("Session acquired.")
                yield session
            except Exception:
                _logger.debug("Rolling back session...")
                await session.rollback()
                raise

    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        if self._sessionmaker is None:
            _logger.debug("Database not connected. Calling connect()...")
            raise RuntimeError("Database not connected. Call connect() first.")

        return self._sessionmaker


database = Database()
