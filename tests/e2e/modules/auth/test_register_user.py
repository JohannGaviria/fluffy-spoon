import io
import logging
from collections.abc import AsyncIterator, Iterator
from uuid import UUID, uuid4

import pytest
from argon2 import PasswordHasher
from httpx import AsyncClient
from sqlalchemy import insert, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.modules.auth.data.models.user_model import UserModel
from src.modules.auth.data.repositories.user_repository import UserRepository
from src.modules.auth.exceptions.user_exception import UserRepositoryException
from src.shared.api.schemas.response_schema import StatusEnum
from src.shared.data.database import database

# Every request below reaches the real repository and the real password hasher,
# so these tests need PostgreSQL and Redis and the migrated `users` table.
pytestmark = [pytest.mark.e2e, pytest.mark.db]

REGISTER_PATH = "/api/v1/auth/register"
PASSWORD = "SecurePass!23"
SUCCESS_MESSAGE = "User successfully registered."


class LogCapture:
    """Buffer fed by the formatter the application configured on import.

    Structlog is configured at `src.main` import time, before pytest replaces
    `sys.stdout`, so `capsys` would miss the output entirely. Attaching a second
    handler with the very same formatter sees exactly what the application emits.
    """

    def __init__(self, formatter: logging.Formatter | None) -> None:
        self._buffer = io.StringIO()
        self._handler = logging.StreamHandler(self._buffer)
        self._handler.setFormatter(formatter)

    @property
    def raw(self) -> str:
        return self._buffer.getvalue()

    def reset(self) -> None:
        self._buffer.seek(0)
        self._buffer.truncate(0)

    def attach(self, root: logging.Logger, level: int) -> None:
        root.addHandler(self._handler)
        root.setLevel(level)

    def detach(self, root: logging.Logger, level: int) -> None:
        root.removeHandler(self._handler)
        root.setLevel(level)


@pytest.fixture
def captured_logs() -> Iterator[LogCapture]:
    root = logging.getLogger()
    previous_level = root.level
    capture = LogCapture(root.handlers[0].formatter)
    capture.attach(root, logging.DEBUG)

    yield capture

    capture.detach(root, previous_level)


@pytest.fixture
async def session() -> AsyncIterator[AsyncSession]:
    """Yield a session for the assertions that read the database directly."""
    async with database.session() as active_session:
        yield active_session


@pytest.fixture
def payload() -> dict[str, str]:
    return {"name": "John Doe", "email": "john@doe.com", "password": PASSWORD}


async def count_users(session: AsyncSession) -> int:
    result = await session.execute(select(UserModel.id))
    return len(result.all())


class TestRegisterUser:
    class TestRegisterUserSuccess:
        async def test_should_answer_201_created(self, client: AsyncClient, payload):
            response = await client.post(REGISTER_PATH, json=payload)

            assert response.status_code == 201

        async def test_should_answer_the_success_envelope(
            self, client: AsyncClient, payload
        ):
            response = await client.post(REGISTER_PATH, json=payload)

            body = response.json()
            assert body["status"] == StatusEnum.SUCCESS
            assert body["message"] == SUCCESS_MESSAGE

        async def test_should_answer_exactly_the_documented_fields(
            self, client: AsyncClient, payload
        ):
            response = await client.post(REGISTER_PATH, json=payload)

            assert set(response.json()["data"]) == {
                "id",
                "name",
                "email",
                "created_at",
                "updated_at",
            }

        async def test_should_echo_the_registered_name_and_email(
            self, client: AsyncClient, payload
        ):
            response = await client.post(REGISTER_PATH, json=payload)

            data = response.json()["data"]
            assert data["name"] == payload["name"]
            assert data["email"] == payload["email"]

        async def test_should_answer_a_uuid_as_the_identifier(
            self, client: AsyncClient, payload
        ):
            response = await client.post(REGISTER_PATH, json=payload)

            assert UUID(response.json()["data"]["id"])

        async def test_should_answer_equal_timestamps_for_a_fresh_user(
            self, client: AsyncClient, payload
        ):
            response = await client.post(REGISTER_PATH, json=payload)

            data = response.json()["data"]
            assert data["created_at"] == data["updated_at"]

        async def test_should_give_a_different_identifier_to_each_registration(
            self, client: AsyncClient, payload
        ):
            first = await client.post(REGISTER_PATH, json=payload)
            second = await client.post(
                REGISTER_PATH, json={**payload, "email": "jane@doe.com"}
            )

            assert first.json()["data"]["id"] != second.json()["data"]["id"]

        async def test_should_never_answer_with_the_password(
            self, client: AsyncClient, payload
        ):
            response = await client.post(REGISTER_PATH, json=payload)

            assert PASSWORD not in response.text
            assert "password" not in response.text

    class TestRegisterUserPersistsTheUser:
        async def test_should_store_the_row_in_postgres(
            self, client: AsyncClient, payload, session: AsyncSession
        ):
            response = await client.post(REGISTER_PATH, json=payload)

            stored = (
                await session.execute(
                    select(UserModel).where(UserModel.email == payload["email"])
                )
            ).scalar_one()

            assert stored.id == UUID(response.json()["data"]["id"])
            assert stored.name == payload["name"]

        async def test_should_store_an_argon2_hash_and_not_the_password(
            self, client: AsyncClient, payload, session: AsyncSession
        ):
            await client.post(REGISTER_PATH, json=payload)

            stored = (
                await session.execute(
                    select(UserModel).where(UserModel.email == payload["email"])
                )
            ).scalar_one()

            assert stored.password_hash.startswith("$argon2")
            assert PASSWORD not in stored.password_hash

        async def test_should_store_a_hash_that_verifies_against_the_password(
            self, client: AsyncClient, payload, session: AsyncSession
        ):
            # What makes the registration useful: the stored value has to be
            # verifiable by the login story that comes next.
            await client.post(REGISTER_PATH, json=payload)

            stored = (
                await session.execute(
                    select(UserModel).where(UserModel.email == payload["email"])
                )
            ).scalar_one()

            assert PasswordHasher().verify(stored.password_hash, PASSWORD) is True

        async def test_should_not_answer_the_timestamps_as_local_naive_values(
            self, client: AsyncClient, payload
        ):
            # The columns are `timestamptz`, so the response has to carry the offset
            # too. A naive value would be read as local time by the next service.
            response = await client.post(REGISTER_PATH, json=payload)

            assert response.json()["data"]["created_at"].endswith(("Z", "+00:00"))

    class TestRegisterUserRequestValidation:
        @pytest.mark.parametrize(
            "missing", ["name", "email", "password"], ids=["name", "email", "password"]
        )
        async def test_should_answer_422_when_a_required_field_is_missing(
            self, client: AsyncClient, payload, missing: str
        ):
            body = dict(payload)
            del body[missing]

            response = await client.post(REGISTER_PATH, json=body)

            assert response.status_code == 422

        @pytest.mark.parametrize(
            "field", ["name", "email", "password"], ids=["name", "email", "password"]
        )
        async def test_should_answer_422_when_a_field_has_the_wrong_type(
            self, client: AsyncClient, payload, field: str
        ):
            response = await client.post(
                REGISTER_PATH, json={**payload, field: {"nested": "value"}}
            )

            assert response.status_code == 422

        @pytest.mark.parametrize(
            "name",
            ["Jo", "", "J" * 101],
            ids=["two_chars", "empty", "one_hundred_and_one"],
        )
        async def test_should_answer_422_when_the_name_is_out_of_range(
            self, client: AsyncClient, payload, name: str
        ):
            response = await client.post(REGISTER_PATH, json={**payload, "name": name})

            assert response.status_code == 422

        @pytest.mark.parametrize(
            "password",
            ["Ab1!def", "Ab1!" + "a" * 13],
            ids=["seven_chars", "seventeen_chars"],
        )
        async def test_should_answer_422_when_the_password_length_is_out_of_range(
            self, client: AsyncClient, payload, password: str
        ):
            # The 8 to 16 range is a schema constraint, so it answers 422 and not
            # the 400 that the password policy rules produce.
            response = await client.post(
                REGISTER_PATH, json={**payload, "password": password}
            )

            assert response.status_code == 422

        @pytest.mark.parametrize(
            "email",
            ["not-an-email", "john@", "john doe@doe.com", ""],
            ids=["no_domain", "no_local_part", "embedded_space", "empty"],
        )
        async def test_should_answer_422_when_the_email_is_malformed(
            self, client: AsyncClient, payload, email: str
        ):
            response = await client.post(
                REGISTER_PATH, json={**payload, "email": email}
            )

            assert response.status_code == 422

        async def test_should_not_store_anything_when_validation_fails(
            self, client: AsyncClient, payload, session: AsyncSession
        ):
            await client.post(REGISTER_PATH, json={**payload, "name": "Jo"})

            assert await count_users(session) == 0

    class TestRegisterUserPasswordPolicy:
        @pytest.mark.parametrize(
            ("password", "rule"),
            [
                ("securepass!23", "Password must contain an uppercase letter."),
                ("SECUREPASS!23", "Password must contain a lowercase letter."),
                ("SecurePass!ab", "Password must contain a digit."),
                ("SecurePass123", "Password must contain a special character."),
            ],
            ids=["uppercase", "lowercase", "digit", "special"],
        )
        async def test_should_answer_400_when_the_password_breaks_a_rule(
            self, client: AsyncClient, payload, password: str, rule: str
        ):
            # These pass the schema, which only enforces the length range, and fail
            # the business rule, which the endpoint maps to a 400.
            response = await client.post(
                REGISTER_PATH, json={**payload, "password": password}
            )

            assert response.status_code == 400
            assert response.json()["details"] == rule

        async def test_should_answer_the_password_error_envelope(
            self, client: AsyncClient, payload
        ):
            response = await client.post(
                REGISTER_PATH, json={**payload, "password": "securepass!23"}
            )

            assert response.json() == {
                "status": "error",
                "message": "The password is invalid.",
                "details": "Password must contain an uppercase letter.",
            }

        async def test_should_not_store_anything_when_a_rule_is_broken(
            self, client: AsyncClient, payload, session: AsyncSession
        ):
            await client.post(
                REGISTER_PATH, json={**payload, "password": "securepass!23"}
            )

            assert await count_users(session) == 0

    class TestRegisterUserDuplicateEmail:
        async def test_should_answer_409_when_the_email_is_already_registered(
            self, client: AsyncClient, payload
        ):
            await client.post(REGISTER_PATH, json=payload)

            response = await client.post(REGISTER_PATH, json=payload)

            assert response.status_code == 409

        async def test_should_answer_the_conflict_envelope(
            self, client: AsyncClient, payload
        ):
            await client.post(REGISTER_PATH, json=payload)

            response = await client.post(REGISTER_PATH, json=payload)

            assert response.json() == {
                "status": "error",
                "message": "User already exists.",
            }

        async def test_should_keep_the_original_account(
            self, client: AsyncClient, payload, session: AsyncSession
        ):
            await client.post(REGISTER_PATH, json=payload)
            await client.post(REGISTER_PATH, json={**payload, "name": "Impostor"})

            stored = (
                await session.execute(
                    select(UserModel).where(UserModel.email == payload["email"])
                )
            ).scalar_one()

            assert stored.name == payload["name"]
            assert await count_users(session) == 1

        async def test_should_answer_409_when_a_concurrent_registration_wins_the_race(
            self, client: AsyncClient, payload, monkeypatch: pytest.MonkeyPatch
        ):
            # The lookup and the insert are not atomic, so a second request can insert
            # the same email in between. The unique constraint is what catches it and
            # it has to surface as a conflict rather than as a server error.
            async with database.session() as session:
                session.add(
                    UserModel(
                        name=payload["name"],
                        email=payload["email"],
                        password_hash="$argon2id$stale",
                    )
                )
                await session.commit()

            async def pretend_the_email_is_free(self, email: str) -> None:
                return None

            monkeypatch.setattr(
                UserRepository, "find_by_email", pretend_the_email_is_free
            )

            response = await client.post(REGISTER_PATH, json=payload)

            assert response.status_code == 409
            assert response.json()["message"] == "User already exists."

    class TestRegisterUserRepositoryFailure:
        @pytest.fixture
        def failing_repository(self, monkeypatch: pytest.MonkeyPatch) -> None:
            async def failing_lookup(self, email: str) -> None:
                raise UserRepositoryException(
                    "An error occurred while retrieving user by email address."
                )

            monkeypatch.setattr(UserRepository, "find_by_email", failing_lookup)

        async def test_should_answer_500_when_the_repository_fails(
            self, client: AsyncClient, payload, failing_repository: None
        ):
            response = await client.post(REGISTER_PATH, json=payload)

            assert response.status_code == 500

        async def test_should_answer_the_repository_error_envelope(
            self, client: AsyncClient, payload, failing_repository: None
        ):
            response = await client.post(REGISTER_PATH, json=payload)

            assert response.json() == {
                "status": "error",
                "message": "Error while interacting with the user repository.",
                "details": "An error occurred while retrieving user by email address.",
            }

        async def test_should_not_store_anything_when_the_repository_fails(
            self,
            client: AsyncClient,
            payload,
            session: AsyncSession,
            failing_repository: None,
        ):
            await client.post(REGISTER_PATH, json=payload)

            assert await count_users(session) == 0

        async def test_should_answer_a_generic_500_for_an_unexpected_error(
            self, client: AsyncClient, payload, monkeypatch: pytest.MonkeyPatch
        ):
            # Anything that is not a `BaseAppException` reaches the shared handler,
            # which must not repeat the driver text back to the caller.
            async def exploding_lookup(self, email: str) -> None:
                raise RuntimeError("connection to 10.0.0.5:5432 refused")

            monkeypatch.setattr(UserRepository, "find_by_email", exploding_lookup)

            response = await client.post(REGISTER_PATH, json=payload)

            assert response.status_code == 500

        @pytest.mark.skipif(
            settings.DEBUG,
            reason=(
                "FastAPI's ServerErrorMiddleware answers an unhandled exception with "
                "a plain-text traceback and never reaches the shared handler while "
                "debug is enabled."
            ),
        )
        async def test_should_answer_the_generic_envelope_when_debug_is_off(
            self, client: AsyncClient, payload, monkeypatch: pytest.MonkeyPatch
        ):
            async def exploding_lookup(self, email: str) -> None:
                raise RuntimeError("connection to 10.0.0.5:5432 refused")

            monkeypatch.setattr(UserRepository, "find_by_email", exploding_lookup)

            response = await client.post(REGISTER_PATH, json=payload)

            assert response.json() == {
                "status": "error",
                "message": "An unexpected error occurred while processing the request.",
            }
            assert "10.0.0.5" not in response.text
            assert "Traceback" not in response.text


class TestRegisterUserNeverLogsThePassword:
    async def test_should_not_write_the_password_to_the_logs(
        self, client: AsyncClient, payload, captured_logs: LogCapture
    ):
        await client.post(REGISTER_PATH, json=payload)

        assert PASSWORD not in captured_logs.raw

    async def test_should_not_write_the_password_to_the_logs_on_a_conflict(
        self, client: AsyncClient, payload, captured_logs: LogCapture
    ):
        await client.post(REGISTER_PATH, json=payload)
        captured_logs.reset()

        await client.post(REGISTER_PATH, json=payload)

        assert PASSWORD not in captured_logs.raw

    async def test_should_not_write_the_password_to_the_logs_when_a_rule_breaks(
        self, client: AsyncClient, payload, captured_logs: LogCapture
    ):
        await client.post(REGISTER_PATH, json={**payload, "password": "securepass!23"})

        assert "securepass!23" not in captured_logs.raw

    async def test_should_not_write_the_password_to_the_logs_when_validation_fails(
        self, client: AsyncClient, payload, captured_logs: LogCapture
    ):
        await client.post(REGISTER_PATH, json={**payload, "name": "Jo"})

        assert PASSWORD not in captured_logs.raw

    async def test_should_not_write_the_password_to_the_logs_on_a_server_error(
        self,
        client: AsyncClient,
        payload,
        captured_logs: LogCapture,
        monkeypatch: pytest.MonkeyPatch,
    ):
        # This path renders the whole traceback, so it is the one most likely to
        # carry a credential into the log.
        async def failing_lookup(self, email: str) -> None:
            raise UserRepositoryException("An error occurred while saving user.")

        monkeypatch.setattr(UserRepository, "find_by_email", failing_lookup)

        await client.post(REGISTER_PATH, json=payload)

        assert PASSWORD not in captured_logs.raw

    async def test_should_not_write_the_stored_hash_to_the_logs(
        self,
        client: AsyncClient,
        payload,
        session: AsyncSession,
        captured_logs: LogCapture,
    ):
        await client.post(REGISTER_PATH, json=payload)

        stored = (
            await session.execute(
                select(UserModel).where(UserModel.email == payload["email"])
            )
        ).scalar_one()
        first_hash = stored.password_hash
        captured_logs.reset()

        # A second registration for a different email, so the insert and its
        # logging run again while the first hash is a live value in the table.
        await client.post(REGISTER_PATH, json={**payload, "email": "jane@doe.com"})

        assert first_hash not in captured_logs.raw

    async def test_should_not_write_a_hash_to_the_logs_on_a_conflict(
        self,
        client: AsyncClient,
        payload,
        captured_logs: LogCapture,
        monkeypatch: pytest.MonkeyPatch,
    ):
        async def pretend_the_email_is_free(self, email: str) -> None:
            return None

        await client.post(REGISTER_PATH, json=payload)
        captured_logs.reset()

        # A second request for the same email with the availability check bypassed,
        # so the insert runs and the repository reports the violation it raises.
        # Argon2 salts every hash, so the rejected hash cannot be read from the
        # table; the encoding marker is what proves whether one reached the log.
        monkeypatch.setattr(UserRepository, "find_by_email", pretend_the_email_is_free)
        response = await client.post(
            REGISTER_PATH, json={**payload, "name": "Impostor"}
        )

        assert response.status_code == 409
        assert "$argon2id$" not in captured_logs.raw
        assert "[parameters:" not in captured_logs.raw

    async def test_should_not_write_a_hash_to_the_logs_on_a_server_error(
        self,
        client: AsyncClient,
        payload,
        captured_logs: LogCapture,
        monkeypatch: pytest.MonkeyPatch,
    ):
        # The 500 path used to leak twice over: the repository logged the driver
        # message, and the exception handler rendered the traceback, which carries
        # the chained `IntegrityError` and therefore the same parameters. Forcing
        # the write to fail is what exercises both.
        async def failing_save(self, name: str, email: str, password_hash: str) -> None:
            # Mirrors what the repository does on a write failure: the domain
            # exception is raised `from` the driver error, so the chained cause
            # carries the bound parameters of the INSERT.
            try:
                await self._session.execute(
                    insert(UserModel),
                    {
                        "id": uuid4(),
                        "name": "J" * 101,
                        "email": email,
                        "password_hash": password_hash,
                    },
                )
            except SQLAlchemyError as exc:
                raise UserRepositoryException(
                    "An error occurred while saving user."
                ) from exc

        monkeypatch.setattr(UserRepository, "save", failing_save)
        captured_logs.reset()

        response = await client.post(REGISTER_PATH, json=payload)

        assert response.status_code == 500
        assert "$argon2id$" not in captured_logs.raw
        assert "[parameters:" not in captured_logs.raw
        assert "Traceback" not in captured_logs.raw


class TestRegisterUserOpenApi:
    async def test_should_document_the_endpoint(self, client: AsyncClient):
        response = await client.get("/openapi.json")

        operation = response.json()["paths"][REGISTER_PATH]["post"]

        assert operation["summary"] == "Register a new user."

    @pytest.mark.parametrize("status_code", ["201", "400", "409", "422", "500"])
    async def test_should_document_every_documented_status(
        self, client: AsyncClient, status_code: str
    ):
        response = await client.get("/openapi.json")

        responses = response.json()["paths"][REGISTER_PATH]["post"]["responses"]

        assert status_code in responses

    async def test_should_not_expose_a_password_field_in_the_request_schema(
        self, client: AsyncClient
    ):
        response = await client.get("/openapi.json")

        schema_name = (
            response.json()["paths"][REGISTER_PATH]["post"]["requestBody"]["content"][
                "application/json"
            ]["schema"]["$ref"]
        ).rsplit("/", 1)[-1]
        schema = response.json()["components"]["schemas"][schema_name]

        # `writeOnly` tells the generators this never comes back, and `format:
        # password` is what makes tooling mask it.
        password_schema = schema["properties"]["password"]

        assert password_schema["writeOnly"] is True
        assert password_schema["format"] == "password"


class TestRegisterUserCorrelationId:
    async def test_should_echo_the_correlation_id(self, client: AsyncClient, payload):
        correlation_id = str(uuid4())

        response = await client.post(
            REGISTER_PATH,
            json=payload,
            headers={"X-Correlation-ID": correlation_id},
        )

        assert response.headers["X-Correlation-ID"] == correlation_id
