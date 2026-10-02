from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class RegisterUserCommandDTO:
    name: str
    email: str
    password: str


@dataclass(frozen=True, slots=True)
class RegisterUserResponseDTO:
    id: UUID
    name: str
    email: str
    created_at: datetime
    updated_at: datetime
