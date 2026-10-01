import io
import json
import logging
import sys
from collections.abc import Callable, Iterator

import pytest
import structlog

from src.shared.infrastructure.logging.structlog_configure_logging import (
    StructlogConfigureLogging,
)
from src.shared.infrastructure.logging.structlog_logger import StructlogLogger

NOISY_LOGGERS = ("uvicorn.access", "watchfiles.main")


class LogCapture:
    """A buffer fed by the formatter the application configured.

    Attributes:
        raw (str): Everything written to the buffer so far.
    """

    def __init__(self, buffer: io.StringIO) -> None:
        self._buffer = buffer

    @property
    def raw(self) -> str:
        """Return: Everything written to the buffer so far."""
        return self._buffer.getvalue()

    @property
    def lines(self) -> list[str]:
        """Return: The non-empty lines written to the buffer."""
        return [line for line in self.raw.splitlines() if line.strip()]

    def record(self) -> dict:
        """Return: The single rendered log record, parsed as JSON."""
        assert len(self.lines) == 1, f"expected one log line, got: {self.lines}"
        parsed: dict = json.loads(self.lines[0])
        return parsed


@pytest.fixture(autouse=True)
def restore_logging() -> Iterator[None]:
    """Snapshot and restore the global logging and structlog state.

    Yields:
        None: Control passes to the test with the state snapshotted.
    """
    root = logging.getLogger()
    handlers = list(root.handlers)
    level = root.level
    noisy_levels = {name: logging.getLogger(name).level for name in NOISY_LOGGERS}
    structlog_config = structlog.get_config().copy()

    yield

    root.handlers[:] = handlers
    root.setLevel(level)
    for name, noisy_level in noisy_levels.items():
        logging.getLogger(name).setLevel(noisy_level)
    structlog.configure(**structlog_config)


@pytest.fixture
def capture() -> Callable[..., LogCapture]:
    """Return a callable that configures logging and captures what it renders.

    Returns:
        Callable: Accepts the `debug` flag, configures structlog, attaches a
            buffer using the configured formatter and returns it.
    """

    def _capture(debug: bool = False) -> LogCapture:
        StructlogConfigureLogging.configure(debug=debug)
        buffer = io.StringIO()
        handler = logging.StreamHandler(buffer)
        handler.setFormatter(logging.getLogger().handlers[0].formatter)
        logging.getLogger().addHandler(handler)
        return LogCapture(buffer)

    return _capture


class TestLevels:
    def test_should_use_debug_level_when_debug_is_enabled(self) -> None:
        StructlogConfigureLogging.configure(debug=True)

        assert logging.getLogger().level == logging.DEBUG

    def test_should_use_info_level_when_debug_is_disabled(self) -> None:
        StructlogConfigureLogging.configure(debug=False)

        assert logging.getLogger().level == logging.INFO

    def test_should_drop_debug_events_when_debug_is_disabled(
        self, capture: Callable[..., LogCapture]
    ) -> None:
        logs = capture(debug=False)

        StructlogLogger("src.tests").debug("should be filtered out")

        assert logs.raw == ""

    def test_should_keep_debug_events_when_debug_is_enabled(
        self, capture: Callable[..., LogCapture]
    ) -> None:
        logs = capture(debug=True)

        StructlogLogger("src.tests").debug("kept")

        assert logs.record()["event"] == "kept"


class TestHandlers:
    def test_should_replace_the_root_handlers_with_a_single_one(self) -> None:
        StructlogConfigureLogging.configure()

        assert len(logging.getLogger().handlers) == 1

    def test_should_write_to_stdout(self) -> None:
        StructlogConfigureLogging.configure()

        handler = logging.getLogger().handlers[0]
        assert isinstance(handler, logging.StreamHandler)
        assert handler.stream is sys.stdout

    def test_should_install_a_processor_formatter(self) -> None:
        StructlogConfigureLogging.configure()

        formatter = logging.getLogger().handlers[0].formatter

        assert isinstance(formatter, structlog.stdlib.ProcessorFormatter)

    @pytest.mark.parametrize("name", NOISY_LOGGERS)
    def test_should_silence_the_noisy_dependency_loggers(self, name: str) -> None:
        StructlogConfigureLogging.configure()

        assert logging.getLogger(name).level == logging.WARNING


class TestRendering:
    def test_should_render_structlog_events_as_json(
        self, capture: Callable[..., LogCapture]
    ) -> None:
        logs = capture()

        StructlogLogger("src.tests").info("user_created", user_id="42")

        record = logs.record()
        assert record["event"] == "user_created"
        assert record["level"] == "info"
        assert record["logger"] == "src.tests"
        assert record["user_id"] == "42"
        assert record["timestamp"]

    def test_should_render_third_party_stdlib_logs_as_json(
        self, capture: Callable[..., LogCapture]
    ) -> None:
        logs = capture()

        logging.getLogger("third_party").warning("something happened")

        record = logs.record()
        assert record["event"] == "something happened"
        assert record["level"] == "warning"
        assert record["logger"] == "third_party"

    def test_should_merge_the_bound_contextvars(
        self, capture: Callable[..., LogCapture]
    ) -> None:
        logs = capture()
        structlog.contextvars.bind_contextvars(correlation_id="abc-123")

        StructlogLogger("src.tests").info("request_finished")

        assert logs.record()["correlation_id"] == "abc-123"

        structlog.contextvars.clear_contextvars()
