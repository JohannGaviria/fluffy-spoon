from collections.abc import AsyncIterator

import pytest

from src.shared.data.database import database
from tests.helpers import database_is_connected, reset_users_table


@pytest.fixture(autouse=True)
async def clean_users_table() -> AsyncIterator[None]:
    """Leave the `users` table empty around every test in this folder.

    Registration persists rows for real, so without this a suite run would make
    the duplicate-email cases pass or fail depending on the order pytest happens
    to collect them, and a rerun against a kept container volume would fail on
    rows left by the previous run.

    The connection is opened only when the test did not already arrange one:
    the end-to-end lifespan owns the shared handle, and tearing it down from
    here would leave later tests unable to reach PostgreSQL.
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
