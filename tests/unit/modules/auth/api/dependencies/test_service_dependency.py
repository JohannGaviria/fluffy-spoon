from src.modules.auth.api.dependencies.service_dependecy import get_register_use_service
from src.modules.auth.business.services.register_user_service import RegisterUserService
from src.modules.auth.data.repositories.user_repository import UserRepository
from src.modules.auth.infrastructure.password_hasher import Argon2PasswordHasher
from tests.unit.modules.auth.fakes import FakeAsyncSession


class TestGetRegisterUserService:
    def test_should_return_a_register_user_service(self):
        repository = UserRepository(session=FakeAsyncSession())
        hasher = Argon2PasswordHasher()

        service = get_register_use_service(
            user_repository=repository,
            password_hasher=hasher,
        )

        assert isinstance(service, RegisterUserService)

    def test_should_wire_the_repository_and_the_hasher_into_the_service(self):
        repository = UserRepository(session=FakeAsyncSession())
        hasher = Argon2PasswordHasher()

        service = get_register_use_service(
            user_repository=repository,
            password_hasher=hasher,
        )

        assert service._repo is repository
        assert service._password_hasher is hasher
