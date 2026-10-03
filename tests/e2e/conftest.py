from collections.abc import AsyncIterator

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from src.main import app


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    """Provide an HTTP client bound to the ASGI app, lifespan included.

    `ASGITransport` on its own does not run the ASGI lifespan, so the manager
    is what makes startup and shutdown actually execute and the backing
    services get connected.

    `raise_app_exceptions=False` because a real server answers an unhandled
    exception with the response its error middleware built and carries on, while
    the transport re-raises by default. Without it the tests could not assert the
    500 body a caller would actually receive.

    Yields:
        AsyncClient: A client whose requests run through the full application.
    """
    async with LifespanManager(app):
        transport = ASGITransport(app=app, raise_app_exceptions=False)
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as http_client:
            yield http_client
