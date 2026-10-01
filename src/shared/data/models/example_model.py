from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.data.models.base_model import BaseModel


class ExampleModel(BaseModel):
    """Example SQLAlchemy model for project scaffolding.

    Replace or remove this model when implementing the actual domain models.
    """

    __tablename__ = "example"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
