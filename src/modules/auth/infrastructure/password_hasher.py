from argon2 import PasswordHasher

from src.config import settings


class Argon2PasswordHasher:
    def __init__(self) -> None:
        self._hasher = PasswordHasher(
            time_cost=settings.ARGON2_TIME_COST,
            memory_cost=settings.ARGON2_MEMORY_COST,
            parallelism=settings.ARGON2_PARALLELISM,
        )

    def hash(self, password: str) -> str:
        """Hash a given password.

        Args:
           password (str): The password to hash.

        Returns:
           str: The hash of the given password.
        """
        return self._hasher.hash(password)
