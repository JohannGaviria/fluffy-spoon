import structlog


class StructlogLogger:
    """Concrete logger backed by structlog.

    Wraps a structlog bound-logger so every call is routed through the
    processors configured in ``StructlogConfigureLogging.configure()``,
    which render every event as JSON. The ``debug`` flag only decides the
    level threshold, not the output format.

    Loggers are stateless, so a single module-level instance is enough and
    is cheaper than building one per object.

    Usage::

        logger = StructlogLogger(__name__)
        logger.info("user_created", user_id=str(user.id))
    """

    def __init__(self, name: str) -> None:
        """Initialize the logger bound to a single module.

        Args:
            name (str): Typically ``__name__`` of the calling module,
                used as the ``logger`` field in structured log output.
        """
        self._logger = structlog.get_logger(name)

    def debug(self, message: str, **kwargs: object) -> None:
        """Log a debug-level message.

        Args:
            message (str): The log message (mapped to structlog's ``event`` field).
            **kwargs: Arbitrary key-value pairs added as structured fields.
        """
        self._logger.debug(event=message, **kwargs)

    def info(self, message: str, **kwargs: object) -> None:
        """Log an info-level message.

        Args:
            message (str): The log message (mapped to structlog's ``event`` field).
            **kwargs: Arbitrary key-value pairs added as structured fields.
        """
        self._logger.info(event=message, **kwargs)

    def warning(self, message: str, **kwargs: object) -> None:
        """Log a warning-level message.

        Args:
            message (str): The log message (mapped to structlog's ``event`` field).
            **kwargs: Arbitrary key-value pairs added as structured fields.
        """
        self._logger.warning(event=message, **kwargs)

    def error(self, message: str, **kwargs: object) -> None:
        """Log an error-level message.

        Args:
            message (str): The log message (mapped to structlog's ``event`` field).
            **kwargs: Arbitrary key-value pairs added as structured fields.
        """
        self._logger.error(event=message, **kwargs)

    def critical(self, message: str, **kwargs: object) -> None:
        """Log a critical-level message.

        Args:
            message (str): The log message (mapped to structlog's ``event`` field).
            **kwargs: Arbitrary key-value pairs added as structured fields.
        """
        self._logger.critical(event=message, **kwargs)
