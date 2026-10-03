import pytest
from httpx import AsyncClient

from src.config import settings
from src.shared.data.database import database
from src.shared.data.redis_client import redis_client

# The lifespan connects to PostgreSQL and Redis, so these tests need the same
# infrastructure as the integration suite. The root conftest skips them when it
# is not reachable, which keeps a bare `pytest` run green on the host.
pytestmark = [pytest.mark.e2e, pytest.mark.db]


class TestRoot:
    async def test_should_welcome_when_root_is_called(
        self,
        client: AsyncClient,
    ) -> None:
        response = await client.get("/")

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert settings.APP_NAME in body["message"]
        assert settings.APP_VERSION in body["message"]


class TestLiveness:
    async def test_should_report_alive_when_the_process_is_serving(
        self,
        client: AsyncClient,
    ) -> None:
        response = await client.get("/health")

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert body["data"] == {"status": "alive"}

    async def test_should_stay_alive_when_every_dependency_is_down(
        self,
        client: AsyncClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # Liveness must not depend on PostgreSQL or Redis: an orchestrator that
        # restarts the app when they are down turns a recoverable outage into an
        # outage.
        async def failing_ping() -> bool:
            raise ConnectionError("everything is down")

        monkeypatch.setattr(database, "ping", failing_ping)
        monkeypatch.setattr(redis_client, "ping", failing_ping)

        response = await client.get("/health")

        assert response.status_code == 200


class TestReadiness:
    async def test_should_report_ready_when_every_dependency_answers(
        self,
        client: AsyncClient,
    ) -> None:
        response = await client.get("/health/ready")

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert body["data"] == {
            "status": "ready",
            "database": True,
            "redis": True,
        }

    async def test_should_report_503_when_the_database_is_down(
        self,
        client: AsyncClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        async def failing_ping() -> bool:
            raise ConnectionError("postgres is down")

        monkeypatch.setattr(database, "ping", failing_ping)

        response = await client.get("/health/ready")

        assert response.status_code == 503
        assert response.json()["data"] == {
            "status": "not_ready",
            "database": False,
            "redis": True,
        }

    async def test_should_report_503_when_redis_is_down(
        self,
        client: AsyncClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        async def failing_ping() -> bool:
            raise ConnectionError("redis is down")

        monkeypatch.setattr(redis_client, "ping", failing_ping)

        response = await client.get("/health/ready")

        assert response.status_code == 503
        assert response.json()["data"] == {
            "status": "not_ready",
            "database": True,
            "redis": False,
        }


class TestCorrelationId:
    async def test_should_generate_a_correlation_id_when_the_header_is_absent(
        self,
        client: AsyncClient,
    ) -> None:
        response = await client.get("/health")

        assert response.headers["X-Correlation-ID"]

    async def test_should_echo_the_correlation_id_when_the_header_is_present(
        self,
        client: AsyncClient,
    ) -> None:
        correlation_id = "test-correlation-id"

        response = await client.get(
            "/health",
            headers={"X-Correlation-ID": correlation_id},
        )

        assert response.headers["X-Correlation-ID"] == correlation_id


class TestApplicationMetadata:
    async def test_should_expose_the_application_metadata(
        self,
        client: AsyncClient,
    ) -> None:
        response = await client.get("/openapi.json")

        assert response.status_code == 200
        info = response.json()["info"]
        assert info["title"] == settings.APP_NAME
        assert info["version"] == settings.APP_VERSION
