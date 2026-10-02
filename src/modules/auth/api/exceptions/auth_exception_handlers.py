from fastapi import FastAPI

from src.modules.auth.api.exceptions.user_exception_handlers import (
    register_user_exception_handlers,
)
from src.shared.infrastructure.logging.structlog_logger import StructlogLogger

_logger = StructlogLogger(__name__)


def auth_exception_handlers(app: FastAPI) -> None:
    """Handles exceptions related to authentication."""
    register_user_exception_handlers(app)
