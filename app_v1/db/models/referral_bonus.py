from typing import Literal, TYPE_CHECKING

from sqlalchemy import Enum, BigInteger, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.models.base import Base

BonusType = Literal["deposit", "generation"]

if TYPE_CHECKING:
    from .user import User
    from .payment import Payment


class ReferralBonus(Base):
    """Referral bonus model."""

    __tablename__ = "referral_bonuses"

    #  Внутренний ID пользователя, который пригласил
    ref_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE")
    )
    #  Telegram ID пользователя, который пригласил
    referred_user_id: Mapped[int] = mapped_column(BigInteger)
    #  Telegram ID пользователя, которого пригласили
    referrer_user_id: Mapped[int] = mapped_column(BigInteger)
    #  Тип бонуса: за депозит или за генерацию
    bonus_type: Mapped[BonusType] = mapped_column(
        Enum("deposit", "generation", name="bonus_type_enum")
    )
    #  Сумма реферального бонуса в кредитах
    amount: Mapped[int]
    #  Сумма депозита в рублях
    deposit_rub_amount: Mapped[int]
    #  Сумма депозита в кредитах
    deposit_token_amount: Mapped[int]
    #  ID платежа, за который начислен бонус
    pay_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("payments.id", ondelete="SET NULL")
    )

    #  Связь с пользователем, который пригласил (по внутреннему ID)
    referrer_user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[ref_id],
        back_populates="referral_bonuses",
    )
    #  Связь с платежом
    payment: Mapped["Payment | None"] = relationship(
        "Payment", back_populates="referral_bonuses"
    )
