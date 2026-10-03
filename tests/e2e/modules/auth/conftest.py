from collections.abc import AsyncIterator

import pytest

from src.shared.data.database import database
from tests.helpers import database_is_connected, reset_users_table


@pytest.fixture(autouse=True)
async def clean_users_table() -> AsyncIterator[None]:
    """Leave the `users` table empty around every test in this folder.

    The requests below reach the real repository, so each case that registers a
    user writes a real row. Without this the duplicate-email cases would depend
    on collection order, and a rerun against a kept container volume would fail
    on the rows the previous run left behind.

    The connection is opened only when the test did not already arrange one:
    the client fixture's ASGI lifespan owns the shared handle, and tearing it
    down from here would leave later requests unable to reach PostgreSQL.
    """
    connected_here = not database_is_connected()
    if connected_here:
        database.connect()

    await reset_users_table()

    try:
        yield
    finally:
        if database_is_connected():
            await reset_users_table()
        if connected_here and database_is_connected():
            await database.disconnect()
