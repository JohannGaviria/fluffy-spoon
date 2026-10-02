from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from src.modules.auth.exceptions.user_exception import (
    InvalidPasswordException,
    UserAlreadyExistsException,
    UserRepositoryException,
)
from src.shared.api.schemas.response_schema import ErrorsResponseSchema
from src.shared.infrastructure.logging.structlog_logger import StructlogLogger

_logger = StructlogLogger(__name__)


def register_user_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(UserAlreadyExistsException)
    async def user_already_exists_exception_handler(
        request: Request, exc: UserAlreadyExistsException
    ) -> JSONResponse:
        """User already exists exception handler.

        Args:
            request (Request): The request object.
            exc (UserAlreadyExistsException): The UserAlreadyExistsException exception.

        Returns:
            JSONResponse: The JSON response with the appropriate status code and message.
        """
        _logger.warning(
            "User already exists exception occurred while processing request.",
            request_method=request.method,
            request_path=request.url.path,
            exception_message=str(exc),
        )
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=jsonable_encoder(
                ErrorsResponseSchema(
                    message=str(exc),
                ),
                exclude_none=True,
            ),
        )

    @app.exception_handler(UserRepositoryException)
    async def user_repository_exception_handler(
        request: Request, exc: UserRepositoryException
    ) -> JSONResponse:
        """User repository exception handler.

        Args:
            request (Request): The request object.
            exc (UserRepositoryException): The UserRepositoryException exception.

        Returns:
            JSONResponse: The JSON response with the appropriate status code and message.
        """
        _logger.error(
            "User repository exception occurred while processing request.",
            request_method=request.method,
            request_path=request.url.path,
            exception_message=exc,
            error=exc.error,
            exc_info=True,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=jsonable_encoder(
                ErrorsResponseSchema(
                    message=str(exc),
                    details=exc.error,
                ),
                exclude_none=True,
            ),
        )

    @app.exception_handler(InvalidPasswordException)
    async def user_invalid_password_exception_handler(
        request: Request, exc: InvalidPasswordException
    ) -> JSONResponse:
        """Invalid password exception handler.

        Args:
            request (Request): The request object.
            exc (InvalidPasswordException): The InvalidPasswordException exception.

        Returns:
            JSONResponse: The JSON response with the appropriate status code and message.
        """
        _logger.warning(
            "Invalid password exception occurred while processing request.",
            request_method=request.method,
            request_path=request.url.path,
            exception_message=str(exc),
        )

        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=jsonable_encoder(
                ErrorsResponseSchema(
                    message=str(exc),
                    details=exc.error,
                ),
                exclude_none=True,
            ),
        )
