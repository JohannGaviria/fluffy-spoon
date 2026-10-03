import contextlib

import pytest

from src.modules.auth.business.dtos.register_user_dto import RegisterUserCommandDTO
from src.modules.auth.business.services.register_user_service import RegisterUserService
from src.modules.auth.exceptions.user_exception import (
    InvalidPasswordException,
    UserAlreadyExistsException,
    UserRepositoryException,
)
from src.shared.exceptions.exception import BaseAppException
from tests.unit.modules.auth.fakes import (
    FakeUserRepository,
    RecordingLogger,
    RecordingPasswordHasher,
    build_user_model,
)

SERVICE_MODULE = "src.modules.auth.business.services.register_user_service"

VALID_PASSWORD = "SecurePass!23"
INVALID_PASSWORD = "nouppercase1!"


def build_command(password: str = VALID_PASSWORD) -> RegisterUserCommandDTO:
    return RegisterUserCommandDTO(
        name="John Doe",
        email="john@doe.com",
        password=password,
    )


def build_service(
    repository: FakeUserRepository,
    hasher: RecordingPasswordHasher,
) -> RegisterUserService:
    return RegisterUserService(user_repository=repository, password_hasher=hasher)


@pytest.fixture
def command() -> RegisterUserCommandDTO:
    return build_command()


@pytest.fixture
def repository() -> FakeUserRepository:
    return FakeUserRepository(saved_user=build_user_model())


@pytest.fixture
def hasher() -> RecordingPasswordHasher:
    return RecordingPasswordHasher()


@pytest.fixture
def logger(monkeypatch: pytest.MonkeyPatch) -> RecordingLogger:
    recording_logger = RecordingLogger()
    monkeypatch.setattr(f"{SERVICE_MODULE}._logger", recording_logger)
    return recording_logger


@pytest.fixture
def service(
    repository: FakeUserRepository,
    hasher: RecordingPasswordHasher,
) -> RegisterUserService:
    return build_service(repository, hasher)


class TestRegisterUserServiceSuccess:
    async def test_should_return_the_persisted_user_when_registration_succeeds(
        self,
        service: RegisterUserService,
        repository: FakeUserRepository,
    ):
        persisted = repository.saved_user
        assert persisted is not None

        response = await service.execute(build_command())

        assert response.id == persisted.id
        assert response.name == persisted.name
        assert response.email == persisted.email
        assert response.created_at == persisted.created_at
        assert response.updated_at == persisted.updated_at

    async def test_should_look_the_email_up_before_saving(
        self,
        service: RegisterUserService,
        repository: FakeUserRepository,
    ):
        await service.execute(build_command())

        assert repository.find_calls == ["john@doe.com"]

    async def test_should_hash_the_password_once(
        self,
        service: RegisterUserService,
        hasher: RecordingPasswordHasher,
    ):
        await service.execute(build_command())

        assert hasher.hashed == [VALID_PASSWORD]

    async def test_should_persist_the_hash_instead_of_the_plaintext(
        self,
        service: RegisterUserService,
        repository: FakeUserRepository,
        hasher: RecordingPasswordHasher,
    ):
        await service.execute(build_command())

        persisted_hash = repository.save_calls[0]["password_hash"]
        assert persisted_hash == hasher.HASH_PREFIX
        assert VALID_PASSWORD not in persisted_hash

    async def test_should_persist_the_name_and_the_email_verbatim(
        self,
        service: RegisterUserService,
        repository: FakeUserRepository,
    ):
        await service.execute(
            RegisterUserCommandDTO(
                name="  Ada  Lovelace ",
                email="ada@lovelace.dev",
                password=VALID_PASSWORD,
            )
        )

        assert repository.save_calls[0]["name"] == "  Ada  Lovelace "
        assert repository.save_calls[0]["email"] == "ada@lovelace.dev"


class TestRegisterUserServicePasswordValidation:
    async def test_should_raise_when_the_password_is_invalid(
        self,
        service: RegisterUserService,
    ):
        with pytest.raises(InvalidPasswordException):
            await service.execute(build_command(INVALID_PASSWORD))

    async def test_should_not_query_the_repository_when_the_password_is_invalid(
        self,
        service: RegisterUserService,
        repository: FakeUserRepository,
    ):
        with pytest.raises(InvalidPasswordException):
            await service.execute(build_command(INVALID_PASSWORD))

        # Validating first keeps the endpoint from answering differently for a
        # weak password and for a registered email, which would let a caller
        # probe which emails exist.
        assert repository.find_calls == []

    async def test_should_not_hash_the_password_when_it_is_invalid(
        self,
        service: RegisterUserService,
        hasher: RecordingPasswordHasher,
    ):
        with pytest.raises(InvalidPasswordException):
            await service.execute(build_command(INVALID_PASSWORD))

        assert hasher.hashed == []

    async def test_should_not_persist_when_the_password_is_invalid(
        self,
        service: RegisterUserService,
        repository: FakeUserRepository,
    ):
        with pytest.raises(InvalidPasswordException):
            await service.execute(build_command(INVALID_PASSWORD))

        assert repository.save_calls == []


class TestRegisterUserServiceDuplicateEmail:
    @pytest.fixture
    def repository(self) -> FakeUserRepository:
        return FakeUserRepository(existing_user=build_user_model())

    async def test_should_raise_when_the_email_is_already_registered(
        self,
        service: RegisterUserService,
    ):
        with pytest.raises(UserAlreadyExistsException):
            await service.execute(build_command())

    async def test_should_not_save_when_the_email_is_already_registered(
        self,
        service: RegisterUserService,
        repository: FakeUserRepository,
    ):
        with pytest.raises(UserAlreadyExistsException):
            await service.execute(build_command())

        assert repository.save_calls == []

    async def test_should_not_hash_when_the_email_is_already_registered(
        self,
        service: RegisterUserService,
        hasher: RecordingPasswordHasher,
    ):
        with pytest.raises(UserAlreadyExistsException):
            await service.execute(build_command())

        assert hasher.hashed == []


class TestRegisterUserServiceRepositoryErrors:
    async def test_should_propagate_a_unique_violation_from_the_repository(
        self,
        hasher: RecordingPasswordHasher,
    ):
        # A concurrent registration can win the race after the lookup, so the
        # repository reports the conflict too. The service has to let it through
        # untouched, otherwise the handler would answer 500 for a 409 case.
        repository = FakeUserRepository(save_error=UserAlreadyExistsException())
        service = build_service(repository, hasher)

        with pytest.raises(UserAlreadyExistsException):
            await service.execute(build_command())

    async def test_should_propagate_a_save_failure_without_wrapping_it(
        self,
        hasher: RecordingPasswordHasher,
    ):
        failure = UserRepositoryException("An error occurred while saving user.")
        repository = FakeUserRepository(save_error=failure)
        service = build_service(repository, hasher)

        with pytest.raises(UserRepositoryException) as exc_info:
            await service.execute(build_command())

        assert exc_info.value is failure

    async def test_should_propagate_a_lookup_failure_without_wrapping_it(
        self,
        hasher: RecordingPasswordHasher,
    ):
        failure = UserRepositoryException(
            "An error occurred while retrieving user by email address."
        )
        repository = FakeUserRepository(find_error=failure)
        service = build_service(repository, hasher)

        with pytest.raises(UserRepositoryException) as exc_info:
            await service.execute(build_command())

        assert exc_info.value is failure
        assert repository.save_calls == []

    async def test_should_let_an_unexpected_error_through_untouched(
        self,
        hasher: RecordingPasswordHasher,
    ):
        repository = FakeUserRepository(save_error=RuntimeError("boom"))
        service = build_service(repository, hasher)

        # Not a `BaseAppException`, so the service neither logs nor rewrites it
        # and the shared handler answers with the generic 500.
        with pytest.raises(RuntimeError, match="boom"):
            await service.execute(build_command())


class TestRegisterUserServiceLogging:
    async def test_should_log_the_successful_registration(
        self,
        service: RegisterUserService,
        logger: RecordingLogger,
    ):
        await service.execute(build_command())

        assert ("info", "User registered successfully.", {"email": "john@doe.com"}) in (
            logger.calls
        )

    async def test_should_log_the_conflict_when_the_email_is_already_registered(
        self,
        hasher: RecordingPasswordHasher,
        logger: RecordingLogger,
    ):
        repository = FakeUserRepository(existing_user=build_user_model())
        service = build_service(repository, hasher)

        with pytest.raises(UserAlreadyExistsException):
            await service.execute(build_command())

        assert ("error", "User already exists.", {"email": "john@doe.com"}) in (
            logger.calls
        )

    @pytest.mark.parametrize(
        "repository",
        [
            FakeUserRepository(existing_user=build_user_model()),
            FakeUserRepository(save_error=UserRepositoryException("failed")),
            FakeUserRepository(find_error=UserRepositoryException("failed")),
        ],
        ids=["conflict", "save_failure", "lookup_failure"],
    )
    async def test_should_log_the_violated_business_rule(
        self,
        repository: FakeUserRepository,
        hasher: RecordingPasswordHasher,
        logger: RecordingLogger,
    ):
        service = build_service(repository, hasher)

        with pytest.raises(BaseAppException):
            await service.execute(build_command())

        assert [message for _, message, _ in logger.calls_at("warning")] == [
            "Business rule violated while registering user."
        ]

    @pytest.mark.parametrize(
        "repository",
        [
            FakeUserRepository(saved_user=build_user_model()),
            FakeUserRepository(existing_user=build_user_model()),
            FakeUserRepository(save_error=RuntimeError("boom")),
        ],
        ids=["success", "conflict", "unexpected_error"],
    )
    async def test_should_log_the_completion_on_every_path(
        self,
        repository: FakeUserRepository,
        hasher: RecordingPasswordHasher,
        logger: RecordingLogger,
    ):
        service = build_service(repository, hasher)

        with contextlib.suppress(BaseAppException, RuntimeError):
            await service.execute(build_command())

        assert logger.calls_at("debug") == [
            ("debug", "Executed: Register user service.", {})
        ]

    @pytest.mark.parametrize(
        "repository",
        [
            FakeUserRepository(saved_user=build_user_model()),
            FakeUserRepository(existing_user=build_user_model()),
            FakeUserRepository(save_error=UserRepositoryException("failed")),
            FakeUserRepository(find_error=UserRepositoryException("failed")),
        ],
        ids=["success", "conflict", "save_failure", "lookup_failure"],
    )
    async def test_should_never_write_the_password_to_the_logs(
        self,
        repository: FakeUserRepository,
        hasher: RecordingPasswordHasher,
        logger: RecordingLogger,
    ):
        service = build_service(repository, hasher)

        with contextlib.suppress(BaseAppException, RuntimeError):
            await service.execute(build_command())

        assert VALID_PASSWORD not in logger.rendered()
        assert hasher.HASH_PREFIX not in logger.rendered()
