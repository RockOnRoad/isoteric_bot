from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, Boolean, BigInteger, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.models.base import Base

if TYPE_CHECKING:
    from .user import User


class GenerationHistory(Base):
    """Generation history model."""

    __tablename__ = "generation_history"

    #  Telegram ID пользователя
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE")
    )
    #  Время генерации
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    #  Модель, которая использовалась
    model: Mapped[str] = mapped_column(String)
    #  Описание запроса, который ввел клиент
    request: Mapped[str] = mapped_column(Text)
    #  Стоимость в кредитах
    cost: Mapped[int] = mapped_column(Integer)
    #  Статус генерации: True - успешна, False - неуспешна
    gen_successful: Mapped[bool] = mapped_column(Boolean)
    #  Тип генерации в зависимости от бота
    gen_type: Mapped[str] = mapped_column(String)

    #  Связь с пользователем
    user: Mapped["User"] = relationship("User", back_populates="generation_history")
