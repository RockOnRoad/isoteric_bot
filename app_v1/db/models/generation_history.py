from enum import Enum as PyEnum
from typing import TYPE_CHECKING, Any, Literal

from sqlalchemy import (
    String,
    BigInteger,
    ForeignKey,
    Integer,
    Enum,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.models.base import Base


class GenStatus(str, PyEnum):
    success = "success"
    error = "error"
    not_enough_balance = "not_enough_balance"
    already_generated_today = "already_generated_today"


if TYPE_CHECKING:
    from .user import User


class GenerationHistory(Base):
    """Generation history model."""

    __tablename__ = "generation_history"

    #  ID пользователя
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE")
    )
    #  Модель, которая использовалась
    model: Mapped[str] = mapped_column(String)
    #  Описание запроса, который ввел клиент
    request: Mapped[dict[str, Any]] = mapped_column(JSONB)
    #  Стоимость в кредитах
    cost: Mapped[int] = mapped_column(Integer)
    #  Статус генерации
    gen_status: Mapped[GenStatus] = mapped_column(
        Enum(GenStatus, name="gen_status_enum")
    )
    #  Тип генерации в зависимости от бота
    gen_type: Mapped[str] = mapped_column(String)

    #  Связь с пользователем
    user: Mapped["User"] = relationship("User", back_populates="generation_history")
