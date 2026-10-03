import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient, Response

from src.modules.auth.api.exceptions.user_exception_handlers import (
    register_user_exception_handlers,
)
from src.modules.auth.exceptions.user_exception import (
    InvalidPasswordException,
    UserAlreadyExistsException,
    UserRepositoryException,
)

SECRET = "SecurePass!23"
REGISTER_PATH = "/api/v1/auth/register"


async def post_to_handler(exception: Exception) -> Response:
    """Drive a route that raises `exception` through the real handlers."""
    app = FastAPI()
    register_user_exception_handlers(app)

    @app.post(REGISTER_PATH)
    async def failing_route() -> None:
        raise exception

    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post(REGISTER_PATH)


class TestUserAlreadyExistsHandler:
    async def test_should_answer_409_conflict(self):
        response = await post_to_handler(UserAlreadyExistsException())

        assert response.status_code == 409

    async def test_should_answer_the_error_envelope(self):
        response = await post_to_handler(UserAlreadyExistsException())

        assert response.json() == {
            "status": "error",
            "message": "User already exists.",
        }

    async def test_should_not_include_a_details_field(self):
        response = await post_to_handler(UserAlreadyExistsException())

        # A conflict has no single offending field, so `details` is left out
        # rather than serialized as null.
        assert "details" not in response.json()


class TestUserRepositoryHandler:
    async def test_should_answer_500_internal_server_error(self):
        response = await post_to_handler(
            UserRepositoryException("An error occurred while saving user.")
        )

        assert response.status_code == 500

    async def test_should_answer_the_generic_message_and_the_detail(self):
        response = await post_to_handler(
            UserRepositoryException("An error occurred while saving user.")
        )

        assert response.json() == {
            "status": "error",
            "message": "Error while interacting with the user repository.",
            "details": "An error occurred while saving user.",
        }


class TestInvalidPasswordHandler:
    async def test_should_answer_400_bad_request(self):
        response = await post_to_handler(
            InvalidPasswordException("Password must contain an uppercase letter.")
        )

        assert response.status_code == 400

    async def test_should_answer_the_generic_message_and_the_detail(self):
        response = await post_to_handler(
            InvalidPasswordException("Password must contain an uppercase letter.")
        )

        assert response.json() == {
            "status": "error",
            "message": "The password is invalid.",
            "details": "Password must contain an uppercase letter.",
        }

    async def test_should_tell_the_caller_which_rule_failed(self):
        response = await post_to_handler(
            InvalidPasswordException("Password must contain a digit.")
        )

        # A 400 that only says "invalid" would leave the caller guessing which
        # of the four rules to fix.
        assert "digit" in response.json()["details"]


class TestHandlersDoNotLeakSecrets:
    @pytest.mark.parametrize(
        "exception",
        [
            UserAlreadyExistsException(),
            UserRepositoryException("An error occurred while saving user."),
            InvalidPasswordException("Password must contain a digit."),
        ],
        ids=["conflict", "repository_failure", "invalid_password"],
    )
    async def test_should_never_answer_with_a_traceback_or_a_password(
        self, exception: Exception
    ):
        response = await post_to_handler(exception)

        assert "Traceback" not in response.text
        assert SECRET not in response.text
        assert "user_exception" not in response.text
