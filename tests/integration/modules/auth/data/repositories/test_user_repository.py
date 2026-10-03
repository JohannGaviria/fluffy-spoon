from collections.abc import AsyncIterator
from datetime import datetime
from typing import cast
from uuid import uuid4

import pytest
from sqlalchemy import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.data.models.user_model import UserModel
from src.modules.auth.data.repositories import user_repository as user_repository_module
from src.modules.auth.data.repositories.user_repository import UserRepository
from src.modules.auth.exceptions.user_exception import (
    UserAlreadyExistsException,
    UserRepositoryException,
)
from src.shared.data.database import database

pytestmark = pytest.mark.db

PASSWORD = "SecurePass!23"
PASSWORD_HASH = "$argon2id$v=19$m=8,t=1,p=1$fake-salt$fake-hash"


class RecordingLogger:
    """Stand-in for `StructlogLogger` that keeps what the repository handed the log.

    Asserting on the call instead of on rendered output keeps the test independent
    of the structlog configuration, which differs between a bare test process and
    the one the application configures on import. Only `error` records anything:
    it is the sole method `UserRepository` uses to report a failure.
    """

    def __init__(self) -> None:
        self.entries: list[str] = []

    def error(self, message: str, **kwargs: object) -> None:
        rendered = " ".join(f"{key}={value}" for key, value in kwargs.items())
        self.entries.append(f"{message} {rendered}")

    def debug(self, message: str, **kwargs: object) -> None:
        """Ignore the call; this repository only reports failures."""

    def info(self, message: str, **kwargs: object) -> None:
        """Ignore the call; this repository only reports failures."""

    def warning(self, message: str, **kwargs: object) -> None:
        """Ignore the call; this repository only reports failures."""

    def critical(self, message: str, **kwargs: object) -> None:
        """Ignore the call; this repository only reports failures."""


@pytest.fixture
def recording_logger(monkeypatch: pytest.MonkeyPatch) -> RecordingLogger:
    recorder = RecordingLogger()
    monkeypatch.setattr(user_repository_module, "_logger", recorder)
    return recorder


@pytest.fixture
async def session() -> AsyncIterator[AsyncSession]:
    """Yield a session on the connection the autouse fixture already opened."""
    async with database.session() as active_session:
        yield active_session


@pytest.fixture
def repository(session: AsyncSession) -> UserRepository:
    return UserRepository(session=session)


class TestUserRepository:
    class TestFindByEmail:
        async def test_should_return_the_user_when_the_email_is_registered(
            self,
            repository: UserRepository,
            session: AsyncSession,
        ):
            await repository.save(
                name="John Doe",
                email="john@doe.com",
                password_hash=PASSWORD_HASH,
            )
            await session.commit()

            found = await repository.find_by_email("john@doe.com")

            assert found is not None
            assert found.email == "john@doe.com"

        async def test_should_return_none_when_the_email_is_not_registered(
            self,
            repository: UserRepository,
        ):
            found = await repository.find_by_email("nobody@doe.com")

            assert found is None

        async def test_should_not_match_a_differently_cased_email(
            self,
            repository: UserRepository,
            session: AsyncSession,
        ):
            # The schema normalizes nothing, so the lookup is exact and registration
            # treats `John@doe.com` and `john@doe.com` as two accounts. Pinned so
            # that anyone relying on the other behaviour has to decide on it.
            await repository.save(
                name="John Doe",
                email="John@doe.com",
                password_hash=PASSWORD_HASH,
            )
            await session.commit()

            assert await repository.find_by_email("john@doe.com") is None

        async def test_should_translate_an_unusable_session_into_a_repository_error(
            self,
            repository: UserRepository,
            session: AsyncSession,
        ):
            # PostgreSQL aborts the whole transaction on a constraint failure, so a
            # lookup attempted before the rollback fails at `execute` rather than on
            # the query. The repository has to answer with its own exception: a
            # SQLAlchemy type escaping the data layer would reach the route, which
            # has no handler for it and would render a bare traceback.
            with pytest.raises(UserRepositoryException):
                await repository.save(
                    name="J" * 101,
                    email="john@doe.com",
                    password_hash=PASSWORD_HASH,
                )

            with pytest.raises(UserRepositoryException):
                await repository.find_by_email("john@doe.com")

            await session.rollback()

    class TestSave:
        async def test_should_persist_the_row(
            self,
            repository: UserRepository,
        ):
            await repository.save(
                name="John Doe",
                email="john@doe.com",
                password_hash=PASSWORD_HASH,
            )

            stored = await repository.find_by_email("john@doe.com")

            assert stored is not None
            assert stored.name == "John Doe"

        async def test_should_return_the_server_generated_id_and_timestamps(
            self,
            repository: UserRepository,
            session: AsyncSession,
        ):
            saved = await repository.save(
                name="John Doe",
                email="john@doe.com",
                password_hash=PASSWORD_HASH,
            )
            await session.commit()

            # `id`, `created_at` and `updated_at` come from the column defaults, so
            # the response DTO the endpoint builds only has them because the
            # repository flushes and refreshes before returning.
            assert saved.id is not None
            assert isinstance(saved.created_at, datetime)
            assert isinstance(saved.updated_at, datetime)

        async def test_should_store_the_hash_and_never_the_plaintext(
            self,
            repository: UserRepository,
            session: AsyncSession,
        ):
            await repository.save(
                name="John Doe",
                email="john@doe.com",
                password_hash=PASSWORD_HASH,
            )
            await session.commit()

            stored = await repository.find_by_email("john@doe.com")

            assert stored is not None
            assert stored.password_hash == PASSWORD_HASH
            assert PASSWORD not in stored.password_hash

        async def test_should_accept_a_name_of_the_maximum_length(
            self,
            repository: UserRepository,
        ):
            name = "J" * 100

            saved = await repository.save(
                name=name,
                email="john@doe.com",
                password_hash=PASSWORD_HASH,
            )

            assert saved.name == name

        async def test_should_report_a_server_error_when_the_name_overflows(
            self,
            repository: UserRepository,
            session: AsyncSession,
        ):
            # A truncation is an integrity failure but not a conflict, so it has to
            # stay a 500 rather than turning into a 409.
            with pytest.raises(UserRepositoryException):
                await repository.save(
                    name="J" * 101,
                    email="john@doe.com",
                    password_hash=PASSWORD_HASH,
                )

            await session.rollback()

        async def test_should_report_a_server_error_when_a_required_field_is_null(
            self,
            repository: UserRepository,
            session: AsyncSession,
        ):
            # The only integrity failure a real driver produces that is neither a
            # unique violation nor a truncation: every column is `nullable=False`, so
            # a null one raises `not_null_violation` (SQLSTATE 23502). It has to
            # stay a 500, because a null value is not a conflict over the email.
            # The overflowing-name test above cannot prove this branch, because
            # SQLAlchemy classifies `varchar` truncation as `DataError`, which is a
            # sibling of `IntegrityError` rather than a subclass of it.
            with pytest.raises(UserRepositoryException):
                await repository.save(
                    name=cast(str, None),
                    email="john@doe.com",
                    password_hash=PASSWORD_HASH,
                )

            await session.rollback()

            assert await repository.find_by_email("john@doe.com") is None

        class TestUniqueEmail:
            async def test_should_report_a_conflict_when_the_email_is_already_taken(
                self,
                repository: UserRepository,
                session: AsyncSession,
            ):
                await repository.save(
                    name="John Doe",
                    email="john@doe.com",
                    password_hash=PASSWORD_HASH,
                )
                await session.commit()

                with pytest.raises(UserAlreadyExistsException):
                    await repository.save(
                        name="Impostor",
                        email="john@doe.com",
                        password_hash=PASSWORD_HASH,
                    )

            async def test_should_keep_the_first_row_when_a_duplicate_is_rejected(
                self,
                repository: UserRepository,
                session: AsyncSession,
            ):
                await repository.save(
                    name="John Doe",
                    email="john@doe.com",
                    password_hash=PASSWORD_HASH,
                )
                await session.commit()

                with pytest.raises(UserAlreadyExistsException):
                    await repository.save(
                        name="Impostor",
                        email="john@doe.com",
                        password_hash=PASSWORD_HASH,
                    )

                await session.rollback()

                stored = await repository.find_by_email("john@doe.com")

                assert stored is not None
                assert stored.name == "John Doe"

            async def test_should_keep_the_session_usable_after_a_duplicate(
                self,
                repository: UserRepository,
                session: AsyncSession,
            ):
                await repository.save(
                    name="John Doe",
                    email="john@doe.com",
                    password_hash=PASSWORD_HASH,
                )
                await session.commit()

                with pytest.raises(UserAlreadyExistsException):
                    await repository.save(
                        name="Impostor",
                        email="john@doe.com",
                        password_hash=PASSWORD_HASH,
                    )

                await session.rollback()

                # PostgreSQL aborts the transaction on a constraint failure. If the
                # repository left the session unrecoverable, the next write on the
                # same connection would fail with `current transaction is aborted`.
                await repository.save(
                    name="Grace Hopper",
                    email="grace@hopper.dev",
                    password_hash=PASSWORD_HASH,
                )
                await session.commit()

                assert await repository.find_by_email("grace@hopper.dev") is not None


class TestUserRepositoryLogging:
    async def test_should_not_write_the_hash_to_the_log_when_a_duplicate_is_rejected(
        self,
        repository: UserRepository,
        session: AsyncSession,
        recording_logger: RecordingLogger,
    ):
        # `save` reports the driver failure. The message it used to log verbatim
        # rendered the bound parameters of the INSERT, the password hash among
        # them, so every conflicting registration wrote the hash to the log.
        await repository.save(
            name="John Doe",
            email="john@doe.com",
            password_hash=PASSWORD_HASH,
        )
        await session.commit()
        recording_logger.entries.clear()

        with pytest.raises(UserAlreadyExistsException):
            await repository.save(
                name="Impostor",
                email="john@doe.com",
                password_hash=PASSWORD_HASH,
            )

        assert len(recording_logger.entries) == 1
        assert PASSWORD_HASH not in recording_logger.entries[0]

        await session.rollback()

    async def test_should_not_write_the_hash_to_the_log_when_the_name_overflows(
        self,
        repository: UserRepository,
        session: AsyncSession,
        recording_logger: RecordingLogger,
    ):
        with pytest.raises(UserRepositoryException):
            await repository.save(
                name="J" * 101,
                email="john@doe.com",
                password_hash=PASSWORD_HASH,
            )

        assert len(recording_logger.entries) == 1
        assert PASSWORD_HASH not in recording_logger.entries[0]

        await session.rollback()

    @pytest.mark.parametrize(
        ("name", "expected_sqlstate"),
        [
            pytest.param("J" * 101, "22001", id="truncated_name"),
            pytest.param(None, "23502", id="null_name"),
        ],
    )
    async def test_should_log_the_database_error_code_instead_of_the_driver_message(
        self,
        repository: UserRepository,
        session: AsyncSession,
        recording_logger: RecordingLogger,
        name: str | None,
        expected_sqlstate: str,
    ):
        # Pinning the fields that replaced the driver message: the failure has to
        # stay diagnosable, so removing the leak cannot become "log nothing".
        with pytest.raises((UserRepositoryException, UserAlreadyExistsException)):
            await repository.save(
                name=cast(str, name),
                email="john@doe.com",
                password_hash=PASSWORD_HASH,
            )

        assert len(recording_logger.entries) == 1
        entry = recording_logger.entries[0]

        assert f"sqlstate={expected_sqlstate}" in entry
        assert "error_type=" in entry
        assert "[parameters:" not in entry

        await session.rollback()

    async def test_should_not_write_a_password_hash_to_the_log_when_a_lookup_fails(
        self,
        repository: UserRepository,
        session: AsyncSession,
        recording_logger: RecordingLogger,
    ):
        # The read path reports the same way, and a failing statement renders its
        # bound parameters through `str()` too.
        with pytest.raises(UserRepositoryException):
            await repository.save(
                name="J" * 101,
                email="john@doe.com",
                password_hash=PASSWORD_HASH,
            )

        recording_logger.entries.clear()

        with pytest.raises(UserRepositoryException):
            await repository.find_by_email("john@doe.com")

        assert len(recording_logger.entries) == 1
        entry = recording_logger.entries[0]

        # `PendingRollbackError` comes from the session, not the driver, so it has
        # no code to report. Pinned so that reading one is not mistaken for a bug.
        assert "sqlstate=None" in entry
        assert "error_type=PendingRollbackError" in entry
        assert "[parameters:" not in entry

        await session.rollback()


class TestUsersDatabaseConstraints:
    async def test_should_reject_a_duplicate_email_at_the_database_level(
        self,
        session: AsyncSession,
    ):
        # Verify the database constraint independently from the repository.
        with pytest.raises(IntegrityError) as exc_info:
            await session.execute(
                insert(UserModel),
                [
                    {
                        "id": uuid4(),
                        "name": "John Doe",
                        "email": "john@doe.com",
                        "password_hash": PASSWORD_HASH,
                    },
                    {
                        "id": uuid4(),
                        "name": "Impostor",
                        "email": "john@doe.com",
                        "password_hash": PASSWORD_HASH,
                    },
                ],
            )

        # PostgreSQL's unique-violation SQLSTATE.
        assert getattr(exc_info.value.orig, "sqlstate", None) == "23505"
