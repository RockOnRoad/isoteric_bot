from datetime import datetime
from typing import Literal, TYPE_CHECKING

from sqlalchemy import DateTime, Enum, BigInteger, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.models.base import Base

Segment = Literal["lead", "qual", "client", "banned"]
Sex = Literal["m", "f"]

if TYPE_CHECKING:
    from .payment import Payment
    from .referral_bonus import ReferralBonus
    from .generation_history import GenerationHistory
    from .user_source import UserSource


# class User(Base):
#     """User model."""

#     user_id: Mapped[int] = mapped_column(
#         BigInteger, unique=True, nullable=False
#     )  # tg_id
#     username: Mapped[str | None]
#     first_name: Mapped[str | None]
#     last_name: Mapped[str | None]
#     mail: Mapped[str | None]
#     balance: Mapped[int] = mapped_column(default=0)
#     segment: Mapped[Segment] = mapped_column(
#         Enum("lead", "qual", "client", "banned", name="segment_enum"), default="lead"
#     )
#     referred_id: Mapped[int | None] = mapped_column(nullable=True)
#     name: Mapped[str | None]
#     birthday: Mapped[str | None]
#     sex: Mapped[Sex | None] = mapped_column(Enum("m", "f", name="sex_enum"))
#     latest_conversation: Mapped[str | None]
#     last_updated: Mapped[datetime] = mapped_column(
#         DateTime(timezone=True),
#         server_default=func.now(),
#         onupdate=func.now(),
#         nullable=False,
#     )


class User(Base):
    """User model."""

    #  Telegram ID
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    #  TG Username
    username: Mapped[str | None]
    #  TG First Name
    first_name: Mapped[str | None]
    #  TG Last Name
    last_name: Mapped[str | None]
    mail: Mapped[str | None]
    balance: Mapped[int] = mapped_column(default=0)
    #  Сегмент в котором находится пользователь в зависимости от того пополнял ли он баланс
    #  и насколько активно он использует бота
    segment: Mapped[Segment] = mapped_column(
        Enum("lead", "qual", "client", "banned", name="segment_enum"), default="lead"
    )
    #  ID пользователя, который пригласил этого пользователя
    referred_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    #  Вводимые данные пользователя, когда он заходит в бота впервые
    #  или нажимает "/start"
    name: Mapped[str | None]
    birthday: Mapped[str | None]
    sex: Mapped[Sex | None] = mapped_column(Enum("m", "f", name="sex_enum"))
    #  ID последнего запроса ChatGPT, нужен для сохранения контекста разговора
    latest_conversation: Mapped[str | None]
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Реферер (кто пригласил этого пользователя)
    referrer: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[referred_id],
        remote_side="User.id",
        back_populates="referrals",
    )
    # Рефералы (кого пригласил этот пользователь)
    referrals: Mapped[list["User"]] = relationship(
        "User",
        back_populates="referrer",
    )
    # Платежи пользователя
    payments: Mapped[list["Payment"]] = relationship(
        "Payment",
        back_populates="user",
    )
    # Реферальные бонусы, начисленные этому пользователю
    referral_bonuses: Mapped[list["ReferralBonus"]] = relationship(
        "ReferralBonus",
        foreign_keys="ReferralBonus.ref_id",
        back_populates="referrer_user",
    )
    # История генераций пользователя
    generation_history: Mapped[list["GenerationHistory"]] = relationship(
        "GenerationHistory",
        back_populates="user",
    )
    # Источники пользователя (откуда пришел)
    user_sources: Mapped[list["UserSource"]] = relationship(
        "UserSource",
        back_populates="user",
    )
