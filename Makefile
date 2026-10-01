# ==============================================================================
# Configuration
# ==============================================================================

.PHONY: help setup \
        up down logs clean \
        build-test test test-unit test-integration test-e2e \
        test-integration-no-db \
        test-coverage test-coverage-unit test-coverage-integration \
        test-coverage-e2e test-coverage-report \
        format lint check pre-commit

# ==============================================================================
# Help
# ==============================================================================

help: ## Show available commands
	@echo "=== Available Commands ==="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "%-30s %s\n", $$1, $$2}'

# ==============================================================================
# Setup
# ==============================================================================

setup: ## Install dependencies and Git hooks
	@echo "Installing project dependencies..."
	poetry install --with dev,test

	@echo "Installing pre-commit hooks..."
	poetry run pre-commit install

# ==============================================================================
# Docker
# ==============================================================================

up: ## Start development environment
	@echo "Starting development environment..."
	docker compose --profile dev up --build

down: ## Stop development and testing containers
	@echo "Stopping containers..."
	docker compose --profile dev --profile test down

logs: ## Follow container logs
	@echo "Following container logs..."
	docker compose logs -f

clean: ## Remove containers, volumes and local images
	@echo "Cleaning Docker resources..."
	docker compose --profile dev --profile test down -v --rmi local

# ==============================================================================
# Testing
# ==============================================================================

build-test: ## Build testing image
	@echo "Building testing image..."
	docker compose build backend-test

test: build-test ## Run all tests
	@echo "Running complete test suite..."
	docker compose --profile test run --rm backend-test pytest tests -v

test-unit: ## Run unit tests
	@echo "Running unit tests..."
	poetry run pytest tests/unit -v

test-integration: build-test ## Run integration tests
	@echo "Running integration tests..."
	docker compose --profile test run --rm backend-test \
		pytest tests/integration -v

test-integration-no-db: ## Run integration tests without external infrastructure
	@echo "Running infrastructure-free integration tests..."
	poetry run pytest tests/integration -m "not db" -v

test-e2e: build-test ## Run end-to-end tests
	@echo "Running E2E tests..."
	docker compose --profile test run --rm backend-test \
		pytest tests/e2e -v

# ==============================================================================
# Coverage
# ==============================================================================

test-coverage: build-test ## Run all tests with coverage
	@echo "Running test suite with coverage..."
	docker compose --profile test run --rm backend-test \
		pytest tests \
		--cov=src \
		--cov-report=term-missing \
		--cov-fail-under=70

# The per-scope coverage files are set with target-specific exports instead of
# a `VAR=value command` prefix, because that prefix is POSIX shell syntax and
# fails on Windows, where make runs recipes through cmd.exe.
test-coverage-unit: export COVERAGE_FILE=tests/.coverage.unit
test-coverage-unit: ## Collect unit test coverage
	@echo "Collecting unit test coverage..."
	poetry run pytest tests/unit \
		--cov=src \
		--cov-report=

test-coverage-integration: build-test ## Collect integration test coverage
	@echo "Collecting integration test coverage..."
	docker compose --profile test run --rm \
		-e COVERAGE_FILE=tests/.coverage.integration \
		backend-test \
		pytest tests/integration \
		--cov=src \
		--cov-report=

test-coverage-e2e: build-test ## Collect E2E test coverage
	@echo "Collecting E2E test coverage..."
	docker compose --profile test run --rm \
		-e COVERAGE_FILE=tests/.coverage.e2e \
		backend-test \
		pytest tests/e2e \
		--cov=src \
		--cov-report=

test-coverage-report: ## Combine coverage reports and enforce threshold
	@echo "Combining coverage reports..."
	poetry run coverage combine tests/
	poetry run coverage report --show-missing --fail-under=70

# ==============================================================================
# Code Quality
# ==============================================================================

format: ## Format code and apply safe fixes
	@echo "Applying Ruff fixes..."
	poetry run ruff check --fix .

	@echo "Formatting code..."
	poetry run ruff format .

lint: ## Run Ruff linting
	@echo "Running Ruff..."
	poetry run ruff check .

check: ## Run all code quality checks
	@echo "Checking formatting..."
	poetry run ruff format --check .

	@echo "Checking lint..."
	poetry run ruff check .

	@echo "Checking types..."
	poetry run mypy .

pre-commit: ## Run all pre-commit hooks
	@echo "Running pre-commit hooks..."
	poetry run pre-commit run --all-files