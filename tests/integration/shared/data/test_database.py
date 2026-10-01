import pytest
from sqlalchemy import text

from src.shared.data.database import Database

pytestmark = pytest.mark.db


class TestDatabase:
    async def test_should_connect_when_connect_is_called(self):
        database = Database()

        database.connect()

        assert await database.ping() is True

        await database.disconnect()

    async def test_should_be_idempotent_when_connect_is_called_twice(self):
        database = Database()

        database.connect()
        first_engine = database._engine
        database.connect()
        second_engine = database._engine

        assert first_engine is second_engine

        await database.disconnect()

    async def test_should_raise_runtime_error_when_ping_called_before_connect(
        self,
    ):
        database = Database()

        with pytest.raises(RuntimeError):
            await database.ping()

    async def test_should_raise_runtime_error_when_session_called_before_connect(
        self,
    ):
        database = Database()

        with pytest.raises(RuntimeError):
            async with database.session():
                pass

    async def test_should_be_idempotent_when_disconnect_is_called_without_connect(
        self,
    ):
        database = Database()

        await database.disconnect()

    async def test_should_be_idempotent_when_disconnect_is_called_twice(self):
        database = Database()
        database.connect()

        await database.disconnect()
        await database.disconnect()

    async def test_should_reset_internal_state_when_disconnect_is_called(
        self,
    ):
        database = Database()
        database.connect()

        await database.disconnect()

        with pytest.raises(RuntimeError):
            await database.ping()

    async def test_should_allow_reconnect_when_connect_is_called_after_disconnect(
        self,
    ):
        database = Database()
        database.connect()
        await database.disconnect()

        database.connect()

        assert await database.ping() is True

        await database.disconnect()

    async def test_should_yield_working_session_when_session_is_used(self):
        database = Database()
        database.connect()

        async with database.session() as session:
            result = await session.execute(text("SELECT 1"))
            assert result.scalar() == 1

        await database.disconnect()

    async def test_should_rollback_when_exception_is_raised_inside_session(
        self,
    ):
        database = Database()
        database.connect()

        with pytest.raises(ValueError):
            async with database.session() as session:
                await session.execute(text("SELECT 1"))
                raise ValueError("boom")

        # The database is still usable afterwards, proving the session
        # was rolled back and closed cleanly rather than left dangling.
        async with database.session() as session:
            result = await session.execute(text("SELECT 1"))
            assert result.scalar() == 1

        await database.disconnect()

    async def test_should_close_session_when_context_manager_exits(self):
        database = Database()
        database.connect()

        async with database.session() as session:
            pass

        assert not session.is_active or session.in_transaction() is False

        await database.disconnect()

    async def test_should_raise_runtime_error_when_session_factory_called_before_connect(
        self,
    ):
        database = Database()

        with pytest.raises(RuntimeError):
            database.session_factory()

    async def test_should_return_sessionmaker_when_session_factory_is_called(self):
        database = Database()
        database.connect()

        session_factory = database.session_factory()

        assert session_factory is database._sessionmaker

        await database.disconnect()
