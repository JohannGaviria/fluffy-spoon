from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, status
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.config import settings
from src.modules.auth.api.exceptions.auth_exception_handlers import (
    auth_exception_handlers,
)
from src.modules.auth.api.routes.auth_router import router as auth_router
from src.shared.api.exceptions.exception_handlers import exception_handlers
from src.shared.api.middleware.correlation_id_middleware import (
    CorrelationIdMiddleware,
)
from src.shared.api.schemas.response_schema import SuccessResponseSchema
from src.shared.data.database import database
from src.shared.data.redis_client import redis_client
from src.shared.infrastructure.logging.structlog_configure_logging import (
    StructlogConfigureLogging,
)
from src.shared.infrastructure.logging.structlog_logger import StructlogLogger

_logger = StructlogLogger(__name__)


async def _is_reachable(ping: Callable[[], Awaitable[bool]]) -> bool:
    """Run a dependency ping and treat any failure as unreachable.

    A health check must answer even when the dependency is down, so the
    driver errors are converted into a False instead of propagating and
    turning the endpoint into a 500.

    Args:
        ping: The coroutine function that pings the dependency.

    Returns:
        bool: True when the dependency answered, False otherwise.
    """
    try:
        return await ping()
    except Exception:
        _logger.warning("Dependency ping failed.", exc_info=True)
        return False


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Application lifespan context manager for managing database and Redis connections.

    This context manager ensures that the database and Redis connections are properly
    established and closed when the application starts and stops.
    """
    # Startup: open database and Redis connections once per process. The connects
    # sit inside the `try` so a failure part-way through startup still releases
    # whatever was already opened. Both `disconnect()` methods are idempotent, so
    # calling them for a dependency that never connected is a no-op.
    try:
        database.connect()
        redis_client.connect()

        yield
    finally:
        # Shutdown: close database and Redis connections once per process.
        await redis_client.disconnect()
        await database.disconnect()


app = FastAPI(
    title=settings.APP_NAME,
    summary=settings.APP_SUMMARY,
    description=settings.APP_DESCRIPTION,
    debug=settings.DEBUG,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)


# Configure logging using structlog
StructlogConfigureLogging.configure(debug=settings.DEBUG)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOW_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Includes the middleware for the API endpoints
app.add_middleware(CorrelationIdMiddleware)


# Includes the exception handlers for the API endpoints
auth_exception_handlers(app)
exception_handlers(app)


# Includes the routers for the API endpoints
app.include_router(auth_router)


@app.get(
    path="/",
    tags=["System"],
    summary="Root Endpoint",
    description="Returns a welcome message.",
)
async def root() -> JSONResponse:
    """Root endpoint that returns a welcome message.

    Returns:
        dict: A dictionary containing a welcome message.
    """
    return JSONResponse(
        content=jsonable_encoder(
            SuccessResponseSchema(
                message=f"Welcome to the {settings.APP_NAME}, version {settings.APP_VERSION}!",
            ),
            exclude_none=True,
        ),
        status_code=status.HTTP_200_OK,
    )


@app.get(
    path="/health",
    tags=["System"],
    summary="Liveness Endpoint",
    description=(
        "Confirms the process is up and serving requests. Does not check "
        "dependencies, so an outage in PostgreSQL or Redis never restarts the "
        "application. Use /health/ready to check dependencies."
    ),
)
async def liveness_check() -> JSONResponse:
    """Liveness check: the process is running and able to answer.

    Deliberately does not touch PostgreSQL or Redis. A liveness probe that
    fails while a dependency is down makes an orchestrator restart the app for
    a problem a restart cannot fix, so dependency checks belong to the
    readiness endpoint instead.

    Returns:
        JSONResponse: Always a 200 response, since reaching this handler
            already proves the process is serving.
    """
    return JSONResponse(
        content=jsonable_encoder(
            SuccessResponseSchema(
                message="The server is running.",
                data={"status": "alive"},
            ),
        ),
        status_code=status.HTTP_200_OK,
    )


@app.get(
    path="/health/ready",
    tags=["System"],
    summary="Readiness Endpoint",
    description=(
        "Checks whether the application can serve traffic by verifying that "
        "PostgreSQL and Redis are reachable."
    ),
)
async def readiness_check() -> JSONResponse:
    """Readiness check: every dependency answers.

    This is the endpoint to point load balancers and rolling updates at. It
    answers 503 while a dependency is down so traffic is routed elsewhere
    instead of hitting an app that cannot serve requests.

    Returns:
        JSONResponse: A 200 response when both dependencies answer, a 503
            otherwise, with the per-dependency detail in the payload.
    """
    database_status = await _is_reachable(database.ping)
    redis_status = await _is_reachable(redis_client.ping)
    is_ready = database_status and redis_status

    payload = {
        "status": "ready" if is_ready else "not_ready",
        "database": database_status,
        "redis": redis_status,
    }

    return JSONResponse(
        content=jsonable_encoder(
            SuccessResponseSchema(
                message=f"Readiness status: {payload['status']}",
                data=payload,
            ),
        ),
        status_code=(
            status.HTTP_200_OK if is_ready else status.HTTP_503_SERVICE_UNAVAILABLE
        ),
    )
