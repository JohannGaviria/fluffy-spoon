# Test Strategy - Fluffy Spoon

> Defines the test levels applied to the project (unit, integration and end-to-end), their organization, the coverage target and the commands available to run them.

## Table of Contents

- [Overall Approach](#overall-approach)
- [Test Organization](#test-organization)
    - [Unit Tests](#unit-tests)
    - [Integration Tests](#integration-tests)
    - [End-to-End (E2E) Tests](#end-to-end-e2e-tests)
- [Coverage Target](#coverage-target)
- [Running the Tests](#running-the-tests)
    - [Tests with Docker (recommended)](#tests-with-docker-recommended)
    - [Tests without Docker (unit tests only)](#tests-without-docker-unit-tests-only)

---

## Overall Approach

The project follows the **testing pyramid**: a broad base of fast unit tests, a middle layer of integration tests against real infrastructure, and a reduced set of end-to-end tests covering complete user flows.

This combination makes sense for two reasons. First, most of the system's value lies in the business rules —resource ownership, public/private visibility, rating uniqueness, 1–5 scores— which can be verified in isolation and at high speed. Second, real interactions with PostgreSQL, Redis and S3 introduce risks that can only be detected by testing against the real infrastructure.

- **Unit:** verify the business rules and use cases without depending on databases, Redis, S3 or the network. They are the most numerous and the fastest.
- **Integration:** verify the shared infrastructure (async SQLAlchemy engine and session in `shared/data/`, the cache adapter and the Redis client) against real PostgreSQL and Redis instances.
- **E2E:** verify complete HTTP flows against the running application, validating the behavior observable by a user.

> **Current state:** the suite covers the shared infrastructure and the system endpoints. There are no module tests yet, because `src/modules/` has no code; the module-level tests will be added as each module is built. The scenarios listed below for albums, images, comments and ratings come from the [requirements specification](REQUIREMENTS_SPECIFICATION.md) and describe the target scope.

---

## Test Organization

Tests are organized in three directories according to their level. Inside each one, the folders mirror the structure of `src/`, so a test sits next to the layer it verifies:

```
tests/
├── conftest.py                        # Suite-wide fixtures and the skip rule below
├── helpers.py                         # Shared helpers (service reachability)
├── unit/                              # Unit tests (no infrastructure)
│   ├── test_config.py                 # Environment variable parsing
│   └── shared/
│       └── infrastructure/
│           └── logging/               # Structlog configuration and logger
├── integration/                       # Integration tests (real PostgreSQL and Redis)
│   └── shared/
│       └── data/                      # Engine, session, ping and the Redis client
│           ├── test_database.py
│           └── test_redis_client.py
└── e2e/                               # End-to-end tests (HTTP flows)
    └── test_health.py                 # /, /health and /health/ready
```

**Naming convention:** files use the `test_*.py` prefix and each level mirrors the structure of `src/`. Tests that require infrastructure are marked with `-m db` (integration) and `-m e2e` (end-to-end); unit tests require no marker. An end-to-end test carries both markers, because the health endpoints reach PostgreSQL and Redis. The common fixtures of each level are defined in `conftest.py` and the shared helpers in `tests/helpers.py`.

**No `modules/` folders yet.** There are no tests for `src/modules/auth/` or for the planned albums, images, comments and ratings modules, because none of that code exists. The tree above only shows what is in the repository; the per-module test folders will be created next to the code they cover.

`conftest.py` also holds a rule worth knowing before you see a skipped test: any test marked `db` is skipped, with an actionable reason, when `tests/helpers.py` cannot open a TCP connection to the configured PostgreSQL or Redis URL. That happens when the suite runs on the host, where those URLs resolve to Docker Compose service names. The tests are not passing — they are waiting to be run through Docker.


### Unit Tests

#### What Is Exercised?

The business rules and use cases without touching infrastructure:

- Validation rules: `title` (1–100), `description` (≤500), `content` (1–500) and `score` (1–5).
- Truth table visibility rules: owner vs. third parties and `public`/`private` on albums and images.
- Resource ownership: only the owner can modify/delete albums, images, comments and ratings.
- Prevention of duplicate ratings and login lockout after failed attempts.
- Logout logic and `access_token` blacklist (key `cache:access_token:revoked:{jti}`).
- `storage_key` generation, `content_type`/`file_size` validation and presigned URL expiration.

The cross-cutting code also has unit coverage: the cache adapter against a fake Redis client, the correlation ID middleware, the response schemas, the configuration parsing, the Structlog configuration and the readiness dependency checks.

#### How Are They Tested?

With fake clients and mock objects that implement the same interface as the real adapters. Asynchronous tests run with `pytest-asyncio`. They require no PostgreSQL, Redis or network.

#### Goal

Verify the business logic in milliseconds and without external dependencies, catching rule and flow errors as early as possible and serving as the project's widest safety net.

### Integration Tests

#### What Is Exercised?

The shared infrastructure against real dependencies:

- Async SQLAlchemy engine and session: acquisition, rollback on error and `ping`.
- Redis: the client's connection handling and the cache adapter's `get`/`set`/`delete`, including invalid JSON, unserializable values, a backend that is down and the sweep of a namespace by prefix.
- Module repositories, once the modules are built: CRUD, combined filters, sorting and pagination, referential integrity (`ON DELETE SET NULL` and `ON DELETE CASCADE`) and database constraints (`CHECK (score BETWEEN 1 AND 5)`, uniqueness of `(image_id, user_id)`).
- Concurrency, once the modules are built: simultaneous creation of ratings on the same image and duplicate confirmation of the same `storage_key`.

#### How Are They Tested?

Against a real PostgreSQL instance and a real Redis, brought up with the `test` profile of Docker Compose. The tests use the `-m db` marker and expose asynchronous fixtures (SQLAlchemy session and engine) to guarantee isolation between cases.

#### Goal

Detect ORM mapping errors, real database constraints, cache behavior and concurrency issues that unit tests cannot reproduce.

### End-to-End (E2E) Tests

#### What Is Exercised?

Complete user flows over the API:

- Liveness and readiness: `/`, `/health` and `/health/ready`, including the `503` answer when a dependency is down.
- Correlation ID: the `X-Correlation-ID` header is echoed in the response and present in the logs.
- Error mapping: the envelope and status code returned for a cache failure and for an unhandled exception.
- Once the modules are built: registration → login → logout, and the album, image, comment and rating flows described in the [requirements specification](REQUIREMENTS_SPECIFICATION.md).

#### How Are They Tested?

With an asynchronous HTTP client (`httpx`/`AsyncClient`) against the running application, driven through its ASGI lifespan so the database and cache connections are opened and closed exactly as in production. They are marked with `-m e2e` and follow the module structure of `src/`.

#### Goal

Confirm that the layers integrate correctly, that the application starts and shuts down cleanly and that the business rules hold as a real user would experience them.

---

## Coverage Target

It is measured with `pytest-cov` over `src/` using `--cov=src --cov-report=term-missing`.

- **Defined threshold:** line coverage ≥ **80%** over `src/`.
- **Business rules and repositories** must keep the highest possible coverage, since they concentrate the system's critical logic.
- The cross-cutting code in `src/shared/` is also held to a high bar: it is used by every module, so a defect there surfaces everywhere at once.
- Integration and E2E tests complement the coverage of the coordination between layers, which is not always reachable from unit tests.
- In CI the threshold is enforced as a failure condition with `--cov-fail-under`.

---

## Running the Tests

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
