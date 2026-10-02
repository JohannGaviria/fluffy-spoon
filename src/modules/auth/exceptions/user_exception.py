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
