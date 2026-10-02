from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.data.database import database


async def get_session() -> AsyncGenerator[AsyncSession]:
    """Provide a database session for a request.

    The session is committed after the request completes successfully.
    If an exception occurs, the transaction is rolled back and the
    exception is re-raised.

    Yields:
        AsyncSession: Active database session.
    """
    async with database.session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
