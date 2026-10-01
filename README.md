# Python Backend Starter

Reusable FastAPI backend template: Docker, PostgreSQL, Redis, Alembic migrations, structured logging, a three-level test suite and CI/CD pipelines already wired together.

It exists to avoid rebuilding the same scaffolding on every new service. There is no demo domain on purpose — what you get is the infrastructure layer, so you can drop in your models and use cases without first fighting the plumbing.

---

## Table of Contents

- [Technologies](#technologies)
- [Quick Start](#quick-start)
    - [Cloning the Repository](#cloning-the-repository)
    - [Dependency Management](#dependency-management)
    - [Running the Environment](#running-the-environment)
- [Architecture and Decisions](#architecture-and-decisions)
- [API Endpoints](#api-endpoints)
- [Testing](#testing)
- [Code Quality](#code-quality)
- [CI/CD and Secrets](#cicd-and-secrets)
- [Project Structure](#project-structure)
- [License](#license)

---

## Technologies

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![REST API](https://img.shields.io/badge/REST_API-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Swagger](https://img.shields.io/badge/Swagger-85EA2D?style=for-the-badge&logo=swagger&logoColor=black)
![Uvicorn](https://img.shields.io/badge/Uvicorn-499848?style=for-the-badge&logoColor=white)
![Gunicorn](https://img.shields.io/badge/Gunicorn-499848?style=for-the-badge&logo=gunicorn&logoColor=white)
![Pydantic](https://img.shields.io/badge/Pydantic-E92024?style=for-the-badge&logo=pydantic&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-CC2927?style=for-the-badge&logo=python&logoColor=white)
![Alembic](https://img.shields.io/badge/Alembic-3D3D3D?style=for-the-badge&logoColor=white)
![PyJWT](https://img.shields.io/badge/PyJWT-000000?style=for-the-badge&logo=jsonwebtokens&logoColor=white)
![Structlog](https://img.shields.io/badge/Structlog-000000?style=for-the-badge&logo=logstash&logoColor=white)
![Poetry](https://img.shields.io/badge/Poetry-60A5FA?style=for-the-badge&logo=poetry&logoColor=white)
![Ruff](https://img.shields.io/badge/Ruff-000000?style=for-the-badge&logo=ruff&logoColor=white)
![mypy](https://img.shields.io/badge/mypy-233564?style=for-the-badge&logoColor=white)
![pre-commit](https://img.shields.io/badge/pre--commit-F9F3E6?style=for-the-badge&logo=precommit&logoColor=000)
![Makefile](https://img.shields.io/badge/Makefile-000000?style=for-the-badge&logo=gnu&logoColor=white)
![PyTest](https://img.shields.io/badge/PyTest-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=for-the-badge&logo=githubactions&logoColor=white)
![CI/CD](https://img.shields.io/badge/CI%2FCD-000000?style=for-the-badge&logo=github&logoColor=white)
![semantic-release](https://img.shields.io/badge/semantic--release-24292F?style=for-the-badge&logo=semantic--release&logoColor=000)

---

## Quick Start

### Cloning the Repository

```bash
git clone git@github.com:JohannGaviria/python-backend-starter.git
cd python-backend-starter
```

Copy the environment variables file:

```bash
cp .env.example .env
```

The defaults in `.env.example` are already coherent for the Docker setup, so the stack runs without editing anything.

| Group                   | Variable                 | Description                                                 | Example                                                                  |
|-------------------------|--------------------------|-------------------------------------------------------------|--------------------------------------------------------------------------|
| **Application**         | `APP_NAME`               | Title of the API in the OpenAPI docs and the root endpoint. | `Python Backend Starter`                                                 |
|                         | `APP_SUMMARY`            | Short summary shown in the OpenAPI docs.                    | `Reusable Python backend starter API.`                                   |
|                         | `APP_DESCRIPTION`        | Long description shown in the OpenAPI docs.                 | `Reusable Python backend starter template...`                            |
| **Backend**             | `DEBUG`                  | Enables debug mode.                                         | `True` / `False`                                                         |
|                         | `ENVIRONMENT`            | Runtime environment of the application.                     | `development`                                                            |
|                         | `BACKEND_PORT`           | Port the API listens on and is published on the host.       | `8000`                                                                   |
|                         | `BACKEND_WORKERS`        | Gunicorn worker processes (production stage).               | `4`                                                                      |
|                         | `CORS_ALLOW_ORIGINS`     | Allowed origins, comma separated.                           | `http://localhost:8000`                                                  |
|                         | `CORS_ALLOW_CREDENTIALS` | Whether credentials may be included in CORS requests.       | `True` / `False`                                                         |
| **PostgreSQL**          | `POSTGRES_USER`          | User created by the `postgres` container.                   | `postgres`                                                               |
|                         | `POSTGRES_PASSWORD`      | Password of that user.                                      | `password`                                                               |
|                         | `POSTGRES_DB`            | Database name.                                              | `db`                                                                     |
|                         | `POSTGRES_PORT`          | Host port published for `postgres`.                         | `5432`                                                                   |
| **Database**            | `DATABASE_URL`           | Connection string used by the app and by Alembic.           | `postgresql+asyncpg://postgres:password@postgres:5432/db`                |
|                         | `DB_POOL_SIZE`           | Maximum connections kept in the pool.                       | `10`                                                                     |
|                         | `DB_MAX_OVERFLOW`        | Connections allowed above the pool size.                    | `5`                                                                      |
|                         | `DB_POOL_TIMEOUT`        | Seconds to wait for a free connection.                      | `30`                                                                     |
|                         | `DB_ECHO`                | Logs every SQL statement.                                   | `false`                                                                  |
| **Redis**               | `REDIS_URL`              | Redis connection URL.                                       | `redis://redis:6379/0`                                                   |
|                         | `REDIS_PORT`             | Host port published for `redis`.                            | `6379`                                                                   |
|                         | `REDIS_MAX_CONNECTIONS`  | Maximum size of the Redis pool.                             | `20`                                                                     |
|                         | `REDIS_DECODE_RESPONSES` | Decodes responses to `str` instead of `bytes`.              | `true`                                                                   |
| **Test infrastructure** | `POSTGRES_TEST_USER`     | User created by the `postgres-test` container.              | `postgres_test`                                                          |
|                         | `POSTGRES_TEST_PASSWORD` | Password of that user.                                      | `password`                                                               |
|                         | `POSTGRES_TEST_DB`       | Database name.                                              | `db_test`                                                                |
|                         | `POSTGRES_TEST_PORT`     | Host port published for `postgres-test`.                    | `5433`                                                                   |
|                         | `DATABASE_URL_TEST`      | Overrides `DATABASE_URL` inside `backend-test`.             | `postgresql+asyncpg://postgres_test:password@postgres-test:5432/db_test` |
|                         | `REDIS_TEST_PORT`        | Host port published for `redis-test`.                       | `6380`                                                                   |
|                         | `REDIS_URL_TEST`         | Overrides `REDIS_URL` inside `backend-test`.                | `redis://redis-test:6379/0`                                              |

> The hosts in `DATABASE_URL` and `REDIS_URL` are the compose service names, so they only resolve **inside the Docker network**. To run the API without Docker, point them at `localhost`.

> The version in the OpenAPI docs is not an environment variable: it is read from `version` in `[project]` of `pyproject.toml`, so there is a single source of truth.

> The `_TEST` variables are only used by the `test` profile (`docker compose --profile test`), which runs against isolated instances so a test run never touches your development data.

### Dependency Management

[Poetry](https://python-poetry.org/) manages dependencies and the virtual environment.

```bash
poetry install --with dev,test   # or: make setup
```

> `make setup` additionally installs the pre-commit hooks.

Dependency groups:

| Group  | Installed with | Contents                                            |
|--------|----------------|-----------------------------------------------------|
| `dev`  | `--with dev`   | ruff, mypy, pre-commit                              |
| `test` | `--with test`  | pytest and friends                                  |
| `prod` | `--with prod`  | gunicorn, only needed to build the production image |

### Running the Environment

#### With Docker

**Requirements:** Docker with the Compose plugin.

```bash
docker compose --profile dev up --build   # or: make up
```

The first run pulls the base images and builds the application; later runs are much faster.

- API: `http://localhost:8000`
- Interactive docs: `http://localhost:8000/docs`

The `dev` stage runs Uvicorn with `--reload` and applies migrations on startup. Other targets:

```bash
make logs    # follow logs
make down    # stop dev and test containers
make clean   # stop and remove containers, volumes and local images
```

#### Without Docker

**Requirements:** Python 3.14, PostgreSQL, Redis running locally.

```bash
poetry run alembic upgrade head
poetry run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Remember to point `DATABASE_URL` and `REDIS_URL` at `localhost`.

---

## Architecture and Decisions

```
src/
├── config.py                  # Settings loaded once, secrets masked in repr()
├── main.py                    # App factory wiring, lifespan, endpoints
└── shared/
    ├── domain/                # Framework-free business rules
    │   └── exceptions/        # BaseDomainException and its subtypes
    ├── infrastructure/        # Adapters to external systems
    │   ├── cache/             # RedisClient (connection) + RedisCache (generic adapter)
    │   ├── logging/           # structlog configuration and logger wrapper
    │   └── persistence/       # Database, Alembic, declarative models
    └── presentation/          # The HTTP boundary
        ├── exceptions/        # Exception handlers
        ├── middleware/        # Correlation ID
        └── schemas/           # Success and error response envelopes
```

**Why this layering:** dependencies point inward. `presentation` and `infrastructure` know about `domain`, never the reverse, so business rules can be tested without a database and swapping Redis for something else touches one folder. Each layer has a single reason to change.

Three decisions worth knowing before you build on it:

- **Liveness and readiness are separate.** `GET /health` only proves the process answers, and `GET /health/ready` checks PostgreSQL and Redis. A liveness probe that fails when a dependency is down makes an orchestrator restart the app for something a restart cannot fix. Point liveness probes at `/health` and traffic routers at `/health/ready`.
- **Cache failures are typed.** `CacheUnavailableException` means the backend is unreachable and the caller may retry; `CacheException` means the request or a bug is at fault. They map to 503 and 500 respectively, and the first one is logged with the key while the client only gets a generic message.
- **Unhandled errors never leak.** The catch-all handler logs the original exception and returns a generic message, because exception text can carry SQL, connection strings or file paths. With `DEBUG` on, FastAPI serves the full traceback itself.

For the reasoning in more depth, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## API Endpoints

| Method | Endpoint        | Description                                                                             |
| ------ | --------------- | --------------------------------------------------------------------------------------- |
| `GET`  | `/`             | Welcome message with the application name and version.                                  |
| `GET`  | `/health`       | Liveness. Always 200 while the process serves; does not touch PostgreSQL or Redis.      |
| `GET`  | `/health/ready` | Readiness. 200 when both dependencies answer, 503 otherwise, with per-dependency detail. |
| `GET`  | `/docs`         | Swagger UI.                                                                             |
| `GET`  | `/openapi.json` | OpenAPI schema.                                                                          |

Every response carries an `X-Correlation-ID` header. Send your own and it is echoed back and attached to every log line of that request, which is what makes a request traceable across services.

<details>
<summary>Example responses</summary>

`GET /`

```json
{
  "status": "success",
  "message": "Welcome to the Python Backend Starter, version 1.0.0!"
}
```

`GET /health/ready` when a dependency is down

```json
{
  "status": "success",
  "message": "Readiness status: not_ready",
  "data": { "status": "not_ready", "database": true, "redis": false }
}
```

</details>

---

## Testing

Three levels, each in its own directory:

```
tests/
├── unit/          # No external services. Fakes for engine, pool and Redis client.
├── integration/   # Real PostgreSQL and Redis, inside the Docker network.
└── e2e/           # Full HTTP flows through the ASGI app, lifespan included.
```

Tests that need infrastructure carry the `db` marker. On the host those hosts do not resolve, so instead of failing with a confusing `socket.gaierror`, the suite **skips** them with an actionable reason. Run them through Docker to actually exercise them.

| Scope       | Command                    | Equivalent                                                                          |
| ----------- | -------------------------- | ----------------------------------------------------------------------------------- |
| All         | `make test`                | `docker compose --profile test run --rm backend-test pytest tests -v`               |
| Unit        | `make test-unit`           | `poetry run pytest tests/unit -v`                                                   |
| Integration | `make test-integration`    | `docker compose --profile test run --rm backend-test pytest tests/integration -v`   |
| No DB       | `make test-integration-no-db` | `poetry run pytest tests/integration -m "not db" -v`                             |
| E2E         | `make test-e2e`            | `docker compose --profile test run --rm backend-test pytest tests/e2e -v`           |
| Coverage    | `make test-coverage`       | Full suite with `--cov=src` and a 70% threshold                                     |

The coverage threshold is enforced at 70%. CI goes further: it collects unit, integration and E2E coverage **separately**, uploads them as artifacts, then combines them for a single report — so a line is not counted twice and the total reflects every test that ran.

For the full strategy, see [docs/TEST_STRATEGY.md](docs/TEST_STRATEGY.md).

---

## Code Quality

| Command           | What it does                                    |
| ----------------- | ----------------------------------------------- |
| `make check`      | Ruff format check, Ruff lint, mypy              |
| `make lint`       | Ruff only                                       |
| `make format`     | Ruff with `--fix` plus formatting               |
| `make pre-commit` | Every hook over all files                       |

`make check` is exactly what the CI lint job runs, so a green local check means a green lint job. The pre-commit hooks run the same three tools, so most style problems never reach a commit.

---

## CI/CD and Secrets

Three workflows ship with the template. **None of them requires a secret to run the CI pipeline** — the most common question when adopting a template is which secrets to create, so here is the exact answer.

| Workflow            | Trigger                          | Secrets required                                   |
| ------------------- | -------------------------------- | -------------------------------------------------- |
| `ci.yml`            | push / PR on `main` and `develop`, or manual | **None**                                  |
| `release.yml`       | **Manual only** (opt-in)         | `RELEASE_TOKEN`                                    |
| `publish-image.yml` | Push of a tag matching `v*`      | `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`            |

### `ci.yml` — no secrets

Lint, unit, integration and E2E jobs, then a combined coverage report. It uses only the automatic `GITHUB_TOKEN` that GitHub injects into every workflow, with `contents: read`. Nothing to configure: clone the repository and it runs.

### `RELEASE_TOKEN` — GitHub PAT for semantic-release

A **Personal Access Token** used to check out the full history and to run semantic-release, which derives the next version from commit messages, writes `CHANGELOG.md`, updates the version in `pyproject.toml` and creates the GitHub release.

> **Why a PAT instead of the built-in `GITHUB_TOKEN`:** GitHub does not start workflow runs from pushes made with the automatic token. Since `publish-image.yml` triggers on the `v*` tags that semantic-release creates, using `GITHUB_TOKEN` would break that chain and no image would ever be published. A PAT is what closes the loop.

To create it: **Settings → Developer settings → Personal access tokens**. It needs write access to repository contents, and — if you keep the release-notes-as-PR flow — pull requests and issues as well. The permissions the workflow declares are `contents: write`, `pull-requests: write` and `issues: write`; grant the equivalent on the token.

**The release workflow ships disabled on purpose.** A fresh clone has no `RELEASE_TOKEN`, so triggering it automatically on every push would only produce a red build. To enable it, set the secret and change the trigger in `.github/workflows/release.yml`:

```yaml
on:
  workflow_run:
    workflows: ["CI Pipeline"]
    types: [completed]
    branches: [main]
```

That way a release is only attempted after CI has passed. Until then, run it by hand from the Actions tab.

### `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` — Docker Hub

Used to log in and push the image built from the `production` target. The username also builds the image name, so the published repository is `<DOCKERHUB_USERNAME>/<repo-name>`.

`DOCKERHUB_TOKEN` should be a Docker Hub **access token**, not the account password: **Account settings → Personal access tokens**, with read and write.

Behaviour worth knowing:

- Tags follow the release tag: `v1.2.3` produces `:v1.2.3`.
- A **pre-release** tag (anything containing a `-`, e.g. `v1.2.3-beta.1`) does **not** move `:latest`; a normal tag does.
- The image is scanned with Trivy for `HIGH` and `CRITICAL` findings. The scan reports but does not fail the build (`exit-code: "0"`), so a new CVE surfaces in the log without blocking a release. Tighten that to `"1"` once you want it enforced.

---

## Project Structure

```
.
├── .github/workflows/     # ci.yml, release.yml, publish-image.yml
├── alembic.ini            # Points at the Alembic directory under src/
├── docs/                  # Architecture, test strategy, dev guide, requirements
├── scripts/
│   └── update_version.py  # Called by semantic-release to bump the version
├── src/                   # Application code (see Architecture)
├── tests/                 # unit / integration / e2e
├── Dockerfile             # Multi-stage: dev, test, production
├── docker-compose.yml     # dev profile, plus an isolated test profile
├── entrypoint.sh          # dev (uvicorn) and prod (gunicorn) entrypoints
├── Makefile               # Every common command
├── .env.example           # Template for the environment variables
└── pyproject.toml         # Dependencies, Ruff, mypy, pytest and coverage config
```

`entrypoint.sh` applies migrations before starting the server in both stages, so a fresh environment comes up with the schema already in place.

---

## License

Distributed under the **MIT** License. See [LICENSE](LICENSE).

---

> Made with ♥️ by [JohannGaviria](https://github.com/JohannGaviria); always open to connecting for feedback, collaboration, or job opportunities.
