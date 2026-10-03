from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from src.shared.api.schemas.response_schema import ErrorsResponseSchema
from src.shared.infrastructure.logging.structlog_logger import StructlogLogger

_logger = StructlogLogger(__name__)


def exception_handlers(app: FastAPI) -> None:

    @app.exception_handler(Exception)
    async def exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle an exception that no specific handler claimed.

        The message is generic on purpose. The text of an unexpected exception
        can carry SQL, connection strings, file paths or upstream payloads, so
        it is logged and never returned to the client.

        There is no debug escape hatch here on purpose: with DEBUG enabled
        FastAPI serves the full traceback itself and this handler is never
        reached, so adding one would be dead code.

        Neither the message nor the traceback is logged, for the same reason the
        previous handler avoids them: an unhandled exception can be a SQLAlchemy
        error, and `str()` of one carries the bound parameters of the statement,
        which for a write is the password hash. Only the class is recorded.

        Args:
            request (Request): The request object.
            exc (Exception): The exception.

        Returns:
            JSONResponse: The JSON response with a generic 500 message.
        """
        _logger.error(
            "Unhandled exception while processing request.",
            request_method=request.method,
            request_path=request.url.path,
            exception_type=type(exc).__name__,
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=jsonable_encoder(
                ErrorsResponseSchema(
                    message="An unexpected error occurred while processing the request.",
                ),
                exclude_none=True,
            ),
        )
