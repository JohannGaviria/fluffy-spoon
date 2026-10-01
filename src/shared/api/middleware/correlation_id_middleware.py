from uuid import uuid4

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    HEADER_NAME = "X-Correlation-ID"

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Dispatch the request to the next middleware or application.

        Args:
            request: The incoming HTTP request.
            call_next: The next middleware or application.

        Returns:
            The HTTP response.
        """
        correlation_id = request.headers.get(self.HEADER_NAME) or str(uuid4())

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            correlation_id=correlation_id,
        )

        response = await call_next(request)
        response.headers[self.HEADER_NAME] = correlation_id

        return response
