"""Test doubles for the auth unit tests.

Every double subclasses the type it stands in for and skips its constructor, so
it satisfies the annotations the production code is checked against without
opening a connection or spending the configured Argon2 parameters.
"""

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.data.models.user_model import UserModel
from src.modules.auth.data.repositories.user_repository import UserRepository
from src.modules.auth.infrastructure.password_hasher import Argon2PasswordHasher
from src.shared.infrastructure.logging.structlog_logger import StructlogLogger


class RecordingLogger(StructlogLogger):
    """Stand-in for `StructlogLogger` that keeps every call for assertions."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    def _record(self, level: str, message: str, **kwargs: Any) -> None:
        self.calls.append((level, message, kwargs))

    def debug(self, message: str, **kwargs: Any) -> None:
        self._record("debug", message, **kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        self._record("info", message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        self._record("warning", message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        self._record("error", message, **kwargs)

    def critical(self, message: str, **kwargs: Any) -> None:
        self._record("critical", message, **kwargs)

    def calls_at(self, level: str) -> list[tuple[str, str, dict[str, Any]]]:
        return [call for call in self.calls if call[0] == level]

    def rendered(self) -> str:
        """Every recorded call as one searchable blob, for leak assertions."""
        return repr(self.calls)


class FakeUserRepository(UserRepository):
    """Stand-in for `UserRepository` that records how it was called."""

    def __init__(
        self,
        *,
        existing_user: UserModel | None = None,
        saved_user: UserModel | None = None,
        find_error: Exception | None = None,
        save_error: Exception | None = None,
    ) -> None:
        self.existing_user = existing_user
        self.saved_user = saved_user
        self.find_error = find_error
        self.save_error = save_error
        self.find_calls: list[str] = []
        self.save_calls: list[dict[str, str]] = []

    async def find_by_email(self, email: str) -> UserModel | None:
        self.find_calls.append(email)
        if self.find_error is not None:
            raise self.find_error
        return self.existing_user

    async def save(self, name: str, email: str, password_hash: str) -> UserModel:
        self.save_calls.append(
            {"name": name, "email": email, "password_hash": password_hash}
        )
        if self.save_error is not None:
            raise self.save_error
        assert self.saved_user is not None
        return self.saved_user


class RecordingPasswordHasher(Argon2PasswordHasher):
    """Stand-in for `Argon2PasswordHasher` that records what it was given."""

    HASH_PREFIX = "$argon2id$fake-hash"

    def __init__(self) -> None:
        self.hashed: list[str] = []

    def hash(self, password: str) -> str:
        self.hashed.append(password)
        return self.HASH_PREFIX


class FakeScalarResult:
    """Stand-in for the SQLAlchemy result returned by `AsyncSession.execute`."""

    def __init__(self, value: UserModel | None) -> None:
        self._value = value

    def scalar_one_or_none(self) -> UserModel | None:
        return self._value


class FakeAsyncSession(AsyncSession):
    """Stand-in for `AsyncSession` that records the repository's statements.

    `AsyncSession` is instantiated with no bind on purpose: nothing here binds to
    an engine, and the four methods the repository uses are replaced, so there is
    no database to reach. The signatures keep `*args`/`**kwargs` so the overrides
    stay assignable to the overloaded originals.
    """

    def __init__(
        self,
        *,
        scalar_value: UserModel | None = None,
        execute_error: Exception | None = None,
        flush_error: Exception | None = None,
    ) -> None:
        super().__init__()
        self.scalar_value = scalar_value
        self.execute_error = execute_error
        self.flush_error = flush_error
        self.added: list[Any] = []
        self.executed: list[Any] = []
        self.refreshed: list[Any] = []
        self.flush_count = 0

    def add(self, instance: Any, *args: Any, **kwargs: Any) -> None:
        self.added.append(instance)

    async def execute(self, statement: Any, *args: Any, **kwargs: Any) -> Any:
        self.executed.append(statement)
        if self.execute_error is not None:
            raise self.execute_error
        return FakeScalarResult(self.scalar_value)

    async def flush(self, objects: Any = None) -> None:
        self.flush_count += 1
        if self.flush_error is not None:
            raise self.flush_error

    async def refresh(self, instance: Any, *args: Any, **kwargs: Any) -> None:
        self.refreshed.append(instance)


def build_user_model(
    *,
    id: UUID | None = None,
    name: str = "John Doe",
    email: str = "john@doe.com",
    password_hash: str = "$argon2id$fake-hash",
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
) -> UserModel:
    """Build a detached `UserModel`, with the timestamps the database provides.

    The columns in `BaseModel` use a `server_default`, so the values are absent
    on a detached instance. Supplying them here keeps the response DTO testable
    without a round trip.
    """
    now = datetime.now(timezone.utc)
    return UserModel(
        id=id or uuid4(),
        name=name,
        email=email,
        password_hash=password_hash,
        created_at=created_at or now,
        updated_at=updated_at or now,
    )
