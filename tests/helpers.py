"""Helpers shared by the test suite."""

import socket
from urllib.parse import urlsplit

from sqlalchemy import text

from src.config import settings
from src.shared.data.database import database

REACHABILITY_TIMEOUT = 1.0


def _is_reachable(url: str, default_port: int) -> bool:
    """Check whether the host and port in a connection URL accept a TCP connection.

    Args:
        url: Connection URL to inspect, in either `postgresql+asyncpg://` or
            `redis://` form.
        default_port: Port to assume when the URL does not carry one.

    Returns:
        bool: True if a TCP connection could be established.
    """
    parsed = urlsplit(url)
    host = parsed.hostname
    if not host:
        return False

    port = parsed.port or default_port

    try:
        with socket.create_connection((host, port), timeout=REACHABILITY_TIMEOUT):
            return True
    except OSError:
        return False


def unreachable_services() -> list[str]:
    """List the backing services that the current settings cannot reach.

    Used to skip infrastructure-dependent tests instead of letting them fail
    with a DNS error when the suite runs outside the Docker network.

    Returns:
        list[str]: Display names of the unreachable services, empty when all of
            them are reachable.
    """
    settings_instance = settings
    candidates = (
        ("PostgreSQL", settings_instance.DATABASE_URL, 5432),
        ("Redis", settings_instance.REDIS_URL, 6379),
    )

    return [name for name, url, port in candidates if not _is_reachable(url, port)]


def database_is_connected() -> bool:
    """Check whether the shared database handle has an engine open.

    The end-to-end lifespan connects and disconnects the shared handle around
    each client fixture, so a test-scoped helper cannot assume it stays open for
    the whole session.

    Returns:
        bool: True when the shared database handle is usable right now.
    """
    return database._engine is not None


async def reset_users_table() -> None:
    """Empty the `users` table so each test starts from a known state.

    `TRUNCATE` rather than `DELETE` because it does not fire per-row triggers and
    resets the whole table in a single statement.

    Raises:
        RuntimeError: If the shared database handle has no engine open. Callers
            are expected to check `database_is_connected` first, since the
            end-to-end lifespan closes the handle between tests.
    """
    async with database.session() as session:
        await session.execute(text("TRUNCATE TABLE users CASCADE"))
        await session.commit()
