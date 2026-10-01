# Readme

One-liner: what the project does and who it is for / what problem it solves.

2-4 lines of context: why this project exists — stack practice, portfolio, real MVP, etc. Be direct, don't sell.

---

## Table of Contents

- [Technologies](#technologies)
- [Quick Start](#quick-start)
    - [Cloning the Repository](#cloning-the-repository)
    - [Dependency Management](#dependency-management)
    - [Running the Environment](#running-the-environment)
- [Architecture and Decisions](#architecture-and-decisions)
- [API Endpoints](#api-endpoints)
    - [Group 1, e.g: Authentication](#group-1-eg-authentication)
    - [Group 2](#group-2)
- [Testing](#testing)
- [Future Improvements](#future-improvements)
- [License](#license)

---

## Technologies

<!-- Optional badges (shields.io) or a simple list: ![Lang](https://img.shields.io/badge/...) -->

- Language / Framework:
- Database:
- Cache / Queues (if applicable):
- Testing:
- Infrastructure: Docker / docker-compose

---

## Quick Start

### Cloning the Repository

```bash
git clone git@github.com/JohannGaviria/project-name.git
cd project-name
```

Copy the environment variables file and fill in the local values:

```bash
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

### Dependency Management

[Poetry](https://python-poetry.org/) is used as the dependency manager and virtual environment tool.

#### Installing the project dependencies

```shell
poetry install --with dev,test # Or: make setup
```

> **Note:** running the command via `make` will also install the pre-commit hooks.

This creates an isolated virtual environment and installs all the dependencies defined in `../pyproject.toml`, including the development tools (`ruff`, `mypy`, `pytest`, etc.).

Dependency groups:

| Group  | Installed with | Contents                                            |
|--------|----------------|-----------------------------------------------------|
| `dev`  | `--with dev`   | ruff, mypy, pre-commit                              |
| `test` | `--with test`  | pytest and friends                                  |
| `prod` | `--with prod`  | gunicorn, only needed to build the production image |


### Running the Environment

#### Running the Environment without Docker

Run the API directly with Poetry and manage the external services (PostgreSQL, Redis, etc) separately:

**Requirements:**
- [Python 3.14](https://www.python.org/downloads/release/python-3140/)
- [PostgreSQL](https://www.postgresql.org/docs/)
- [Redis](https://redis.io/docs/latest/)

##### Starting the API

```shell
poetry run alembic upgrade head
poetry run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`. The interactive documentation is available at `http://localhost:8000/docs`.

> The default port will be `8000`, but it can be configured through environment variables.

#### Running the Environment with Docker

Docker compose starts all the required services simultaneously: the API, PostgreSQL, Redis, etc.

**Requirements:**
- [Docker](https://www.docker.com/), or Docker Engine + Compose plugin
- [Docker Compose](https://docs.docker.com/compose/)

##### Starting the API

```shell
docker compose --profile dev up --build # or: make up
```

The first run downloads the base images and builds the application image. Subsequent runs are significantly faster if the dependencies have not changed.

The API will be available at `http://localhost:8000`. The interactive documentation is available at `http://localhost:8000/docs`.

> The default port will be `8000`, but it can be configured through environment variables.

---

## Architecture and Decisions

[2-3 lines + simple diagram. Do not repeat the whole architecture here.]

```
src/
├── [layer 1]/   # [what it contains]
├── [layer 2]/   # [what it contains]
└── [layer 3]/   # [what it contains]
```

**Why [most relevant decision, e.g: this architecture / this pattern]:** [1-2 lines of the main reasoning.]

For a detailed explanation of the architecture and its decisions, see [ARCHITECTURE.md](ARCHITECTURE.md).

For the rest of the technical decisions and their trade-offs, see `DECISIONS.md` (not created yet).

---

## API Endpoints

### [Group 1, e.g: Authentication]

| Method | Endpoint      | Auth/Role | Description |
| ------ | ------------- | --------- | ----------- |
| `POST` | `/api/v1/...` | ...       | ...         |

### [Group 2]

| Method | Endpoint      | Auth/Role | Description |
| ------ | ------------- | --------- | ----------- |
| `GET`  | `/api/v1/...` | ...       | ...         |

---

## Testing

The tests are organized in three levels, each one in its own directory:

```
tests/
├── unit/          # No DB or Redis. Uses FakeRepositories. Very fast.
├── integration/   # Uses a real PostgreSQL instance. Tests repositories and concurrency.
└── e2e/           # Full HTTP flows against the running application.
```

- **Unit** → [what it covers, mocked dependencies]
- **Integration** → [what it covers, against which real infra]
- **E2E** → [what it covers]

The integration and E2E tests require the infrastructure services to be running; the unit tests have no external dependencies.

| Scope       | Makefile                      | Equivalent                                                                                                                 |
| ----------- | ----------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| All         | `make test`                   | `docker compose --profile test run --rm backend-test pytest tests -v`                                                      |
| Unit        | `make test-unit`              | `poetry run pytest tests/unit -v`                                                                                          |
| Integration | `make test-integration`       | `docker compose --profile test run --rm backend-test pytest tests/integration -v`                                          |
| No DB       | `make test-integration-no-db` | `poetry run pytest tests/integration -m "not db" -v`                                                                       |
| E2E         | `make test-e2e`               | `docker compose --profile test run --rm backend-test pytest tests/e2e -v`                                                  |
| Coverage    | `make test-coverage`          | `docker compose --profile test run --rm backend-test pytest tests --cov=src --cov-report=term-missing --cov-fail-under=70` |

For the testing strategy, test structure, coverage target and the full list of commands, see [TEST_STRATEGY.md](TEST_STRATEGY.md).

---

## Future Improvements

- [pending feature 1]
- [pending feature 2]
- [pending feature 3]

---

## License

Distributed under the **MIT** License. See [LICENSE](../LICENSE).

---

> Made with ♥️ by [JohannGaviria](https://github.com/JohannGaviria); always open to connecting for feedback, collaboration, or job opportunities.
