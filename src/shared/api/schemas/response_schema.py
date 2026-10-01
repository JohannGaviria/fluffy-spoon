from enum import StrEnum
from typing import Any, TypeVar

from pydantic import BaseModel


class StatusEnum(StrEnum):
    """Enumeration for response status types.

    Attributes:
        SUCCESS (str): Indicates a successful response.
        ERROR (str): Indicates an error response.
    """

    SUCCESS = "success"
    ERROR = "error"


ResponseSchemaTypeVar = TypeVar("ResponseSchemaTypeVar", bound=BaseModel)


class SuccessResponseSchema[ResponseSchemaTypeVar](BaseModel):
    """Schema for successful responses.

    Attributes:
        status (StatusEnum): The status of the response, default is 'success'.
        message (str): A descriptive success message.
        data (ResponseSchemaTypeVar | None): The data payload of the response.
    """

    status: StatusEnum = StatusEnum.SUCCESS
    message: str
    data: ResponseSchemaTypeVar | None = None


class ErrorsResponseSchema(BaseModel):
    """Schema for error responses.

    Attributes:
        status (StatusEnum): The status of the response, default is 'error'.
        message (str): A descriptive error message.
        context (dict[str, Any] | None): Additional context information.
        details (list[str] | None): The individual error messages, when the
            failure maps to more than one of them.
    """

    status: StatusEnum = StatusEnum.ERROR
    message: str
    context: dict[str, Any] | None = None
    details: list[str] | None = None
