from datetime import datetime

from sqlalchemy import Integer, DateTime, func, MetaData
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column

from core.config import settings


class Base(DeclarativeBase):
    """Base class for all models."""

    __abstract__ = True

    metadata = MetaData(naming_convention=settings.naming_convention)

    #  Присваевает __tablename__ с окончанием 's' всем дочерним моделям
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return f"{cls.__name__.lower()}s"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
