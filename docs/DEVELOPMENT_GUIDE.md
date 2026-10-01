# Development Guide
 
> Guide with the steps needed to run the project in a local environment: dependency installation, running the application with and without Docker, database migrations, cache management and code quality checks.

## Table of Contents

- [Cloning the Repository](#cloning-the-repository)
- [Dependency Management](#dependency-management)
    - [Installing Poetry](#installing-poetry)
    - [Installing the project dependencies](#installing-the-project-dependencies)
    - [Useful Poetry Commands](#useful-poetry-commands)
- [Running the Environment](#running-the-environment)
    - [Running the Environment without Docker](#running-the-environment-without-docker)
    - [Running the Environment with Docker](#running-the-environment-with-docker)
    - [Common Commands](#common-commands)
- [Database](#database)
    - [Direct Connection](#direct-connection)
    - [Migrations with Alembic](#migrations-with-alembic)
    - [Creating a new migration](#creating-a-new-migration)
- [Cache](#cache)
    - [Direct Connection](#direct-connection-1)
    - [Useful redis-cli commands](#useful-redis-cli-commands)
- [Testing](#testing)
    - [Tests with Docker (recommended)](#tests-with-docker-recommended)
    - [Tests without Docker (unit tests only)](#tests-without-docker-unit-tests-only)
    - [Combining the coverage reports](#combining-the-coverage-reports)
- [Linting and Type Checking](#linting-and-type-checking)
    - [Ruff (linter + formatter)](#ruff-linter--formatter)
    - [Mypy (static type checking)](#mypy-static-type-checking)
    - [Running everything together (pre-commit / CI)](#running-everything-together-pre-commit--ci)
    - [Pre-commit hooks (optional but recommended)](#pre-commit-hooks-optional-but-recommended)

---

## Cloning the Repository

```shell
git clone git@github.com/JohannGaviria/project-name.git
cd project-name
```

Copy the environment variables file and fill in the local values:

```shell
cp .env.example .env
```

| Variable                 | Description                                                                  | Example                                                                                                       |
|--------------------------|------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------|
| **Application metadata** | Used to build the OpenAPI docs.                                              |                                                                                                               |
| `APP_NAME`               | Title of the API shown in the OpenAPI docs and in the root endpoint.         | `Python Backend Starter`                                                                                      |
| `APP_SUMMARY`            | Short summary of the API shown in the OpenAPI docs.                          | `Reusable Python backend starter API.`                                                                        |
| `APP_DESCRIPTION`        | Long description of the API shown in the OpenAPI docs.                       | `Reusable Python backend starter template with Docker, PostgreSQL, Redis, testing, and code quality tooling.` |
| **Backend**              |                                                                              |                                                                                                               |
| `DEBUG`                  | Enables or disables debug mode.                                              | `True` / `False`                                                                                              |
| `ENVIRONMENT`            | Runtime environment of the application.                                      | `development`                                                                                                 |
| `BACKEND_PORT`           | Port the API listens on inside the container and is published on the host.   | `8000`                                                                                                        |
| `BACKEND_WORKERS`        | Number of Gunicorn worker processes (production stage).                      | `4`                                                                                                           |
| `CORS_ALLOW_ORIGINS`     | Allowed origins for CORS requests.                                           | `http://localhost:8000`                                                                                       |
| `CORS_ALLOW_CREDENTIALS` | Allows credentials to be included in CORS requests.                          | `True` / `False`                                                                                              |
| **PostgreSQL (dev)**     | Consumed by the `postgres` container.                                        |                                                                                                               |
| `POSTGRES_USER`          | User created by the `postgres` container.                                    | `postgres`                                                                                                    |
| `POSTGRES_PASSWORD`      | Password of that user. Required, the image refuses to initialize without it. | `password`                                                                                                    |
| `POSTGRES_DB`            | Database name created by the `postgres` container.                           | `db`                                                                                                          |
| `POSTGRES_PORT`          | Host port published for `postgres`.                                          | `5432`                                                                                                        |
| **Database (dev)**       |                                                                              |                                                                                                               |
| `DATABASE_URL`           | Connection string used by the application and by Alembic (SQLAlchemy Async). | `postgresql+asyncpg://postgres:password@postgres:5432/db`                                                     |
| `DB_POOL_SIZE`           | Maximum number of connections kept in the pool.                              | `10`                                                                                                          |
| `DB_MAX_OVERFLOW`        | Connections allowed above the pool size before the pool blocks.              | `5`                                                                                                           |
| `DB_POOL_TIMEOUT`        | Seconds to wait for a free connection before failing.                        | `30`                                                                                                          |
| `DB_ECHO`                | Logs every SQL statement executed by the engine.                             | `false`                                                                                                       |
| **Redis (dev)**          |                                                                              |                                                                                                               |
| `REDIS_URL`              | Redis connection URL.                                                        | `redis://redis:6379/0`                                                                                        |
| `REDIS_PORT`             | Host port published for `redis`.                                             | `6379`                                                                                                        |
| `REDIS_MAX_CONNECTIONS`  | Maximum size of the Redis connection pool.                                   | `20`                                                                                                          |
| `REDIS_DECODE_RESPONSES` | Decodes the Redis responses to `str` instead of `bytes`.                     | `true`                                                                                                        |
| **Test infrastructure**  | Only used by the `test` profile (`docker compose --profile test`).           |                                                                                                               |
| `POSTGRES_TEST_USER`     | User created by the `postgres-test` container.                               | `postgres_test`                                                                                               |
| `POSTGRES_TEST_PASSWORD` | Password of that user.                                                       | `password`                                                                                                    |
| `POSTGRES_TEST_DB`       | Database name created by the `postgres-test` container.                      | `db_test`                                                                                                     |
| `POSTGRES_TEST_PORT`     | Host port published for `postgres-test`.                                     | `5433`                                                                                                        |
| `DATABASE_URL_TEST`      | Overrides `DATABASE_URL` inside `backend-test`.                              | `postgresql+asyncpg://postgres_test:password@postgres-test:5432/db_test`                                      |
| `REDIS_TEST_PORT`        | Host port published for `redis-test`.                                        | `6380`                                                                                                        |
| `REDIS_URL_TEST`         | Overrides `REDIS_URL` inside `backend-test`.                                 | `redis://redis-test:6379/0`                                                                                   |

> The hosts in `DATABASE_URL` and `REDIS_URL` are the compose service names, so those values only resolve from inside the Docker network. To run the API without Docker, point them at `localhost`.

> The version exposed in the OpenAPI docs is not an environment variable: it is read from the `version` field of `[project]` in `pyproject.toml`.

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

Run the API directly with Poetry and manage the external services (PostgreSQL, Redis, etc) separately:

**Requirements:**
- [Python 3.14](https://www.python.org/downloads/release/python-3140/)
- [PostgreSQL](https://www.postgresql.org/docs/)
- [Redis](https://redis.io/docs/latest/)

#### Starting the API

```shell
poetry run alembic upgrade head
poetry run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`. The interactive documentation is available at `http://localhost:8000/docs`.

> The default port will be `8000`, but it can be configured through environment variables.

### Running the Environment with Docker

Docker Compose starts all the required services simultaneously: the API, PostgreSQL, Redis, etc.

**Requirements:**
- [Docker](https://www.docker.com/), or Docker Engine + Compose plugin
- [Docker Compose](https://docs.docker.com/compose/)

#### Starting the API

```shell
docker compose --profile dev up --build # or: make up
```

The first run downloads the base images and builds the application image. Subsequent runs are significantly faster if the dependencies have not changed.

The API will be available at `http://localhost:8000`. The interactive documentation is available at `http://localhost:8000/docs`.

> The default port will be `8000`, but it can be configured through environment variables.

#### Common Commands

```shell
# Run in the background
docker compose --profile dev up -d

# View logs for a specific service
docker compose --profile dev logs -f backend-dev
docker compose --profile dev logs -f postgres

# Follow the logs of every running service
docker compose logs -f # or: make logs

# Rebuild only the application image (e.g. after changing dependencies)
docker compose --profile dev build backend-dev

# Stop the dev and test services
docker compose --profile dev --profile test down # or: make down

# Stop the services and remove volumes and local images (deletes both databases)
docker compose --profile dev --profile test down -v --rmi local # or: make clean

# Remove only the test volumes, keeping the development database
docker compose --profile test down -v

# Check the status of all services
docker compose --profile dev ps
docker compose --profile test ps
```

---

## Database

Docker Compose runs **two completely separate PostgreSQL instances**, one per profile, each with its own volume. Running the tests therefore never touches the development database:

| Profile | Service         | Volume               | Host port | Database           |
| ------- | --------------- | -------------------- | --------- | ------------------ |
| `dev`   | `postgres`      | `postgres_data`      | `5432`    | `POSTGRES_DB`      |
| `test`  | `postgres-test` | `postgres_test_data` | `5433`    | `POSTGRES_TEST_DB` |

The `redis` and `redis-test` services follow the same pattern (`redis_data` on `6379`, `redis_test_data` on `6380`).

The `backend-test` service receives `DATABASE_URL` and `REDIS_URL` overridden with the `DATABASE_URL_TEST` and `REDIS_URL_TEST` values from `.env`, so the test suite transparently talks to the test instances. Alembic needs no separate variable: `alembic/env.py` reads the same `DATABASE_URL` and runs the migrations asynchronously.

### Direct Connection

```shell
# Development database, from the host (requires psql to be installed)
psql postgresql://postgres:password@localhost:5432/db

# Development database, from inside the container
docker compose --profile dev exec postgres psql -U postgres -d db

# Test database, from the host
psql postgresql://postgres:password@localhost:5433/db_test

# Test database, from inside the container
docker compose --profile test exec postgres-test psql -U postgres_test -d db_test
```

> Use the name and the port that match the profile you started. Both profiles can run at the same time because they do not share containers, volumes or ports.

### Migrations with Alembic

Alembic is used to version the database schema. All migrations are stored in `*/alembic/versions/` and are fully reversible.

> The following commands can be run both locally and from the Docker container.

#### Applying migrations

```shell
# Locally
poetry run alembic upgrade head

# From the container
docker compose --profile dev exec backend-dev alembic upgrade head
```

#### Reverting the last migration

```shell
# Locally
poetry run alembic downgrade -1

# From the container
docker compose --profile dev exec backend-dev alembic downgrade -1
```

#### Rolling back to a specific revision

```shell
# Locally
poetry run alembic downgrade <revision_id>

# From the container
docker compose --profile dev exec backend-dev alembic downgrade <revision_id>
```

#### Viewing the history

```shell
# Locally
poetry run alembic history --verbose

# From the container
docker compose --profile dev exec backend-dev alembic history --verbose
```

#### Showing the current revision

```shell
# Locally
poetry run alembic current

# From the container
docker compose --profile dev exec backend-dev alembic current
```

### Creating a new migration

Always generate the migrations from the SQLAlchemy models instead of writing them manually.

```shell
# Locally
poetry run alembic revision --autogenerate -m "add_notifications_table"

# From the container
docker compose --profile dev exec backend-dev alembic revision --autogenerate -m "add_notifications_table"
```

> Review the generated file in `*/alembic/versions/` before applying it and make sure the `downgrade()` function is correct.

---

## Cache

As with the database, the cache is isolated per profile: `redis` uses the `redis_data` volume on port `6379`, and `redis-test` uses `redis_test_data` on `6380`.

### Direct Connection

```shell
# Development cache, from the host (requires redis-cli to be installed)
redis-cli -h localhost -p 6379

# Development cache, from inside the container
docker compose --profile dev exec redis redis-cli

# Test cache, from the host
redis-cli -h localhost -p 6380

# Test cache, from inside the container
docker compose --profile test exec redis-test redis-cli
```

### Useful redis-cli commands

```shell
# Authenticate
AUTH password

# List all active keys
KEYS *

# Inspect a specific refresh token
GET cache:refresh_token:<token>

# Check the remaining TTL of a key
TTL cache:refresh_token:<token>

# Manually delete a key (useful during development)
DEL cache:refresh_token:<token>

# Show general server information
INFO server

# Clear database 0 (use with caution in production!)
FLUSHDB
```

---

## Testing

The project has three types of tests, organized in separate directories:

```
tests/
├── unit/          # No DB or Redis. Uses FakeRepositories. Very fast.
├── integration/   # Uses a real PostgreSQL instance. Tests repositories and concurrency.
└── e2e/           # Full HTTP flows against the running application.
```

### Tests with Docker (recommended)

Docker Compose runs the suite against the dedicated `postgres-test` and `redis-test` services, which have their own containers, volumes and ports. The development database and cache are never touched, so both profiles can run at the same time.

```shell
# Run all tests (unit + integration + e2e)
docker compose --profile test run --rm backend-test pytest tests -v # or: make test

# Run only unit tests
docker compose --profile test run --rm backend-test pytest tests/unit -v

# Run only integration tests
docker compose --profile test run --rm backend-test pytest tests/integration -v # or: make test-integration

# Run only e2e tests
docker compose --profile test run --rm backend-test pytest tests/e2e -v # or: make test-e2e

# Run with a coverage report (fails if the coverage drops below 70%)
docker compose --profile test run --rm backend-test pytest tests --cov=src --cov-report=term-missing --cov-fail-under=70 # or: make test-coverage

# Run a specific test by name
docker compose --profile test run --rm backend-test pytest -k "test_concurrent_book_confirmation"

# Stop on the first failure
docker compose --profile test run --rm backend-test pytest -x
```

`docker compose run` starts the `postgres-test` and `redis-test` dependencies automatically, so they do not need to be brought up beforehand. To keep them running in the background and then execute the suite against them:

```shell
docker compose --profile test up -d
docker compose --profile test run --rm backend-test pytest tests/integration -m db
docker compose --profile test run --rm backend-test pytest tests/e2e -m e2e
docker compose --profile test --profile dev down # or: make down
```

To discard the test database and start from a clean state, remove the test volumes:

```shell
docker compose --profile test down -v
```

> `make clean` removes the volumes of **both** profiles, so it also deletes the development database.

### Tests without Docker (unit tests only)

Unit tests have no external dependencies and can be run directly with Poetry:

```shell
# Run only unit tests
poetry run pytest tests/unit -v # or: make test-unit

# Run the integration tests that do not require a database
poetry run pytest tests/integration -m "not db" -v # or: make test-integration-no-db

# Collect the unit coverage data into tests/.coverage.unit
COVERAGE_FILE=tests/.coverage.unit poetry run pytest tests/unit --cov=src --cov-report= # or: make test-coverage-unit
```

> Watch mode is not available out of the box: `pytest-watch` is not declared in `pyproject.toml`. Add it first with `poetry add --group test pytest-watch` and then run `poetry run ptw tests/unit/`.

### Combining the coverage reports

Each suite writes its own coverage data file, and the final step combines them and enforces the threshold:

```shell
# Build the testing image before running the containerized suites
docker compose build backend-test # or: make build-test

# Collect the integration coverage data into tests/.coverage.integration*
docker compose --profile test run --rm -e COVERAGE_FILE=tests/.coverage.integration backend-test pytest tests/integration --cov=src --cov-report= # or: make test-coverage-integration

# Collect the e2e coverage data into tests/.coverage.e2e*
docker compose --profile test run --rm -e COVERAGE_FILE=tests/.coverage.e2e backend-test pytest tests/e2e --cov=src --cov-report= # or: make test-coverage-e2e

# Combine tests/.coverage.unit*, tests/.coverage.integration* and tests/.coverage.e2e*
poetry run coverage combine tests/ # or: make test-coverage-report
```

---

## Linting and Type Checking

### Ruff (linter + formatter)

```shell
# Check for linting errors
poetry run ruff check . # or: make lint

# Automatically fix issues Ruff can resolve
poetry run ruff check --fix . # or: make format

# Format the code (equivalent to black)
poetry run ruff format . # or: make format

# Check formatting without modifying files (useful in CI)
poetry run ruff format --check . # or: make check
```

### Mypy (static type checking)

```shell
# Check types across the whole project
poetry run mypy . # or: make check

# Check types of a specific module
poetry run mypy src/modules/books/

# Generate a type coverage report (writes any-exprs.txt and types-of-anys.txt)
poetry run mypy src/ --any-exprs-report .
```

### Running everything together (pre-commit / CI)

`make check` runs the same three verifications used by the CI pipeline:

```shell
poetry run ruff format --check . && poetry run ruff check . && poetry run mypy .
```

Or by using a single Makefile command:

```shell
# Automatically format and fix code
make format

# Check without modifying files
make check

# Linting only
make lint

# Run every pre-commit hook over all files
make pre-commit
```

### Pre-commit hooks (optional but recommended)

```shell
# Install hooks in the local repository
poetry run pre-commit install # or: make setup

# Run the hooks manually over all files
poetry run pre-commit run --all-files # or: make pre-commit
```

> **Note:** if you already ran `make setup`, the pre-commit hooks were installed automatically.
