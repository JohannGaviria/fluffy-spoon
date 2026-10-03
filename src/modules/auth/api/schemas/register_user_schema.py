from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, EmailStr, Field, SecretStr


class RegisterUserRequestSchema(BaseModel):
    """Request schema for user registration.

    Attributes:
        name (str): name of the user for registration.
        email (str): email of the user for registration.
        password (str): password of the user for registration.
    """

    name: str = Field(min_length=3, max_length=100)
    email: EmailStr
    password: SecretStr = Field(min_length=8, max_length=16)

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "John Doe",
                "email": "john@doe.com",
                "password": "SecurePass!23",
            }
        }
    }


class RegisterUserResponseSchema(BaseModel):
    """Response schema for user registration.

    Attributes:
        id (UUID): registered user id.
        name (str): registered user name.
        email (str): registered user email.
        created_at (datetime): registered user created at.
        updated_at (datetime): registered user updated at.
    """

    id: UUID
    name: str
    email: EmailStr
    created_at: datetime
    updated_at: datetime

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": str(uuid4()),
                "name": "John Doe",
                "email": "john@doe.com",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }
        }
    }
