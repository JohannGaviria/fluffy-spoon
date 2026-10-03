# Fluffy Spoon

REST API to manage an image gallery with light social interaction. Users can register an account, upload images individually or group them into albums, and interact with other users' content through ratings (1–5) and comments.

It is a **monolith with layered architecture** built as a practical implementation of a modern backend stack (FastAPI, async SQLAlchemy, PostgreSQL and Redis). The focus is on applying clear domain rules —resource ownership, public/private visibility, rating uniqueness— and sound engineering practices: tests by level, cache with hit/miss, versioned migrations, direct file upload to S3 and reproducible deployment with Docker Compose.

> **Status:** the project is in its foundation stage. The application bootstrap, configuration, health endpoints, exception handling, structured logging, persistence and cache infrastructure are in place, and `auth` is the first module under construction. The albums, images, comments and ratings capabilities are the target scope described in the [requirements specification](docs/REQUIREMENTS_SPECIFICATION.md).

## Table of Contents

- [Technologies](#technologies)
- [Quick Start](#quick-start)
    - [Cloning the Repository](#cloning-the-repository)
    - [Dependency Management](#dependency-management)
    - [Running the Environment](#running-the-environment)
- [Architecture and Decisions](#architecture-and-decisions)
- [API Endpoints](#api-endpoints)
    - [Authentication](#authentication)
    - [Albums](#albums)
    - [Images](#images)
    - [Comments](#comments)
    - [Ratings](#ratings)
    - [System](#system)
- [Tests](#tests)
- [Future Improvements](#future-improvements)
- [License](#license)

## Technologies

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white)![Alembic](https://img.shields.io/badge/Alembic-5C6BC0?style=for-the-badge)![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)![Amazon S3](https://img.shields.io/badge/Amazon%20S3-569A31?style=for-the-badge&logo=amazons3&logoColor=white)![PyJWT](https://img.shields.io/badge/PyJWT-000000?style=for-the-badge&logo=jsonwebtokens&logoColor=white)![Argon2](https://img.shields.io/badge/Argon2-8D6E63?style=for-the-badge)![Structlog](https://img.shields.io/badge/Structlog-2E86DE?style=for-the-badge)![Ruff](https://img.shields.io/badge/Ruff-D7FF64?style=for-the-badge&logo=ruff&logoColor=black)![Mypy](https://img.shields.io/badge/Mypy-2A6DB2?style=for-the-badge&logo=mypy&logoColor=white)![Pytest](https://img.shields.io/badge/Pytest-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white)![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)![Docker Compose](https://img.shields.io/badge/Docker%20Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-2088FF?style=for-the-badge&logo=githubactions&logoColor=white)

---

## Quick Start

### Cloning the Repository

```bash
git clone git@github.com/JohannGaviria/fluffy-spoon.git
cd fluffy-spoon
```

Copy the environment variables file and fill in the local values:

```bash
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
| **Argon2**               | Password hashing parameters consumed by the Argon2 adapter.                  |                                                                                                    |
| `ARGON2_TIME_COST`       | Number of passes over the memory on every hash.                              | `3`                                                                                                |
| `ARGON2_MEMORY_COST`     | Memory used on every hash, in KiB.                                           | `65536`                                                                                            |
| `ARGON2_PARALLELISM`     | Number of parallel lanes used on every hash.                                 | `4`                                                                                                |
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

### Running the Environment

#### Running the Environment without Docker

Run the API directly with Poetry and manage the external services (PostgreSQL, Redis, etc.) separately:

**Requirements:**
- [Python 3.14](https://www.python.org/downloads/release/python-3140/)
- [PostgreSQL](https://www.postgresql.org/docs/)
- [Redis](https://redis.io/docs/latest/)

##### Starting the API

```shell
poetry shell
alembic upgrade head
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`. The interactive documentation is available at `http://localhost:8000/docs`.

> The default port will be `8000`, but it can be configured through environment variables.
#### Running the Environment with Docker

Docker Compose starts all the required services at the same time: the API, PostgreSQL, Redis, etc.

**Requirements:**
- [Docker](https://www.docker.com/), or Docker Engine + Compose plugin
- [Docker Compose](https://docs.docker.com/compose/)

##### Starting the API

```
docker compose up --profile dev --build # or: make up
```

The first run downloads the base images and builds the application image. Later runs are significantly faster if the dependencies have not changed.

The API will be available at `http://localhost:8000`. The interactive documentation is available at `http://localhost:8000/docs`.

> The default port will be `8000`, but it can be configured through environment variables.

---

## Architecture and Decisions

The application is a **monolith with layered architecture**, organized by functional module. Each module under `src/modules/` declares its own API, applies its business rules in `business/`, persists through `data/` and delegates external concerns to `infrastructure/`, keeping the rules decoupled from PostgreSQL, Redis and S3. Cross-cutting capabilities live in `src/shared/`, which uses **the same layer names**, so the vocabulary does not change between the two trees.

```
src/
├── modules/                # Business capabilities, one folder per module
│   ├── auth/               # Registration, login and logout
│   │   ├── api/            # Routers, schemas, dependencies and HTTP wiring
│   │   ├── business/       # Services, dtos and business rules
│   │   ├── data/           # Models, repositories and queries
│   │   ├── enums/          # Enumerations owned by the module
│   │   ├── exceptions/     # Exceptions owned by the module
│   │   └── infrastructure/ # Adapters to external services (S3, Argon2, JWT)
│   ├── albums/             # Album management and their visibility
│   ├── images/             # Direct upload to S3 and image queries
│   ├── comments/           # Comments on images
│   └── ratings/            # Ratings (1–5) on images
└── shared/                 # Cross-cutting capabilities, same layer names
│   ├── api/                # Exception handlers and middleware
│   ├── business/           # Base exception types
│   ├── data/               # Database engine, cache client, session, base model and migrations
│   └── infrastructure/     # Cache and logging adapters
│
├── main.py                 # Application entry point (FastAPI)
└── config.py               # Environment variable configuration
```

**Why this architecture:** a self-contained module can be read, tested and evolved without leaving its folder, and separating the business rules from the infrastructure details makes it possible to swap concrete pieces (e.g. object storage) without touching the business logic. A capability only reaches `shared/` once at least two modules need it, and `shared/` never holds the tables: each module owns its own models in its own `data/`.

> **Current status:** the foundation is in place (bootstrap, configuration, health endpoints, exception handling, logging, persistence, cache) and `auth` is the first module under construction. The albums, images, comments and ratings capabilities are the target scope defined in the requirements, not built code yet. See [Architecture](docs/ARCHITECTURE.md) for the full picture.

For a detailed explanation of the architecture and its decisions, see [Architecture](docs/ARCHITECTURE.md).

For the rest of the technical decisions and their trade-offs, see [Technical Decisions](docs/TECHNICAL_DECISIONS.md).

---

## API Endpoints

All routes require authentication through the `access_token` (JWT). Image upload is done in two steps: a **presigned S3 URL** is requested and the upload is confirmed to create the definitive record.

> Only the `System` endpoints below are implemented today. The other tables describe the target scope from the [requirements](docs/REQUIREMENTS_SPECIFICATION.md) and will be filled in as each module is built.

### Authentication

| Method | Endpoint                | Auth/Role | Description                                  |
|--------|-------------------------|-----------|----------------------------------------------|
| `POST` | `/api/v1/auth/register` | No        | Register a new user.                         |
| `POST` | `/api/v1/auth/login`    | No        | Log in; returns the `access_token`.          |
| `POST` | `/api/v1/auth/logout`   | Auth      | Log out; revokes the current `access_token`. |

### Albums

| Method   | Endpoint                    | Auth/Role | Description                                        |
|----------|-----------------------------|-----------|----------------------------------------------------|
| `POST`   | `/api/v1/albums`            | Auth      | Create an album (owned by the authenticated user). |
| `GET`    | `/api/v1/albums`            | Auth      | Query and filter albums according to visibility.   |
| `PATCH`  | `/api/v1/albums/{album_id}` | Auth      | Update an album of your own.                       |
| `DELETE` | `/api/v1/albums/{album_id}` | Auth      | Delete an album of your own.                       |

### Images

| Method   | Endpoint                    | Auth/Role | Description                                                                   |
|----------|-----------------------------|-----------|-------------------------------------------------------------------------------|
| `POST`   | `/api/v1/images/upload-url` | Auth      | Request a presigned S3 URL; validates metadata and returns the `storage_key`. |
| `POST`   | `/api/v1/images/confirm`    | Auth      | Confirm the upload to S3 and create the definitive image record.              |
| `GET`    | `/api/v1/images`            | Auth      | Query and filter images according to visibility and `album_id`.               |
| `PATCH`  | `/api/v1/images/{image_id}` | Auth      | Update an image of your own.                                                  |
| `DELETE` | `/api/v1/images/{image_id}` | Auth      | Delete an image of your own (and its comments/ratings).                       |

### Comments

| Method   | Endpoint                             | Auth/Role | Description                     |
|----------|--------------------------------------|-----------|---------------------------------|
| `POST`   | `/api/v1/images/{image_id}/comments` | Auth      | Publish a comment on an image.  |
| `GET`    | `/api/v1/images/{image_id}/comments` | Auth      | Query the comments of an image. |
| `PATCH`  | `/api/v1/comments/{comment_id}`      | Auth      | Update a comment of your own.   |
| `DELETE` | `/api/v1/comments/{comment_id}`      | Auth      | Delete a comment of your own.   |

### Ratings

| Method   | Endpoint                            | Auth/Role | Description                                            |
|----------|-------------------------------------|-----------|--------------------------------------------------------|
| `POST`   | `/api/v1/images/{image_id}/ratings` | Auth      | Rate an image with a `score` between 1 and 5.          |
| `GET`    | `/api/v1/images/{image_id}/ratings` | Auth      | Query the `rating_count` and `rating_avg` of an image. |
| `PATCH`  | `/api/v1/ratings/{rating_id}`       | Auth      | Update a rating of your own.                           |
| `DELETE` | `/api/v1/ratings/{rating_id}`       | Auth      | Delete a rating of your own.                           |

### System

| Method | Endpoint        | Description                                                                              |
|--------|-----------------|------------------------------------------------------------------------------------------|
| `GET`  | `/`             | Welcome message with the application name and version.                                   |
| `GET`  | `/health`       | Liveness. Always 200 while the process serves; does not touch PostgreSQL or Redis.       |
| `GET`  | `/health/ready` | Readiness. 200 when both dependencies answer, 503 otherwise, with per-dependency detail. |
| `GET`  | `/docs`         | Swagger UI.                                                                              |
| `GET`  | `/openapi.json` | OpenAPI schema.                                                                          |

---

## Tests

Tests are organized in three levels, each in its own directory, mirroring the structure of `src/`:

```
tests/
├── unit/          # No DB or Redis. Fakes and mocks stand in for the adapters. Very fast.
├── integration/   # Real PostgreSQL and Redis. Tests the shared infrastructure.
└── e2e/           # Full HTTP flows against the running application.
```

- **Unit** → Business rules and use cases in isolation; infrastructure is replaced by fakes and mocks. No external dependencies.
- **Integration** → The shared infrastructure against a real PostgreSQL and Redis (engine, session, cache adapter, client).
- **E2E** → Complete HTTP flows against the running application.

Integration and E2E tests require the infrastructure services to be running; unit tests have no external dependencies.

| Scope       | Makefile                | Equivalent                                                                         |
|-------------|-------------------------|------------------------------------------------------------------------------------|
| All         | `make test`             | `docker compose --profile test run --rm backend-test pytest`                       |
| Unit        | `make test-unit`        | `poetry run pytest tests/unit/ -v`                                                 |
| Integration | `make test-integration` | `docker compose --profile test run --rm backend-test pytest tests/integration/ -v` |
| E2E         | `make test-e2e`         | `docker compose --profile test run --rm backend-test pytest tests/e2e/ -v`         |
| Coverage    | `make test-coverage`    | `pytest --cov=src --cov-report=term-missing`                                       |

For the testing strategy, test structure, coverage target and the full list of commands, see [Test Strategy](docs/TEST_STRATEGY.md).

---

## Future Improvements

- **Event-Driven** approach to detach images when an album is deleted (`AlbumDeleted` event, asynchronous processing and eventual consistency), recorded in ADR-001.
- **User profile** management (updating name/password), mentioned in the system actors but not yet covered by functional requirements.
- Ranking of the highest-rated images and additional search filters on `GET /api/v1/images`.

---

## License

Distributed under the **MIT** License. See [LICENSE](#).

---

> Made with ♥️ by [JohannGaviria](https://github.com/JohannGaviria); always open to connecting for feedback, collaboration, or job opportunities.