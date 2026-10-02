from src.modules.auth.business.dtos.register_user_dto import (
    RegisterUserCommandDTO,
    RegisterUserResponseDTO,
)
from src.modules.auth.business.policies.password_validation_policie import (
    PasswordValidationPolicy,
)
from src.modules.auth.data.repositories.user_repository import UserRepository
from src.modules.auth.exceptions.user_exception import UserAlreadyExistsException
from src.modules.auth.infrastructure.password_hasher import Argon2PasswordHasher
from src.shared.exceptions.exception import BaseAppException
from src.shared.infrastructure.logging.structlog_logger import StructlogLogger

_logger = StructlogLogger(__name__)


class RegisterUserService:
    def __init__(
        self,
        user_repository: UserRepository,
        password_hasher: Argon2PasswordHasher,
    ) -> None:
        """Initialize the Register User Service.

        Args:
            user_repository (UserRepository): Repository used to query and persist users.
            password_hasher (PasswordHasher): Service used to securely hash user passwords.
        """
        self._repo = user_repository
        self._password_hasher = password_hasher
        self._password_validation_policy = PasswordValidationPolicy()

    async def execute(self, command: RegisterUserCommandDTO) -> RegisterUserResponseDTO:
        """Register a new user.

        Validates the provided password, verifies that the email is not
        already registered, hashes the password, and persists the new user.

        Args:
            command: Registration data containing the user's name, email, and plain-text password.

        Returns:
            RegisterUserResponseDTO: The registered user's data, including its generated identifier
            and timestamps.

        Raises:
            UserAlreadyExistsException: If a user with the provided email already exists.
            BaseAppException: If a business rule is violated during registration.
        """
        try:
            self._password_validation_policy.validate(command.password)

            exists_user = await self._repo.find_by_email(command.email)

            if exists_user is not None:
                _logger.error("User already exists.", email=command.email)
                raise UserAlreadyExistsException()

            password_hash = self._password_hasher.hash(command.password)

            user = await self._repo.save(
                name=command.name, email=command.email, password_hash=password_hash
            )

            _logger.info("User registered successfully.", email=command.email)

            return RegisterUserResponseDTO(
                id=user.id,
                name=user.name,
                email=user.email,
                created_at=user.created_at,
                updated_at=user.updated_at,
            )

        except BaseAppException as exc:
            _logger.warning(
                "Business rule violated while registering user.",
                error=str(exc),
                email=command.email,
            )
            raise

        finally:
            _logger.debug("Executed: Register user service.")
