from datetime import timezone
from uuid import UUID

import pytest
from faker import Faker
from pydantic import ValidationError

from src.modules.auth.api.schemas.register_user_schema import (
    RegisterUserRequestSchema,
    RegisterUserResponseSchema,
)


def build_payload(faker: Faker, **overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "name": faker.name(),
        "email": faker.email(),
        "password": faker.password(length=12),
    }
    payload.update(overrides)

    return payload


def build_response_payload(faker: Faker, **overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "id": faker.uuid4(),
        "name": faker.name(),
        "email": faker.email(),
        "created_at": faker.date_time(tzinfo=timezone.utc),
        "updated_at": faker.date_time(tzinfo=timezone.utc),
    }
    payload.update(overrides)

    return payload


class TestRegisterUserRequestSchema:
    def test_should_accept_a_valid_payload(self, faker: Faker):
        payload = build_payload(faker)

        request = RegisterUserRequestSchema(**payload)

        assert request.name == payload["name"]
        assert request.email == payload["email"]
        assert request.password.get_secret_value() == payload["password"]

    @pytest.mark.parametrize(
        "name",
        [
            "Jo",
            "J",
            "",
            " ",
            "J" * 101,
        ],
        ids=["two_chars", "one_char", "empty", "blank", "one_hundred_and_one"],
    )
    def test_should_reject_a_name_outside_the_three_to_one_hundred_range(
        self, faker: Faker, name: str
    ):
        with pytest.raises(ValidationError):
            RegisterUserRequestSchema(**build_payload(faker, name=name))

    @pytest.mark.parametrize(
        "name",
        ["Joh", "John Doe", "J" * 100],
        ids=["three_chars", "typical", "one_hundred"],
    )
    def test_should_accept_the_name_boundaries(self, faker: Faker, name: str):
        request = RegisterUserRequestSchema(**build_payload(faker, name=name))

        assert request.name == name

    @pytest.mark.parametrize(
        "email",
        [
            "not-an-email",
            "john@",
            "@doe.com",
            "john doe@doe.com",
            "john@doe",
            "john@@doe.com",
            "",
        ],
    )
    def test_should_reject_a_malformed_email(self, faker: Faker, email: str):
        with pytest.raises(ValidationError):
            RegisterUserRequestSchema(**build_payload(faker, email=email))

    @pytest.mark.parametrize(
        "password",
        ["", "Ab1!", "Ab1!de", "Ab1!def", "Ab1!" + "a" * 13, "A" * 17],
        ids=["empty", "four", "six", "seven", "seventeen", "seventeen_same_char"],
    )
    def test_should_reject_a_password_outside_the_eight_to_sixteen_range(
        self, faker: Faker, password: str
    ):
        with pytest.raises(ValidationError):
            RegisterUserRequestSchema(**build_payload(faker, password=password))

    @pytest.mark.parametrize(
        "password",
        ["Ab1!defg", "SecurePass!23", "Ab1!" + "a" * 12],
        ids=["eight_chars", "typical", "sixteen_chars"],
    )
    def test_should_accept_the_password_boundaries(self, faker: Faker, password: str):
        request = RegisterUserRequestSchema(**build_payload(faker, password=password))

        assert request.password.get_secret_value() == password

    @pytest.mark.parametrize("missing", ["name", "email", "password"])
    def test_should_reject_a_payload_missing_a_required_field(
        self, faker: Faker, missing: str
    ):
        payload = build_payload(faker)
        del payload[missing]

        with pytest.raises(ValidationError):
            RegisterUserRequestSchema(**payload)

    @pytest.mark.parametrize("field", ["name", "email", "password"])
    def test_should_reject_a_field_of_the_wrong_type(self, faker: Faker, field: str):
        with pytest.raises(ValidationError):
            RegisterUserRequestSchema(
                **build_payload(faker, **{field: {"nested": "value"}})
            )


class TestRegisterUserResponseSchema:
    def test_should_accept_a_valid_payload(self, faker: Faker):
        payload = build_response_payload(faker)

        response = RegisterUserResponseSchema(**payload)

        assert response.id == UUID(str(payload["id"]))
        assert response.name == payload["name"]
        assert response.email == payload["email"]
        assert response.created_at == payload["created_at"]
        assert response.updated_at == payload["updated_at"]

    @pytest.mark.parametrize(
        "invalid_id",
        ["not-a-uuid", "1234", "", None],
        ids=["text", "digits", "empty", "none"],
    )
    def test_should_reject_an_id_that_is_not_a_uuid(
        self, faker: Faker, invalid_id: object
    ):
        with pytest.raises(ValidationError):
            RegisterUserResponseSchema(**build_response_payload(faker, id=invalid_id))

    def test_should_reject_a_malformed_email(self, faker: Faker):
        with pytest.raises(ValidationError):
            RegisterUserResponseSchema(
                **build_response_payload(faker, email="not-an-email")
            )

    @pytest.mark.parametrize("missing", ["id", "name", "email", "created_at"])
    def test_should_reject_a_payload_missing_a_field(self, faker: Faker, missing: str):
        payload = build_response_payload(faker)
        del payload[missing]

        with pytest.raises(ValidationError):
            RegisterUserResponseSchema(**payload)


class TestRequestSchemaSecretHandling:
    def test_should_mask_the_password_in_the_repr(self, faker: Faker):
        password = faker.password(length=12)
        request = RegisterUserRequestSchema(**build_payload(faker, password=password))

        assert password not in repr(request)
        assert "**********" in repr(request)

    def test_should_mask_the_password_in_the_serialized_json(self, faker: Faker):
        password = faker.password(length=12)
        request = RegisterUserRequestSchema(**build_payload(faker, password=password))

        assert password not in request.model_dump_json()

    def test_should_keep_the_password_unreadable_through_the_field(self, faker: Faker):
        password = faker.password(length=12)
        request = RegisterUserRequestSchema(**build_payload(faker, password=password))

        assert password not in str(request.password)
        assert request.password.get_secret_value() == password
