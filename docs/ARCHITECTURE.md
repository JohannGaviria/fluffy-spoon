# Architecture - Fluffy Spoon

> Describes the architecture chosen for the system, the internal organization of the project, the boundaries between layers and the path a typical request takes through them.

## Table of Contents

* [Architecture Overview](#architecture-overview)
* [Current Implementation Status](#current-implementation-status)
* [Project Organization](#project-organization)

  * [Overall Structure](#overall-structure)
  * [Module Layout](#module-layout)
  * [Shared Layout](#shared-layout)
  * [Architecture Layers](#architecture-layers)
  * [Dependency Direction](#dependency-direction)
* [Typical Request Flow](#typical-request-flow)

  * [System Endpoints](#system-endpoints)
  * [How a Module Endpoint Will Flow](#how-a-module-endpoint-will-flow)
* [Known Limits and Assumptions](#known-limits-and-assumptions)

---

## Architecture Overview

Fluffy Spoon is a **modular monolith with layered architecture**, deployed as a single FastAPI process exposing a REST API.

The codebase is organized primarily by **functional module**: each capability under `src/modules/` contains its own API, business logic, persistence code and module-specific infrastructure. This keeps the code related to a capability together while maintaining clear responsibilities between layers.

The project uses four main layers:

* **API** — HTTP transport, request validation, dependencies and response serialization.
* **Business** — use cases, services, business rules and business-level DTOs.
* **Data** — persistence models, repositories and database queries.
* **Infrastructure** — concrete integrations with external technologies such as Argon2, JWT and S3.

The layers follow a **top-down dependency direction**:

```text
API
 ↓
Business
 ↓
Data
 ↓
Infrastructure
```

A module may also use infrastructure components directly when the business logic requires them. These dependencies are injected into services rather than created inside the business logic itself.

This is intentionally a **simple layered architecture**, not a Ports and Adapters or Clean Architecture implementation. The project does not introduce interfaces or ports solely to abstract concrete implementations. Instead, services receive their concrete dependencies through constructor injection, which keeps object creation outside the business logic and makes individual services straightforward to test.

Cross-cutting capabilities used by multiple modules live in `src/shared/`. Redis is one of these shared capabilities: the Redis client is application-wide infrastructure and any module can use it when its use case requires caching or other Redis-backed functionality.

The project is currently in the **foundation stage**: the layer structure and cross-cutting infrastructure are in place, and `auth` is the first module being built. The albums, images, comments and ratings capabilities described in [Requirements Specification](REQUIREMENTS_SPECIFICATION.md) are the target scope, not built code yet.

---

## Current Implementation Status

The table separates what exists in the repository today from what the requirements define.

| Area                                              | Status      | Notes                                                                                          |
| ------------------------------------------------- | ----------- | ---------------------------------------------------------------------------------------------- |
| Application bootstrap                             | Implemented | `src/main.py`, `src/config.py`, CORS, correlation ID middleware.                               |
| Health endpoints                                  | Implemented | `/`, `/health`, `/health/ready`.                                                               |
| Exception handling                                | Implemented | Catch-all handler in `shared/api/exceptions/`; logs the cause and returns a generic 500.       |
| Structured logging                                | Implemented | Structlog with a correlation ID bound to each request.                                         |
| Persistence and cache clients                     | Implemented | Async SQLAlchemy engine/session and async Redis client. No higher-level cache service yet.     |
| Alembic migrations                                | Implemented | `env.py` wired to `Base.metadata`, with one scaffolding revision for the `example` table.      |
| `auth` module                                     | Not started | No files under `src/modules/auth/` yet; the folder layout above is the target.                 |
| `albums`, `images`, `comments`, `ratings` modules | Planned     | Out of the current code base; see [Requirements Specification](REQUIREMENTS_SPECIFICATION.md). |
| Object storage (S3), JWT, Argon2                  | Not started | Not yet dependencies of the project; the flows below describe the target design.               |

---

## Project Organization

### Overall Structure

```text
src/
├── main.py                 # Application entry point (FastAPI)
├── config.py               # Environment variable configuration
├── modules/                # Business capabilities, one folder per module
│   ├── auth/               # Registration, login and logout
│   ├── albums/             # Album management and visibility
│   ├── images/             # Image upload and queries
│   ├── comments/           # Comments on images
│   └── ratings/            # Ratings (1–5) on images
└── shared/                 # Cross-cutting capabilities
```

* `main.py` assembles the FastAPI application and registers the application-level components.
* `config.py` centralizes environment-based configuration such as database, Redis and CORS settings.
* `modules/` contains the business capabilities. Each module owns the code directly related to its domain.
* `shared/` contains capabilities that are used by more than one module or belong to application-wide plumbing.

The test strategy follows the same boundary: `tests/unit`, `tests/integration` and `tests/e2e` mirror the structure of `src/`, so coverage and verification focus on the affected capability. See [Test Strategy](TEST_STRATEGY.md).

### Module Layout

Every module under `src/modules/` uses the same set of folders. A module only creates the folders it needs; all of them are optional.

```text
src/modules/auth/
├── api/            # Routers, HTTP schemas, dependencies and HTTP wiring
├── business/       # Services, DTOs and business rules
├── data/           # Models, repositories and queries
├── enums/          # Enumerations owned by the module
├── exceptions/     # Exceptions owned by the module
└── infrastructure/ # Concrete integrations with external technologies
```

| Folder            | Responsibility                                                                                                                                                      |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `api/`            | Receive HTTP requests, validate HTTP payloads, invoke business services and serialize responses. It contains no business rules.                                     |
| `business/`       | Orchestrate use cases, apply business rules and expose service-level operations. DTOs in this layer represent service inputs and outputs rather than HTTP payloads. |
| `data/`           | Own SQLAlchemy models, repositories and database queries.                                                                                                           |
| `enums/`          | Enumerations owned by the module's domain or application rules.                                                                                                     |
| `exceptions/`     | Exceptions that describe failures specific to the module.                                                                                                           |
| `infrastructure/` | Concrete integrations with external technologies required by the module, such as Argon2, JWT or S3.                                                                 |

HTTP schemas and business DTOs intentionally remain separate.

For example:

```text
HTTP request
    ↓
api/schema
    ↓
business/DTO
    ↓
business/service
    ↓
data/infrastructure
```

The API schema represents the HTTP contract, while the business DTO represents the input or output contract of a service. This prevents HTTP-specific structures from becoming part of the business layer.

### Shared Layout

`src/shared/` contains application-wide capabilities that are not owned by a single business module.

```text
src/shared/
├── api/
│   ├── exceptions/         # Global exception handlers
│   ├── middleware/         # Correlation ID middleware
│   └── schemas/            # Shared HTTP response envelopes
├── data/
│   ├── alembic/            # Migrations (`env.py`, `versions/`)
│   ├── models/             # Declarative base and shared scaffolding model
│   ├── database.py         # Async engine, sessionmaker and session context manager
│   └── redis_client.py     # Application-wide async Redis client
├── exceptions/             # Base application exception
└── infrastructure/
    └── logging/            # Structlog configuration and logger
```

Current contents:

| Path                                                    | Artifact                                                      | Purpose                                                                                                                                                                                         |
| ------------------------------------------------------- | ------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `api/exceptions/exception_handlers.py`                  | `exception_handlers`                                          | Registers the catch-all handler. Logs the real exception and returns a generic 500, so unexpected errors do not leak SQL, connection strings or upstream payloads to the client.                |
| `api/middleware/correlation_id_middleware.py`           | `CorrelationIdMiddleware`                                     | Reads or generates `X-Correlation-ID`, binds it to the structlog context for the request and echoes it back in the response header.                                                             |
| `api/schemas/response_schema.py`                        | `StatusEnum`, `SuccessResponseSchema`, `ErrorsResponseSchema` | Defines the shared HTTP response envelopes returned by endpoints.                                                                                                                               |
| `data/database.py`                                      | `Database`, `database`                                        | Async engine and sessionmaker built from settings, plus a `session()` context manager that rolls back on error and leaves the commit to the caller. Also exposes `ping()` for readiness checks. |
| `data/redis_client.py`                                  | `RedisClient`, `redis_client`                                 | Application-wide async Redis client backed by a connection pool. Provides `connect`, `disconnect` and `ping`.                                                                                   |
| `data/models/base_model.py`                             | `Base`, `BaseModel`                                           | Declarative base used by SQLAlchemy models and the abstract parent that provides `id`, `created_at` and `updated_at`.                                                                           |
| `data/models/example_model.py`                          | `ExampleModel`                                                | Scaffolding model (`example` table) that proves the model and migration path end to end. It is not a domain entity and is meant to be replaced.                                                 |
| `data/alembic/`                                         | `env.py`, `versions/`, `script.py.mako`                       | Migration environment wired to `Base.metadata`. Every module that adds a model must make that model visible to `env.py` so Alembic can detect it during autogeneration.                         |
| `exceptions/exception.py`                               | `BaseAppException`                                            | Root of the application exception hierarchy. Module-specific exceptions inherit from it so application failures can be handled without swallowing programming errors.                           |
| `infrastructure/logging/structlog_configure_logging.py` | `StructlogConfigureLogging`                                   | Configures structlog to emit JSON and routes standard-library records through the same processors.                                                                                              |
| `infrastructure/logging/structlog_logger.py`            | `StructlogLogger`                                             | Thin wrapper over the structlog bound logger. Provides a single logging entry point for the application.                                                                                        |

The shared layers contain only application-wide plumbing.

`shared/api/` contains HTTP concerns that apply to every module.

`shared/data/` contains the database engine, session management, Redis client and SQLAlchemy metadata infrastructure used by repositories across modules.

`shared/infrastructure/` contains infrastructure that is genuinely application-wide, such as logging.

`shared/exceptions/` contains the root application exception because every module may define exceptions derived from it.

The tables themselves are **not** stored in `shared/data/`. Each module owns its own SQLAlchemy models because those models represent entities belonging to that module.

The same rule applies to module-specific infrastructure. Argon2, JWT and S3 remain inside the module that requires them until another module genuinely needs the same capability. At that point, the code can be reconsidered for promotion to `shared/`.

The rule that keeps `shared/` from becoming a junk drawer is simple:

> A capability moves to `shared/` only when it is genuinely cross-cutting or required by more than one module.

Redis is an intentional exception to module ownership because it is an application-wide client and can be used by any module. The client itself lives in `shared/data/`; modules remain responsible for deciding how and why Redis is used.

---

## Architecture Layers

| Layer              | Responsibility                                                                                                      | Representative artifacts                                  |
| ------------------ | ------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------- |
| API (Presentation) | Handle HTTP transport, validate HTTP payloads, invoke business services and serialize responses.                    | Each module's `api/`, `shared/api/`                       |
| Business           | Execute use cases, coordinate operations and apply business rules. Business DTOs define service inputs and outputs. | Each module's `business/`                                 |
| Data               | Persist and retrieve application data through SQLAlchemy models, repositories and queries.                          | Each module's `data/`, `shared/data/`                     |
| Infrastructure     | Provide concrete integrations with external technologies required by the application or a module.                   | Each module's `infrastructure/`, `shared/infrastructure/` |

The layers are intentionally pragmatic.

The project does **not** introduce ports, interfaces or abstract repositories solely to invert dependencies. Services receive the concrete dependencies they need through constructor injection.

For example, a service may depend directly on a concrete implementation:

```python
class AuthenticationService:
    def __init__(
        self,
        argon2_password_hasher: Argon2PasswordHasher,
    ) -> None:
        self._argon2_password_hasher = argon2_password_hasher
```

The service therefore knows that it uses `Argon2PasswordHasher`. This is an intentional trade-off in favor of a simpler architecture and fewer abstractions.

Constructor injection still keeps dependency creation outside the service and makes the service easier to instantiate with controlled dependencies during testing.

---

## Dependency Direction

The project uses a **top-down layered dependency direction**:

```text
┌──────────────────────┐
│         API          │
│ Routers              │
│ HTTP schemas         │
│ HTTP dependencies    │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│      BUSINESS        │
│ Services             │
│ Business DTOs        │
│ Business rules       │
└──────────┬───────────┘
           │
           ├──────────────────┐
           ▼                  ▼
┌──────────────────┐  ┌─────────────────────┐
│       DATA       │  │   INFRASTRUCTURE    │
│ Models           │  │ Argon2              │
│ Repositories     │  │ PyJWT               │
│ Queries          │  │ S3                  │
└────────┬─────────┘  └─────────────────────┘
         │
         ▼
┌──────────────────┐
│ External systems │
│ PostgreSQL       │
│ Redis            │
└──────────────────┘
```

The important rule is that responsibilities move downward through the layers:

* `api` knows about HTTP and calls `business`.
* `business` knows about application rules and uses concrete services, repositories and infrastructure components it requires.
* `data` knows about persistence and database access.
* `infrastructure` knows how to communicate with external technologies.
* Lower layers do not build HTTP responses or depend on FastAPI request/response objects.

The architecture does not claim that the business layer is completely independent of concrete infrastructure. Concrete dependencies such as `Argon2PasswordHasher` may be injected directly into a business service.

The goal is instead to keep responsibilities explicit and keep HTTP, persistence and external technology concerns from being mixed together inside the same code.

---

## Typical Request Flow

### System Endpoints

The only routes currently registered live in `src/main.py`.

1. `CorrelationIdMiddleware` reads or generates `X-Correlation-ID` and binds it to the logging context, so every log line generated during the request carries it.
2. The handler returns a `SuccessResponseSchema` envelope, serialized with `jsonable_encoder`.
3. `/health` answers `200` without touching PostgreSQL or Redis on purpose. It acts as a liveness probe and therefore only verifies that the application process is running.
4. `/health/ready` checks both dependencies through `_is_reachable`, which converts driver errors into `False` so the endpoint can return `503` with per-dependency status instead of becoming an unexpected `500`.

Database and Redis connections are opened once per process in the `lifespan` handler and closed in its `finally` block. This also ensures that a failure during startup releases resources that were already opened.

### How a Module Endpoint Will Flow

The target path for a future `POST /api/v1/auth/login` is:

1. The router in `src/modules/auth/api/` receives the request and validates the HTTP payload using its API schema.
2. The router converts the validated HTTP input into the business DTO expected by the authentication service.
3. The authentication service in `src/modules/auth/business/` executes the login use case and applies its business rules.
4. The service uses the concrete `Argon2PasswordHasher` from `src/modules/auth/infrastructure/` to verify the password.
5. The service uses the module's repository from `src/modules/auth/data/` to retrieve the user.
6. The service may use the application-wide `shared/data/redis_client.py` when the use case requires Redis, such as temporary login-attempt tracking or lockout state.
7. A concrete JWT implementation from `src/modules/auth/infrastructure/` creates the access token.
8. The service returns a business DTO representing the result of the use case.
9. The router converts that business result into the appropriate HTTP response schema.
10. If an application exception escapes the router, the handler registered in `shared/api/exceptions/` converts it into the common error response envelope.

The important boundary is that **HTTP schemas stay in `api/` and business DTOs stay in `business/`**.

A business service does not receive a FastAPI `Request`, return a FastAPI `Response` or manipulate HTTP response envelopes.

Likewise, a repository does not decide how an HTTP error should be represented.

---

## Known Limits and Assumptions

* **Single-process monolith:** the application is deployed as a single FastAPI service managed by Uvicorn (`BACKEND_WORKERS`). There is no service discovery, load balancing or distributed service architecture in the current design.
* **Layered dependencies:** dependencies generally flow from API to business and from business toward data and infrastructure. The project does not attempt to enforce strict dependency inversion through ports or interfaces.
* **Concrete dependency injection:** services receive concrete implementations through constructor injection. This reduces hidden object creation inside services without introducing additional abstraction layers.
* **No asynchronous processing or events:** detaching images when an album is deleted is planned as a transactional and synchronous operation (`ON DELETE SET NULL`, [ADR-001](TECHNICAL_DECISIONS.md)). An event-driven approach (`AlbumDeleted`, consumers, eventual consistency) is left for a later iteration.
* **Redis is application-wide:** the Redis client lives in `shared/data/` because multiple modules may use Redis. Modules are responsible for their own Redis keys, expiration rules and business decisions around caching.
* **Token revocation depends on Redis:** the planned logout flow depends on a Redis blacklist. If the cache is lost or flushed, a token would remain valid until its expiry.
* **Cache invalidation by pattern:** planned listings will be invalidated by sweeping prefixes such as `cache:albums:list:*` and `cache:images:list:*` after writes. There is no fine-grained per-entity invalidation, so a high write frequency can reduce cache hit rates.
* **Direct upload to S3:** the planned image flow requires a bucket configured for presigned URLs and CORS. No thumbnail generation, EXIF processing or background processing queue is currently planned.
* **Minimal user model:** there is no profile management, password change or password recovery in the current scope.
* **Concurrency resolved at the database level:** rating uniqueness is enforced through `UNIQUE (image_id, user_id)`. S3 object existence is also verified before confirming the corresponding operation. No distributed locks are used.
* **External technology coupling is intentional:** module business services may depend directly on concrete infrastructure implementations such as Argon2 or JWT. Introducing interfaces is not considered necessary until the project has a concrete requirement for that additional abstraction.
* **Extreme concurrency and horizontal scaling are out of scope:** the current goal is correctness of business rules, maintainability and architectural clarity rather than massive throughput.
