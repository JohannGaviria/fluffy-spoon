import tomllib
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BeforeValidator, Field
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


@lru_cache(maxsize=1)
def _get_project_version() -> str:
    """Read the project version from pyproject.toml.

    Cached because the file is parsed on every call otherwise, and the value
    cannot change while the process is running.

    Returns:
        str: The version declared in the `[project]` table.
    """
    pyproject_path = Path(__file__).resolve().parent.parent / "pyproject.toml"

    with pyproject_path.open("rb") as file:
        project = tomllib.load(file)

    return str(project["project"]["version"])


def _parse_comma_separated(value: object) -> object:
    """Splits a comma-separated string into a list of stripped values.

    Args:
        value: Raw value coming from the environment.

    Returns:
        object: The list of values, or the original value if it is not a string.
    """
    if not isinstance(value, str):
        return value
    return [item.strip() for item in value.split(",") if item.strip()]


class Settings(BaseSettings):
    """Application configuration settings."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Application metadata
    APP_NAME: str = Field(..., validation_alias="APP_NAME")
    APP_SUMMARY: str = Field(..., validation_alias="APP_SUMMARY")
    APP_DESCRIPTION: str = Field(..., validation_alias="APP_DESCRIPTION")
    APP_VERSION: str = _get_project_version()

    # Backend configuration
    DEBUG: bool = Field(..., validation_alias="DEBUG")
    ENVIRONMENT: Literal["development", "staging", "production"] = Field(
        ..., validation_alias="ENVIRONMENT"
    )
    BACKEND_PORT: int = Field(..., validation_alias="BACKEND_PORT")
    BACKEND_WORKERS: int = Field(..., validation_alias="BACKEND_WORKERS")
    CORS_ALLOW_ORIGINS: Annotated[
        list[str], NoDecode, BeforeValidator(_parse_comma_separated)
    ] = Field(..., validation_alias="CORS_ALLOW_ORIGINS")
    CORS_ALLOW_CREDENTIALS: bool = Field(..., validation_alias="CORS_ALLOW_CREDENTIALS")

    # Argon2 configuration
    ARGON2_TIME_COST: int = Field(..., validation_alias="ARGON2_TIME_COST")
    ARGON2_MEMORY_COST: int = Field(..., validation_alias="ARGON2_MEMORY_COST")
    ARGON2_PARALLELISM: int = Field(..., validation_alias="ARGON2_PARALLELISM")

    # PostgreSQL configuration
    POSTGRES_USER: str = Field(..., validation_alias="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field(
        ..., repr=False, validation_alias="POSTGRES_PASSWORD"
    )
    POSTGRES_DB: str = Field(..., validation_alias="POSTGRES_DB")
    POSTGRES_PORT: int = Field(..., validation_alias="POSTGRES_PORT")

    # Database configuration
    DATABASE_URL: str = Field(..., repr=False, validation_alias="DATABASE_URL")
    DB_POOL_SIZE: int = Field(..., validation_alias="DB_POOL_SIZE")
    DB_MAX_OVERFLOW: int = Field(..., validation_alias="DB_MAX_OVERFLOW")
    DB_POOL_TIMEOUT: int = Field(..., validation_alias="DB_POOL_TIMEOUT")
    DB_ECHO: bool = Field(..., validation_alias="DB_ECHO")

    # Redis configuration
    REDIS_URL: str = Field(..., repr=False, validation_alias="REDIS_URL")
    REDIS_PORT: int = Field(..., validation_alias="REDIS_PORT")
    REDIS_MAX_CONNECTIONS: int = Field(..., validation_alias="REDIS_MAX_CONNECTIONS")
    REDIS_DECODE_RESPONSES: bool = Field(..., validation_alias="REDIS_DECODE_RESPONSES")

    # Test infrastructure configuration
    # Separate instances, so the test suite never touches the development
    # database or cache. The hosts are the compose service names, so these
    # values only resolve from inside the Docker network.
    POSTGRES_TEST_USER: str = Field(
        default="postgres_test", validation_alias="POSTGRES_TEST_USER"
    )
    POSTGRES_TEST_PASSWORD: str = Field(
        default="password", repr=False, validation_alias="POSTGRES_TEST_PASSWORD"
    )
    POSTGRES_TEST_DB: str = Field(
        default="db_test", validation_alias="POSTGRES_TEST_DB"
    )
    POSTGRES_TEST_PORT: int = Field(default=5433, validation_alias="POSTGRES_TEST_PORT")
    DATABASE_URL_TEST: str = Field(
        default="postgresql+asyncpg://postgres_test:password@postgres-test:5432/db_test",
        repr=False,
        validation_alias="DATABASE_URL_TEST",
    )
    REDIS_TEST_PORT: int = Field(default=6380, validation_alias="REDIS_TEST_PORT")
    REDIS_URL_TEST: str = Field(
        default="redis://redis-test:6379/0",
        repr=False,
        validation_alias="REDIS_URL_TEST",
    )


@lru_cache(maxsize=1)
def _get_settings() -> Settings:
    """Get the application settings, building them on first use.

    The instance is created lazily and then cached, so importing this module
    never fails on its own: a misconfigured environment surfaces when a setting
    is first read, which keeps the failure tied to the code that needs it.

    Returns:
        Settings: The application settings instance.
    """
    return Settings()


settings = _get_settings()
