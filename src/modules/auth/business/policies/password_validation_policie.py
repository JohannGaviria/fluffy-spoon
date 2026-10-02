from src.modules.auth.exceptions.user_exception import InvalidPasswordException


class PasswordValidationPolicy:
    _SPECIAL_CHARS = "!@#$%^&*()-_=+[]{};:,.<>/?"

    def validate(self, password: str) -> None:
        """Validate the password provided.

        The password must include at least one uppercase letter,
        one lowercase letter, a number, and a special character.

        Args:
            password (str): The password provided for validation.
        """
        if not any(c.islower() for c in password):
            raise InvalidPasswordException("Password must contain a lowercase letter.")

        if not any(c.isupper() for c in password):
            raise InvalidPasswordException("Password must contain an uppercase letter.")

        if not any(c.isdigit() for c in password):
            raise InvalidPasswordException("Password must contain a digit.")

        if not any(c in self._SPECIAL_CHARS for c in password):
            raise InvalidPasswordException("Password must contain a special character.")
