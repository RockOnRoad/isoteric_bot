from datetime import datetime
from typing import Literal, TYPE_CHECKING

from sqlalchemy import DateTime, String, Enum, BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.models.base import Base

PaymentStatus = Literal["pending", "canceled", "succeeded", "completed"]

if TYPE_CHECKING:
    from .user import User
    from .referral_bonus import ReferralBonus


class Payment(Base):
    """Payment model."""

    #  ID пользователя
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE")
    )
    #  ID транзакции от платежной системы
    payment_id: Mapped[str] = mapped_column(String, unique=True)
    #  Количество кредитов
    amount: Mapped[int]
    #  Количество рублей
    rub_amount: Mapped[int]
    #  Статус платежа (pending - ожидает оплаты, canceled - отменен, succeeded - успешно оплачен, completed - баланс начислен)
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(
            "pending", "canceled", "succeeded", "completed", name="payment_status_enum"
        ),
        default="pending",
    )
    #  Время завершения платежа
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    #  Связь с пользователем
    user: Mapped["User"] = relationship("User", back_populates="payments")
    #  Реферальные бонусы, начисленные за этот платеж
    referral_bonuses: Mapped[list["ReferralBonus"]] = relationship(
        "ReferralBonus",
        back_populates="payment",
    )
