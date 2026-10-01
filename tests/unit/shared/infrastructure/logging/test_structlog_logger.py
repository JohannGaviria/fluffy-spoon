from typing import Any
from unittest.mock import MagicMock

import pytest
import structlog

from src.shared.infrastructure.logging.structlog_logger import StructlogLogger

LEVELS = ("debug", "info", "warning", "error", "critical")


@pytest.fixture
def bound_logger(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Replace the structlog logger with a mock and hand it back.

    Returns:
        MagicMock: The mock that stands in for the structlog bound logger.
    """
    mock = MagicMock()
    monkeypatch.setattr(structlog, "get_logger", lambda _name: mock)
    return mock


class TestLevels:
    @pytest.mark.parametrize("level", LEVELS)
    def test_should_send_the_message_as_the_event_field(
        self,
        bound_logger: MagicMock,
        level: str,
    ) -> None:
        logger = StructlogLogger("src.tests")

        getattr(logger, level)("something happened")

        getattr(bound_logger, level).assert_called_once_with(event="something happened")

    @pytest.mark.parametrize("level", LEVELS)
    def test_should_forward_the_structured_fields(
        self,
        bound_logger: MagicMock,
        level: str,
    ) -> None:
        logger = StructlogLogger("src.tests")

        getattr(logger, level)("user_created", user_id="42", source="api")

        getattr(bound_logger, level).assert_called_once_with(
            event="user_created",
            user_id="42",
            source="api",
        )

    def test_should_bind_the_given_name_to_the_structlog_logger(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        names: list[Any] = []
        monkeypatch.setattr(structlog, "get_logger", names.append)

        StructlogLogger("src.module")

        assert names == ["src.module"]
