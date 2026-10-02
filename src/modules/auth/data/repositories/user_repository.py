from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
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

    async def save(self, name: str, email: str, password_hash: str) -> UserModel:
        """Save user to database.

        Args:
            name (str): Name of user.
            email (str): Email address of user.
            password_hash (str): Password hash of user.

        Returns:
            UserModel: User model to save.

        Raises:
            UserRepositoryException: An error occurred while saving user.
        """
        try:
            user = UserModel(name=name, email=email, password_hash=password_hash)
            self._session.add(user)
            await self._session.flush()
            await self._session.refresh(user)
            return user
        except IntegrityError as exc:
            _logger.error("An error occurred while saving user.", error=str(exc))
            raise UserRepositoryException(
                "An error occurred while saving user."
            ) from exc
        except SQLAlchemyError as exc:
            _logger.error("An error occurred while saving user.", error=str(exc))
            raise UserRepositoryException(
                "An error occurred while saving user."
            ) from exc
