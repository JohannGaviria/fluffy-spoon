from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class RegisterUserCommandDTO:
    """Command DTO for register user.

    Attributes:
        name (str): The name of the user.
        email (str): The email of the user.
        password (str): The password of the user.
    """

    name: str
    email: str
    password: str


@dataclass(frozen=True, slots=True)
class RegisterUserResponseDTO:
    """Response DTO for register user.

    Attributes:
        id (UUID): The id of the user.
        name (str): The name of the user.
        email (str): The email of the user.
        created_at (datetime): The datetime when the user was created.
        updated_at (datetime): The datetime when the user was last updated.
    """

    id: UUID
    name: str
    email: str
    created_at: datetime
    updated_at: datetime
