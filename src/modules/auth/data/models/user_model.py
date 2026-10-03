from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.data.models.base_model import BaseModel


class UserModel(BaseModel):
    """SQLAlchemy User Model.

    Attributes:
        id (UUID): The user ID.
        name (str): The name of the user.
        email (str): The email of the user.
        password_hash (str): The password hash of the user.
        created_at (datetime): The date and time the user was created.
        updated_at (datetime): The date and time the user was last updated.
    """

    __tablename__ = "users"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
