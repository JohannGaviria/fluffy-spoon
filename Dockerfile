ARG PYTHON_VERSION=3.14-slim
ARG POETRY_VERSION=2.4.1

# =============================================================================
# Base
# =============================================================================

FROM python:${PYTHON_VERSION} AS base

ARG POETRY_VERSION

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VERSION=${POETRY_VERSION} \
    POETRY_HOME=/opt/poetry \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false

ENV PATH="${POETRY_HOME}/bin:${PATH}"

WORKDIR /app

RUN pip install --no-cache-dir "poetry==${POETRY_VERSION}"

COPY pyproject.toml poetry.lock ./

COPY --chmod=755 entrypoint.sh /usr/local/bin/entrypoint.sh

ENTRYPOINT ["entrypoint.sh"]

# =============================================================================
# Development
# =============================================================================

FROM base AS development

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN poetry install --no-root --with dev

COPY . .

CMD ["dev"]

# =============================================================================
# Testing
# =============================================================================

FROM base AS testing

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN poetry install --no-root --with test

COPY . .

# The entrypoint owns the migration step for this stage, so it is baked in here
# rather than in CMD: every `docker compose run backend-test <cmd>` invocation
# overrides CMD but keeps the ENTRYPOINT arguments.
ENTRYPOINT ["entrypoint.sh", "test"]

CMD ["poetry", "run", "pytest", "tests"]

# =============================================================================
# Production
# =============================================================================

FROM base AS production

RUN poetry install --no-root --with prod

COPY alembic.ini .
COPY src ./src

RUN useradd \
        --create-home \
        --shell /usr/sbin/nologin \
        appuser \
    && chown -R appuser:appuser /app

USER appuser

CMD ["prod"]