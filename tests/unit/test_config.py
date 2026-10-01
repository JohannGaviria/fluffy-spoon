from typing import Any

import pytest

from src.config import Settings

# Valid values for every setting that has no default, so a Settings instance can
# be built without touching the environment or the .env file.
REQUIRED_SAMPLE_VALUES: dict[str, Any] = {
    "APP_NAME": "Test API",
    "APP_SUMMARY": "Test summary.",
    "APP_DESCRIPTION": "Test description.",
    "DEBUG": True,
    "ENVIRONMENT": "development",
    "BACKEND_PORT": 8000,
    "BACKEND_WORKERS": 4,
    "CORS_ALLOW_ORIGINS": "http://localhost:8000",
    "CORS_ALLOW_CREDENTIALS": True,
    "POSTGRES_USER": "postgres",
    "POSTGRES_PASSWORD": "password",
    "POSTGRES_DB": "db",
    "POSTGRES_PORT": 5432,
    "DATABASE_URL": "postgresql+asyncpg://postgres:password@localhost:5432/db",
    "DB_POOL_SIZE": 10,
    "DB_MAX_OVERFLOW": 5,
    "DB_POOL_TIMEOUT": 30,
    "DB_ECHO": False,
    "REDIS_URL": "redis://localhost:6379/0",
    "REDIS_PORT": 6379,
    "REDIS_MAX_CONNECTIONS": 20,
    "REDIS_DECODE_RESPONSES": True,
}


def build_settings(**overrides: Any) -> Settings:
    """Build a Settings instance from the sample values, ignoring the .env file.

    Args:
        **overrides: Values that replace the corresponding sample values.

    Returns:
        Settings: The constructed instance.
    """
    return Settings(_env_file=None, **{**REQUIRED_SAMPLE_VALUES, **overrides})


class TestSecretsMasking:
    def test_should_not_expose_passwords_and_urls_in_repr(self) -> None:
        settings = build_settings()
        representation = repr(settings)

        for secret in (
            settings.POSTGRES_PASSWORD,
            settings.POSTGRES_TEST_PASSWORD,
            settings.DATABASE_URL,
            settings.DATABASE_URL_TEST,
            settings.REDIS_URL,
            settings.REDIS_URL_TEST,
        ):
            assert secret not in representation

    def test_should_still_expose_non_secret_values_in_repr(self) -> None:
        representation = repr(build_settings())

        assert "postgres" in representation
        assert "development" in representation


class TestApplicationMetadata:
    def test_should_default_the_version_to_the_pyproject_one(self) -> None:
        settings = build_settings()

        assert settings.APP_VERSION

    def test_should_accept_the_metadata_from_the_environment(self) -> None:
        settings = build_settings(APP_NAME="Books API")

        assert settings.APP_NAME == "Books API"


class TestSettingsParsing:
    def test_should_split_comma_separated_origins(self) -> None:
        settings = build_settings(
            CORS_ALLOW_ORIGINS="http://a.test, http://b.test",
        )

        assert settings.CORS_ALLOW_ORIGINS == ["http://a.test", "http://b.test"]

    def test_should_ignore_the_environment_file_when_told_to(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("ENVIRONMENT", "staging")

        settings = build_settings()

        assert settings.ENVIRONMENT == "development"

    def test_should_accept_a_list_for_origins(self) -> None:
        settings = build_settings(CORS_ALLOW_ORIGINS=["http://a.test"])

        assert settings.CORS_ALLOW_ORIGINS == ["http://a.test"]

    def test_should_reject_an_unknown_environment(self) -> None:
        with pytest.raises(ValueError, match="ENVIRONMENT"):
            build_settings(ENVIRONMENT="stagingg")
