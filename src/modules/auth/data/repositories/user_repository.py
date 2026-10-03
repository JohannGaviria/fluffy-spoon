from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.data.models.user_model import UserModel
from src.modules.auth.exceptions.user_exception import (
    UserAlreadyExistsException,
    UserRepositoryException,
)
from src.shared.infrastructure.logging.structlog_logger import StructlogLogger

_logger = StructlogLogger(__name__)

# PostgreSQL `unique_violation`. The email is the only unique constraint on
# `users`, so this code identifies the conflict that registration has to report
# as a conflict. Reading it off the driver error instead of importing the driver
# keeps the repository agnostic to whichever asyncpg exposes the exception.
_UNIQUE_VIOLATION_SQLSTATE = "23505"


def _sqlstate(exc: SQLAlchemyError) -> str | None:
    """Read the PostgreSQL error code off the driver exception.

    Not every `SQLAlchemyError` carries a driver exception: the state errors the
    session raises on its own, such as `PendingRollbackError`, have no `orig` at
    all, so the lookup has to tolerate its absence.

    Args:
        exc (SQLAlchemyError): The error raised by the database.

    Returns:
        str | None: The SQLSTATE code, or None when there is none to read.
    """
    return getattr(getattr(exc, "orig", None), "sqlstate", None)


def _is_unique_violation(exc: IntegrityError) -> bool:
    """Check whether an integrity error was raised by a unique constraint.

    Args:
        exc (IntegrityError): The integrity error raised by the database.

    Returns:
        bool: True when the underlying driver error is a unique violation.
    """
    return _sqlstate(exc) == _UNIQUE_VIOLATION_SQLSTATE


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
            # The driver message is never logged: `str()` of a SQLAlchemy error
            # renders the bound parameters of the statement, which for `save` is
            # the password hash. The SQLSTATE and the error class are what identify
            # the failure, and neither is a secret.
            _logger.error(
                "An error occurred while retrieving user by email address.",
                sqlstate=_sqlstate(exc),
                error_type=type(exc).__name__,
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
            UserAlreadyExistsException: The email is already taken. A concurrent
                registration can win the race after the caller checked, and the
                unique constraint is what reports it.
            UserRepositoryException: Any other error occurred while saving user.
        """
        try:
            user = UserModel(name=name, email=email, password_hash=password_hash)
            self._session.add(user)
            await self._session.flush()
            await self._session.refresh(user)
            return user
        except IntegrityError as exc:
            _logger.error(
                "An error occurred while saving user.",
                sqlstate=_sqlstate(exc),
                error_type=type(exc).__name__,
            )
            if _is_unique_violation(exc):
                raise UserAlreadyExistsException() from exc
            raise UserRepositoryException(
                "An error occurred while saving user."
            ) from exc
        except SQLAlchemyError as exc:
            _logger.error(
                "An error occurred while saving user.",
                sqlstate=_sqlstate(exc),
                error_type=type(exc).__name__,
            )
            raise UserRepositoryException(
                "An error occurred while saving user."
            ) from exc
