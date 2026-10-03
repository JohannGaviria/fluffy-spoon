from src.modules.auth.infrastructure.password_hasher import Argon2PasswordHasher


def get_password_hasher() -> Argon2PasswordHasher:
    """Provide a password hasher for securely hashing passwords.

    Returns:
        Password hasher configured to use Argon2.
    """
    return Argon2PasswordHasher()
