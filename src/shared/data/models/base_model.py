from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""

    pass


class BaseModel(Base):
    """Base model for all entities in the application.

    This model includes common fields such as `id`, `created_at`, and `updated_at`.

    Attributes:
        id (UUID): Unique identifier for the entity.
        created_at (datetime): Timestamp when the entity was created.
        updated_at (datetime): Timestamp when the entity was last updated.
    """

    __abstract__ = True

    id: Mapped[UUID] = mapped_column(
        primary_key=True, unique=True, index=True, default=uuid4
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        index=True,
    )
