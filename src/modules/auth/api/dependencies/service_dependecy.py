from fastapi import Depends

from src.modules.auth.api.dependencies.data_dependency import get_user_repository
from src.modules.auth.api.dependencies.infrastructure_dependency import (
    get_password_hasher,
)
from src.modules.auth.business.services.register_user_service import RegisterUserService
from src.modules.auth.data.repositories.user_repository import UserRepository
from src.modules.auth.infrastructure.password_hasher import Argon2PasswordHasher


def get_register_use_service(
    user_repository: UserRepository = Depends(get_user_repository),
    password_hasher: Argon2PasswordHasher = Depends(get_password_hasher),
) -> RegisterUserService:
    """Provide a user registration service with its dependencies.

    Args:
        user_repository: Repository used to access user data.
        password_hasher: Password hasher used to securely hash passwords.

    Returns:
        User registration service configured with its required dependencies.
    """
    return RegisterUserService(
        user_repository=user_repository,
        password_hasher=password_hasher,
    )
