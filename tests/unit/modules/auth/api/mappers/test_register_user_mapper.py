from typing import Any
from uuid import UUID

from faker import Faker

from src.modules.auth.api.mappers.register_user_mapper import RegisterUserMapper
from src.modules.auth.api.schemas.register_user_schema import (
    RegisterUserRequestSchema,
    RegisterUserResponseSchema,
)
from src.modules.auth.business.dtos.register_user_dto import RegisterUserResponseDTO


def build_request(
    faker: Faker,
    **overrides: object,
) -> RegisterUserRequestSchema:
    payload: dict[str, Any] = {
        "name": faker.name(),
        "email": faker.email(),
        "password": faker.password(length=12),
    }
    payload.update(overrides)

    return RegisterUserRequestSchema(**payload)


def build_response(
    faker: Faker,
    **overrides: object,
) -> RegisterUserResponseDTO:
    payload: dict[str, Any] = {
        "id": UUID(faker.uuid4()),
        "name": faker.name(),
        "email": faker.email(),
        "created_at": faker.date_time(tzinfo=None),
        "updated_at": faker.date_time(tzinfo=None),
    }
    payload.update(overrides)

    return RegisterUserResponseDTO(**payload)


class TestRegisterUserMapperToCommand:
    def test_should_map_the_name_and_the_email(self, faker: Faker):
        request = build_request(faker)

        command = RegisterUserMapper.to_command(request)

        assert command.name == request.name
        assert command.email == request.email

    def test_should_unwrap_the_password_secret(self, faker: Faker):
        request = build_request(faker)

        command = RegisterUserMapper.to_command(request)

        assert command.password == request.password.get_secret_value()


class TestRegisterUserMapperToResponse:
    def test_should_map_every_field_of_the_dto(self, faker: Faker):
        dto = build_response(faker)

        response = RegisterUserMapper.to_response(dto)

        assert isinstance(response, RegisterUserResponseSchema)
        assert response.id == dto.id
        assert response.name == dto.name
        assert response.email == dto.email
        assert response.created_at == dto.created_at
        assert response.updated_at == dto.updated_at
