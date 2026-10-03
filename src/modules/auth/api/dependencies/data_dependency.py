from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.data.repositories.user_repository import UserRepository
from src.shared.api.dependencies.data_dependency import get_session


def get_user_repository(
    session: AsyncSession = Depends(get_session),
) -> UserRepository:
    """Provide a user repository with an active database session.

    Args:
        session (AsyncSession): Active database session provided by
            the database session dependency.

    Returns:
        UserRepository: Repository configured with the database session.
    """
    return UserRepository(session=session)
