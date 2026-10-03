from fastapi import APIRouter, Depends, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from src.modules.auth.api.dependencies.service_dependecy import get_register_use_service
from src.modules.auth.api.mappers.register_user_mapper import RegisterUserMapper
from src.modules.auth.api.schemas.register_user_schema import (
    RegisterUserRequestSchema,
    RegisterUserResponseSchema,
)
from src.modules.auth.business.services.register_user_service import RegisterUserService
from src.shared.api.schemas.response_schema import (
    ErrorsResponseSchema,
    SuccessResponseSchema,
)

router = APIRouter()


@router.post(
    path="/register",
    summary="Register a new user.",
    description="Creates a new user account with the provided credentials.",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {
            "model": SuccessResponseSchema[RegisterUserResponseSchema],
            "description": "User registered successfully.",
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorsResponseSchema,
            "description": "The request contains invalid data.",
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorsResponseSchema,
            "description": "A user with the provided email already exists.",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "model": ErrorsResponseSchema,
            "description": "The request data failed validation.",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorsResponseSchema,
            "description": "An unexpected error occurred while registering the user.",
        },
    },
)
async def register_user(
    request: RegisterUserRequestSchema,
    service: RegisterUserService = Depends(get_register_use_service),
) -> JSONResponse:
    """Register a new user.

    This endpoint will create a new user account with the provided credentials.

    Args:
        request (RegisterUserRequestSchema): Request schema with user details.
        service (RegisterUserService): Service used to register new user.

    Returns:
        JSONResponse: Response with user details.
    """
    response = await service.execute(RegisterUserMapper.to_command(request))
    return JSONResponse(
        content=jsonable_encoder(
            SuccessResponseSchema(
                message="User successfully registered.",
                data=RegisterUserMapper.to_response(response),
            )
        ),
        status_code=status.HTTP_201_CREATED,
    )
