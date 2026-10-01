import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from src.config import settings
from src.shared.data.models.base_model import Base
from src.shared.data.models.example_model import ExampleModel  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def _escape_for_configparser(value: str) -> str:
    """Double percent signs so ConfigParser treats them literally.

    Alembic keeps the URL in an ini section parsed by ConfigParser, where `%`
    introduces an interpolation. A password containing `%` would otherwise make
    the later `get()` raise `InterpolationSyntaxError`, with no mention of the
    password in the message.

    Args:
        value: Raw value about to be written to the Alembic config.

    Returns:
        str: The value with every `%` doubled.
    """
    return value.replace("%", "%%")


config.set_main_option(
    "sqlalchemy.url", _escape_for_configparser(settings.DATABASE_URL)
)


target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in offline mode."""
    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations using the provided database connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations using an asynchronous database connection."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in online mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
