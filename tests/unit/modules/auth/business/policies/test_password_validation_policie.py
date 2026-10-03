import pytest
from faker import Faker

from src.modules.auth.business.policies.password_validation_policie import (
    PasswordValidationPolicy,
)
from src.modules.auth.exceptions.user_exception import InvalidPasswordException


def build_valid_password(faker: Faker) -> str:
    return faker.password(
        length=12, special_chars=True, digits=True, upper_case=True, lower_case=True
    )


class TestPasswordValidationPolicy:
    def test_should_accept_a_password_meeting_every_rule(self, faker: Faker):
        policy = PasswordValidationPolicy()
        password = build_valid_password(faker)

        policy.validate(password)

    @pytest.mark.parametrize(
        "password",
        [
            "SECUREPASS!23",
            "A1!AAAA",
            "XX9$ZZZZ",
        ],
    )
    def test_should_raise_when_the_password_has_no_lowercase_letter(
        self, password: str
    ):
        policy = PasswordValidationPolicy()

        with pytest.raises(InvalidPasswordException) as exc_info:
            policy.validate(password)

        assert exc_info.value.error == "Password must contain a lowercase letter."

    @pytest.mark.parametrize(
        "password",
        [
            "securepass!23",
            "a1!aaaa",
            "xx9$zzzz",
        ],
    )
    def test_should_raise_when_the_password_has_no_uppercase_letter(
        self, password: str
    ):
        policy = PasswordValidationPolicy()

        with pytest.raises(InvalidPasswordException) as exc_info:
            policy.validate(password)

        assert exc_info.value.error == "Password must contain an uppercase letter."

    @pytest.mark.parametrize(
        "password",
        [
            "SecurePass!ab",
            "Aa!!aaaa",
            "XXyy$$zz",
        ],
    )
    def test_should_raise_when_the_password_has_no_digit(self, password: str):
        policy = PasswordValidationPolicy()

        with pytest.raises(InvalidPasswordException) as exc_info:
            policy.validate(password)

        assert exc_info.value.error == "Password must contain a digit."

    @pytest.mark.parametrize(
        "password",
        [
            "SecurePass123",
            "Aa1aaaaaa",
            "XX9yzzzzz",
        ],
    )
    def test_should_raise_when_the_password_has_no_special_character(
        self, password: str
    ):
        policy = PasswordValidationPolicy()

        with pytest.raises(InvalidPasswordException) as exc_info:
            policy.validate(password)

        assert exc_info.value.error == "Password must contain a special character."

    @pytest.mark.parametrize(
        "special_character",
        list(PasswordValidationPolicy._SPECIAL_CHARS),
    )
    def test_should_accept_every_documented_special_character(
        self, special_character: str, faker: Faker
    ):
        policy = PasswordValidationPolicy()
        letters = faker.password(
            length=6,
            special_chars=False,
            digits=False,
            upper_case=False,
            lower_case=True,
        )

        policy.validate(f"Ab1{special_character}{letters}")

    @pytest.mark.parametrize(
        "password",
        [
            "",
            "1234567!",
            "!!!!!!!!",
        ],
    )
    def test_should_report_the_lowercase_rule_first_when_it_is_the_missing_one(
        self, password: str
    ):
        policy = PasswordValidationPolicy()

        with pytest.raises(InvalidPasswordException) as exc_info:
            policy.validate(password)

        assert exc_info.value.error == "Password must contain a lowercase letter."

    def test_should_report_the_uppercase_rule_when_only_that_one_is_missing(
        self, faker: Faker
    ):
        policy = PasswordValidationPolicy()
        letters = faker.password(
            length=6,
            special_chars=False,
            digits=False,
            upper_case=False,
            lower_case=True,
        )
        password = f"abc1!{letters}"

        with pytest.raises(InvalidPasswordException) as exc_info:
            policy.validate(password)

        assert exc_info.value.error == "Password must contain an uppercase letter."

    def test_should_report_the_digit_rule_when_only_that_one_is_missing(
        self, faker: Faker
    ):
        policy = PasswordValidationPolicy()
        letters = faker.password(
            length=6,
            special_chars=False,
            digits=False,
            upper_case=False,
            lower_case=True,
        )
        password = f"Abc!{letters}"

        with pytest.raises(InvalidPasswordException) as exc_info:
            policy.validate(password)

        assert exc_info.value.error == "Password must contain a digit."

    @pytest.mark.parametrize(
        "password",
        [
            "Ab1!defg",
            "Ab1!def",
            "Ab1!de",
        ],
    )
    def test_should_not_enforce_the_documented_length_range(self, password: str):
        policy = PasswordValidationPolicy()

        policy.validate(password)

    def test_should_accept_a_non_ascii_letter_as_a_case_character(self, faker: Faker):
        policy = PasswordValidationPolicy()
        letters = faker.password(
            length=6,
            special_chars=False,
            digits=False,
            upper_case=False,
            lower_case=True,
        )

        policy.validate(f"Ábc1!{letters}")
