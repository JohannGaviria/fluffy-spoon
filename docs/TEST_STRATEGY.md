# Test Strategy

> Defines the test levels applied to the project (unit, integration and end-to-end), their organization, the coverage target and the available commands to run them.

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
    - [Combining the coverage reports](#combining-the-coverage-reports)

---

## Overall Approach

**What goes here:** which testing levels are applied (unit, integration, E2E) and why that combination makes sense for this project.

---

## Test Organization

**What goes here:** test folder structure and naming convention.

### Unit Tests
#### What is Analyzed?
#### How is it Tested?
#### Objective

### Integration Tests
#### What is Analyzed?
#### How is it Tested?
#### Objective

### End-to-End (E2E) Tests
#### What is Analyzed?
#### How is it Tested?
#### Objective

---

## Coverage Target

**What goes here:** the defined threshold, how it is measured and with which tool.

---

## Running the Tests

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
