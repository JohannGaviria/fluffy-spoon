# Development Guide - Fluffy Spoon

> Guide to the steps needed to bring the project up in a local environment: dependency installation, running the application with and without Docker, database migrations, cache management and code quality checks.

## Table of Contents

- [Cloning the Repository](#cloning-the-repository)
- [Dependency Management](#dependency-management)
    - [Installing Poetry](#installing-poetry)
    - [Installing the Project Dependencies](#installing-the-project-dependencies)
    - [Useful Poetry Commands](#useful-poetry-commands)
- [Running the Environment](#running-the-environment)
    - [Running the Environment without Docker](#running-the-environment-without-docker)
    - [Running the Environment with Docker](#running-the-environment-with-docker)
- [Database](#database)
    - [Direct Connection](#direct-connection)
    - [Migrations with Alembic](#migrations-with-alembic)
    - [Creating a New Migration](#creating-a-new-migration)
- [Cache](#cache)
    - [Direct Connection](#direct-connection-1)
    - [Useful redis-cli Commands](#useful-redis-cli-commands)
- [Tests](#tests)
    - [Tests with Docker (recommended)](#tests-with-docker-recommended)
    - [Tests without Docker (unit tests only)](#tests-without-docker-unit-tests-only)
- [Linting and Type Checking](#linting-and-type-checking)
    - [Ruff (linter + formatter)](#ruff-linter--formatter)
    - [Mypy (static type checking)](#mypy-static-type-checking)
    - [Running Everything Together (pre-commit / CI)](#running-everything-together-pre-commit--ci)
    - [Pre-commit Hooks (optional but recommended)](#pre-commit-hooks-optional-but-recommended)

---

## Cloning the Repository

```shell
git clone git@github.com/JohannGaviria/fluffy-spoon.git
cd fluffy-spoon
```

Copy the environment variables file and fill in the local values:

```shell
cp .env.example .env
```

| Variable                 | Description                                                                  | Example                                                                                            |
|--------------------------|------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------|
| **Application metadata** | Used to build the OpenAPI docs.                                              |                                                                                                    |
| `APP_NAME`               | Title of the API shown in the OpenAPI docs and in the root endpoint.         | `Fluffy Spoon`                                                                                     |
| `APP_SUMMARY`            | Short summary of the API shown in the OpenAPI docs.                          | `REST API to manage an image gallery with light social interaction`                                |
| `APP_DESCRIPTION`        | Long description of the API shown in the OpenAPI docs.                       | `REST API to manage an image gallery with albums, light social interaction, comments and ratings.` |
| **Backend**              |                                                                              |                                                                                                    |
| `DEBUG`                  | Enables or disables debug mode.                                              | `True` / `False`                                                                                   |
| `ENVIRONMENT`            | Runtime environment of the application.                                      | `development`                                                                                      |
| `BACKEND_PORT`           | Port the API listens on inside the container and is published on the host.   | `8000`                                                                                             |
| `BACKEND_WORKERS`        | Number of Gunicorn worker processes (production stage).                      | `4`                                                                                                |
| `CORS_ALLOW_ORIGINS`     | Allowed origins for CORS requests.                                           | `http://localhost:8000`                                                                            |
| `CORS_ALLOW_CREDENTIALS` | Allows credentials to be included in CORS requests.                          | `True` / `False`                                                                                   |
| **PostgreSQL (dev)**     | Consumed by the `postgres` container.                                        |                                                                                                    |
| `POSTGRES_USER`          | User created by the `postgres` container.                                    | `postgres`                                                                                         |
| `POSTGRES_PASSWORD`      | Password of that user. Required, the image refuses to initialize without it. | `password`                                                                                         |
| `POSTGRES_DB`            | Database name created by the `postgres` container.                           | `fluffy_spoon`                                                                                     |
| `POSTGRES_PORT`          | Host port published for `postgres`.                                          | `5432`                                                                                             |
| **Database (dev)**       |                                                                              |                                                                                                    |
| `DATABASE_URL`           | Connection string used by the application and by Alembic (SQLAlchemy Async). | `postgresql+asyncpg://postgres:password@postgres:5432/fluffy_spoon`                                |
| `DB_POOL_SIZE`           | Maximum number of connections kept in the pool.                              | `10`                                                                                               |
| `DB_MAX_OVERFLOW`        | Connections allowed above the pool size before the pool blocks.              | `5`                                                                                                |
| `DB_POOL_TIMEOUT`        | Seconds to wait for a free connection before failing.                        | `30`                                                                                               |
| `DB_ECHO`                | Logs every SQL statement executed by the engine.                             | `false`                                                                                            |
| **Redis (dev)**          |                                                                              |                                                                                                    |
| `REDIS_URL`              | Redis connection URL.                                                        | `redis://redis:6379/0`                                                                             |
| `REDIS_PORT`             | Host port published for `redis`.                                             | `6379`                                                                                             |
| `REDIS_MAX_CONNECTIONS`  | Maximum size of the Redis connection pool.                                   | `20`                                                                                               |
| `REDIS_DECODE_RESPONSES` | Decodes the Redis responses to `str` instead of `bytes`.                     | `true`                                                                                             |
| **Test infrastructure**  | Only used by the `test` profile (`docker compose --profile test`).           |                                                                                                    |
| `POSTGRES_TEST_USER`     | User created by the `postgres-test` container.                               | `postgres_test`                                                                                    |
| `POSTGRES_TEST_PASSWORD` | Password of that user.                                                       | `password`                                                                                         |
| `POSTGRES_TEST_DB`       | Database name created by the `postgres-test` container.                      | `db_test`                                                                                          |
| `POSTGRES_TEST_PORT`     | Host port published for `postgres-test`.                                     | `5433`                                                                                             |
| `DATABASE_URL_TEST`      | Overrides `DATABASE_URL` inside `backend-test`.                              | `postgresql+asyncpg://postgres_test:password@postgres-test:5432/db_test`                           |
| `REDIS_TEST_PORT`        | Host port published for `redis-test`.                                        | `6380`                                                                                             |
| `REDIS_URL_TEST`         | Overrides `REDIS_URL` inside `backend-test`.                                 | `redis://redis-test:6379/0`                                                                        |

> The hosts in `DATABASE_URL` and `REDIS_URL` are the compose service names, so those values only resolve from inside the Docker network. To run the API without Docker, point them at `localhost`.
> The version exposed in the OpenAPI docs is not an environment variable: it is read from the `version` field of `[project]` in `pyproject.toml`.
> Each Argon2 parameter is stored inside the hash it produces, so changing these values does not invalidate the passwords already registered.

---

## Dependency Management

[Poetry](https://python-poetry.org/) is used as the dependency manager and virtual environment tool.

### Installing Poetry

Linux/macOS/WSL (Git Bash):

```shell
curl -sSL https://install.python-poetry.org | python3 -
```

Windows (PowerShell):

```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -
```

Verify that it is available in your PATH:

```shell
poetry --version
# Poetry (version 2.3.4)
```

### Installing the project dependencies

The `dev` and `test` dependency groups are declared as `optional = true` in `pyproject.toml`, so they must be requested explicitly:

```shell
poetry install --with dev,test
```

Or using the Makefile:

```shell
make setup
```

> **Note:** running this command will also install the pre-commit hooks.

This creates an isolated virtual environment and installs all the dependencies defined in `pyproject.toml`, including the development tools (`ruff`, `mypy`, `pytest`, etc.).

Dependency groups:

| Group  | Installed with | Contents                                            |
|--------|----------------|-----------------------------------------------------|
| `dev`  | `--with dev`   | ruff, mypy, pre-commit                              |
| `test` | `--with test`  | pytest and friends                                  |
| `prod` | `--with prod`  | gunicorn, only needed to build the production image |

### Useful Poetry Commands

```shell
# Add a production dependency
poetry add fastapi

# Add a development-only dependency
poetry add --group dev pytest-asyncio

# Show the dependency tree
poetry show --tree

# Update dependencies while respecting the constraints in pyproject.toml
poetry update
```

---

## Running the Environment

### Running the Environment without Docker

Run the API directly with Poetry and manage the external services (PostgreSQL, Redis, etc.) separately:

**Requirements:**
- [Python 3.12](https://www.python.org/downloads/release/python-3120/)
- [PostgreSQL](https://www.postgresql.org/docs/)
- [Redis](https://redis.io/docs/latest/)

#### Starting the API

```shell
poetry shell
alembic upgrade head
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`. The interactive documentation is available at `http://localhost:8000/docs`.

> The default port will be `8000`, but it can be configured through environment variables.

### Running the Environment with Docker

Docker Compose starts all the required services at the same time: the API, PostgreSQL, Redis, etc.

**Requirements:**
- [Docker](https://www.docker.com/), or Docker Engine + Compose plugin
- [Docker Compose](https://docs.docker.com/compose/)

#### Starting the API

```
docker compose --profile dev up --build # or: make up
```

The first run downloads the base images and builds the application image. Later runs are significantly faster if the dependencies have not changed.

The API will be available at `http://localhost:8000`. The interactive documentation is available at `http://localhost:8000/docs`.

> The default port will be `8000`, but it can be configured through environment variables.

#### Common Commands

```shell
# Run in the background
docker compose --profile dev up -d

# View the logs of a specific service
docker compose --profile dev logs -f backend-dev
docker compose --profile dev logs -f postgres

# Rebuild only the application image (after changing dependencies)
docker compose --profile dev build backend-dev

# Stop all services
docker compose --profile dev down  # or: make down

# Stop services and remove volumes (deletes the database)
docker compose --profile dev down -v

# Check the status of the services
docker compose ps
```

---

## Database

### Direct Connection

```shell
# Locally (requires psql to be installed)
psql postgresql://postgres:password@postgres:5432/fluffy_spoon

# From the container
docker compose --profile dev exec postgres psql -U postgres -d fluffy_spoon
```

> Use `--profile dev` to connect to the development database or `--profile test` to connect to the test database.

### Migrations with Alembic

Alembic is used to version the database schema. All migrations are stored in `*/alembic/versions/` and are fully reversible.

> The following commands can be run both locally and from the Docker container.

#### Applying Migrations

```shell
# Locally
alembic upgrade head

# From the container
docker compose --profile dev exec backend-dev alembic upgrade head
```

#### Reverting the Last Migration

```shell
# Locally
alembic downgrade -1

# From the container
docker compose --profile dev exec backend-dev alembic downgrade -1
```

#### Going Back to a Specific Revision

```shell
# Locally
alembic downgrade <revision_id>

# From the container
docker compose --profile dev exec backend-dev alembic downgrade <revision_id>
```

#### Viewing the History

```shell
# Locally
alembic history --verbose

# From the container
docker compose --profile dev exec backend-dev alembic history --verbose
```

#### Showing the Current Revision

```shell
# Locally
alembic current

# From the container
docker compose --profile dev exec backend-dev alembic current
```

### Creating a New Migration

Always generate the migrations from the SQLAlchemy models instead of writing them by hand.

```shell
# Locally
alembic revision --autogenerate -m "add_albums_table"

# From the container
docker compose --profile dev exec backend-dev alembic revision --autogenerate -m "add_albums_table"
```

> Review the generated file in `*/alembic/versions/` before applying it and make sure the `downgrade()` function is correct.

---

## Cache

### Direct Connection

```shell
# Locally (requires redis-cli to be installed)
redis-cli -h localhost -p 6379

# From inside the container
docker compose --profile dev exec redis redis-cli
```

### Useful redis-cli Commands

```shell
# Authenticate (if Redis requires it)
AUTH password

# List all active keys
KEYS *

# Inspect a revoked access token
GET cache:access_token:revoked:<jti>

# Check the remaining TTL of a key
TTL cache:access_token:revoked:<jti>

# Delete a key manually (useful in development)
DEL cache:access_token:revoked:<jti>

# Inspect a cached album query
GET cache:albums:list:<query_hash>

# Show general server information
INFO server

# Flush database 0 (use with care in production!)
FLUSHDB
```

---

## Tests

The project has three types of tests, organized in separate directories:

```
tests/
├── unit/          # No DB or Redis. Fakes and mocks stand in for the adapters. Very fast.
├── integration/   # Real PostgreSQL and Redis. Tests the shared infrastructure.
└── e2e/           # Full HTTP flows against the running application.
```

### Tests with Docker (recommended)

Docker Compose uses an isolated database for the tests, avoiding any interference with the development database.

```shell
# Run all tests (unit + integration + e2e)
docker compose --profile test run --rm backend-test pytest # or: make test

# Run only unit tests
docker compose --profile test run --rm backend-test pytest tests/unit/ -v # or: make test-unit

# Run only integration tests
docker compose --profile test run --rm backend-test pytest tests/integration/ -v # or: make test-integration

# Run only e2e tests
docker compose --profile test run --rm backend-test pytest tests/e2e/ -v # or: make test-e2e

# Run with a coverage report
docker compose --profile test run --rm backend-test pytest --cov=src --cov-report=term-missing # or: make test-coverage

# Run a specific test by name
docker compose --profile test run --rm backend-test pytest -k "test_readiness"

# Stop on the first failure
docker compose --profile test run --rm backend-test pytest -x
```

To run integration and end-to-end tests, the infrastructure services must be running first:

```shell
docker compose --profile test up -d
pytest tests/integration/ -m db
pytest tests/e2e/ -m e2e
```

### Tests without Docker (unit tests only)

Unit tests have no external dependencies and can be run directly with Poetry:

```shell
# Run only unit tests
poetry run pytest tests/unit/ -v # or: make test-unit

# Run with a coverage report
poetry run pytest tests/unit/ --cov=src --cov-report=term-missing # or: make test-coverage

# Run in watch mode (requires pytest-watch)
poetry run ptw tests/unit/
```

---

## Linting and Type Checking

### Ruff (linter + formatter)

```shell
# Check for linting errors
poetry run ruff check . # or: make lint

# Automatically fix issues Ruff can resolve
poetry run ruff check . --fix # or: make format

# Format the code (equivalent to black)
poetry run ruff format . # or: make format

# Check formatting without modifying files (useful in CI)
poetry run ruff format . --check # or: make check
```

### Mypy (static type checking)

```shell
# Check types across the whole project
poetry run mypy src/ # or: make check

# Check types of a specific module
poetry run mypy src/modules/auth/

# Generate a type coverage report
poetry run mypy src/ --any-exprs-report .
```

### Running Everything Together (pre-commit / CI)

```shell
ruff check . && ruff format . --check && mypy src/
```

Or using a single Makefile command:

```shell
# Automatically format and fix code
make format

# Check without modifying files
make check

# Linting and type checking
make lint
```

### Pre-commit Hooks (optional but recommended)

```shell
# Install hooks in the local repository
pre-commit install # or: make setup
```

> **Note:** if you already ran `make setup`, the pre-commit hooks were installed automatically.
