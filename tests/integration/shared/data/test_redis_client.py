import pytest

from src.shared.data.redis_client import RedisClient

pytestmark = pytest.mark.db


class TestRedisClient:
    async def test_should_connect_when_connect_is_called(self):
        client = RedisClient()

        client.connect()

        assert await client.ping() is True

        await client.disconnect()

    async def test_should_be_idempotent_when_connect_is_called_twice(self):
        client = RedisClient()

        client.connect()
        first_client = client.client
        client.connect()
        second_client = client.client

        assert first_client is second_client

        await client.disconnect()

    async def test_should_raise_runtime_error_when_client_accessed_before_connect(
        self,
    ):
        client = RedisClient()

        with pytest.raises(RuntimeError):
            _ = client.client

    async def test_should_be_idempotent_when_disconnect_is_called_without_connect(
        self,
    ):
        client = RedisClient()

        await client.disconnect()

    async def test_should_be_idempotent_when_disconnect_is_called_twice(self):
        client = RedisClient()
        client.connect()

        await client.disconnect()
        await client.disconnect()

    async def test_should_reset_internal_state_when_disconnect_is_called(self):
        client = RedisClient()
        client.connect()

        await client.disconnect()

        with pytest.raises(RuntimeError):
            _ = client.client

    async def test_should_allow_reconnect_when_connect_is_called_after_disconnect(
        self,
    ):
        client = RedisClient()
        client.connect()
        await client.disconnect()

        client.connect()

        assert await client.ping() is True

        await client.disconnect()

    async def test_should_return_true_when_ping_succeeds(self):
        client = RedisClient()
        client.connect()

        result = await client.ping()

        assert result is True

        await client.disconnect()
