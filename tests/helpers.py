"""Helpers shared by the test suite."""

import socket
from urllib.parse import urlsplit

from src.config import settings

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
