import logging
import sys

import structlog


class StructlogConfigureLogging:
    @staticmethod
    def configure(debug: bool = False) -> None:
        """Configure structlog for JSON-structured logging.

        Sets up structlog with a chain of processors that:
        - Add the log level to each event
        - Add the logger name (module) to each event
        - Add an ISO-8601 UTC timestamp to each event
        - Render the final event as a JSON string

        The same processors are also applied to stdlib log records coming from
        third-party libraries, so every line stays JSON.

        Args:
            debug: When True, lower the threshold to DEBUG; when False, keep it
                at INFO (production mode). The output format is JSON either way.
        """
        log_level = logging.DEBUG if debug else logging.INFO

        # Shared processors applied to BOTH structlog-native calls and stdlib
        # log records forwarded through ProcessorFormatter.
        shared_processors: list[structlog.types.Processor] = [
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
        ]

        # stdlib logging — capture third-party library logs and route them
        # through structlog's ProcessorFormatter so they also emit JSON.
        stdlib_handler = logging.StreamHandler(sys.stdout)
        stdlib_handler.setFormatter(
            structlog.stdlib.ProcessorFormatter(
                processors=[
                    structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                    structlog.processors.JSONRenderer(),
                ],
                foreign_pre_chain=shared_processors,
            )
        )

        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        root_logger.addHandler(stdlib_handler)
        root_logger.setLevel(log_level)

        # Silence overly verbose loggers from dependencies.
        for noisy in ("uvicorn.access", "watchfiles.main"):
            logging.getLogger(noisy).setLevel(logging.WARNING)

        # structlog configuration.
        structlog.configure(
            processors=[
                *shared_processors,
                structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
            ],
            wrapper_class=structlog.make_filtering_bound_logger(log_level),
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )
