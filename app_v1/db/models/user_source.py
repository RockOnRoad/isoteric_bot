from typing import TYPE_CHECKING

from db.models.base import Base
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from .user import User


#  От куда пользователь пришел в бота
class UserSource(Base):
    """User source model."""

    __tablename__ = "user_sources"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    #  Ключ из ссылки приглашения
    source_key: Mapped[str]
    #  Значение из ссылки приглашения
    source_value: Mapped[str | None]

    user: Mapped["User"] = relationship(back_populates="user_sources")
