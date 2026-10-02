from src.modules.auth.api.schemas.register_user_schema import (
    RegisterUserRequestSchema,
    RegisterUserResponseSchema,
)
from src.modules.auth.business.dtos.register_user_dto import (
    RegisterUserCommandDTO,
    RegisterUserResponseDTO,
)


class RegisterUserMapper:
    @staticmethod
    def to_command(request: RegisterUserRequestSchema) -> RegisterUserCommandDTO:
        """Convert the request schema to a command DTO.

        Args:
            request (RegisterUserRequestSchema): Request schema with user details.

        Returns:
            RegisterUserCommandDTO: Converted command DTO.
        """
        return RegisterUserCommandDTO(
            name=request.name,
            email=request.email,
            password=request.password.get_secret_value(),
        )

    @staticmethod
    def to_response(response: RegisterUserResponseDTO) -> RegisterUserResponseSchema:
        """Convert the response DTO to a response schema.

        Args:
            response (RegisterUserResponseDTO): Response DTO with user details.

        Returns:
            RegisterUserResponseSchema: Converted response schema.
        """
        return RegisterUserResponseSchema(
            id=response.id,
            name=response.name,
            email=response.email,
            created_at=response.created_at,
            updated_at=response.updated_at,
        )
