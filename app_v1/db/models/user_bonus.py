from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.models.base import Base


if TYPE_CHECKING:
    from .user import User


class UserBonus(Base):
    """User bonus model."""

    __tablename__ = "user_bonuses"

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE")
    )
    #  Название бонуса
    bonus_name: Mapped[str]
    #  Сумма бонуса в энергии
    amount: Mapped[int]
    #  Был ли бонус начислен на баланс пользователя
    deposited: Mapped[bool] = mapped_column(default=False)

    user: Mapped["User"] = relationship("User", back_populates="user_bonuses")
