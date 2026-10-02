from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.data.models.user_model import UserModel
from src.modules.auth.exceptions.user_exception import UserRepositoryException
from src.shared.infrastructure.logging.structlog_logger import StructlogLogger

_logger = StructlogLogger(__name__)


class UserRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def find_by_email(self, email: str) -> UserModel | None:
        """Find user by email.

        Args:
            email (str): Email address of user to find.

        Returns:
            UserModel | None: User model or None if user not found.

        Raises:
            UserRepositoryException: An error occurred while retrieving user by email address.
        """
        try:
            stmt = select(UserModel).where(UserModel.email == email)
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as exc:
            _logger.error(
                "An error occurred while retrieving user by email address.",
                error=str(exc),
                email=email,
            )
            raise UserRepositoryException(
                "An error occurred while retrieving user by email address."
            ) from exc
