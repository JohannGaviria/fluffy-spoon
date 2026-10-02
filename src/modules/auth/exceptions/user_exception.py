from src.shared.exceptions.exception import BaseAppException


class UserRepositoryException(BaseAppException):
    """Exception raised for errors in user repository."""

    def __init__(self, error: str) -> None:
        """Initializes UserRepositoryException.

        Args:
            error (str): Error message.
        """
        self.error = error
        super().__init__("Error while interacting with the user repository.")


class InvalidPasswordException(BaseAppException):
    """Exception raised when password is invalid."""

    def __init__(self, error: str) -> None:
        """Initialize the InvalidPasswordException.

        Args:
            error (str): The error message.
        """
        self.error = error
        super().__init__("The password is invalid.")
