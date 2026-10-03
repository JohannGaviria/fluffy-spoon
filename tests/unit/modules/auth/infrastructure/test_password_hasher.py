import pytest
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from faker import Faker

from src.config import settings
from src.modules.auth.infrastructure.password_hasher import Argon2PasswordHasher


@pytest.fixture
def hasher() -> Argon2PasswordHasher:
    return Argon2PasswordHasher()


@pytest.fixture
def strong_password(faker: Faker) -> str:
    return faker.password(
        length=16,
        special_chars=True,
        digits=True,
        upper_case=True,
        lower_case=True,
    )


class TestArgon2PasswordHasher:
    def test_should_return_an_argon2id_hash(
        self, strong_password: str, hasher: Argon2PasswordHasher
    ):
        password_hash = hasher.hash(strong_password)

        assert password_hash.startswith("$argon2id$")

    def test_should_never_return_the_plaintext_password(
        self, strong_password: str, hasher: Argon2PasswordHasher
    ):
        password_hash = hasher.hash(strong_password)

        assert strong_password not in password_hash

    def test_should_produce_a_hash_that_verifies_against_the_password(
        self, strong_password: str, hasher: Argon2PasswordHasher
    ):
        password_hash = hasher.hash(strong_password)

        # Verified with a hasher built independently, so this asserts the stored
        # value is really usable for login rather than just well shaped.
        assert PasswordHasher().verify(password_hash, strong_password) is True

    def test_should_reject_a_password_that_does_not_match(
        self, strong_password: str, hasher: Argon2PasswordHasher
    ):
        password_hash = hasher.hash(strong_password)

        with pytest.raises(VerifyMismatchError):
            PasswordHasher().verify(password_hash, "AnotherPass!23")

    def test_should_salt_every_hash(
        self, strong_password: str, hasher: Argon2PasswordHasher
    ):
        first = hasher.hash(strong_password)
        second = hasher.hash(strong_password)

        # Two identical passwords must not produce identical rows, otherwise the
        # table leaks which accounts share a password.
        assert first != second

    def test_should_encode_the_configured_time_cost(
        self, strong_password: str, hasher: Argon2PasswordHasher
    ):
        password_hash = hasher.hash(strong_password)

        assert f"m={settings.ARGON2_MEMORY_COST}" in password_hash
        assert f"t={settings.ARGON2_TIME_COST}" in password_hash
        assert f"p={settings.ARGON2_PARALLELISM}" in password_hash
