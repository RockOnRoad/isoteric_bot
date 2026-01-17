import logging

from aiogram import Router
from aiogram.filters import CommandStart, Filter, CommandObject
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import RELATED_CHANNELS, bot
from db.crud import get_user_by_telegram_id, get_user_bonus_by_name
from db.models import User
from services.first_start import first_start_routine
from schemas import BONUSES

logger = logging.getLogger(__name__)
rtr = Router()


channels = [[000, 111, 238163604, 222], [238163604, 333, 444, 555]]


class NotASub(Filter):
    """Filter to check if the user is not subscribed to the channel"""

    async def __call__(
        self, update: Message | CallbackQuery, db_session: AsyncSession
    ) -> bool:
        user = await get_user_by_telegram_id(update.from_user.id, db_session)
        if user is None:
            return True

        sub_2_bonus = await get_user_bonus_by_name(
            user_id=user.id,
            bonus_name="sub_2",
            session=db_session,
        )

        if sub_2_bonus:
            return False
        else:
            is_not_subbed = False
            # for channel in channels:
            #     if update.from_user.id not in channel:
            #         is_not_subbed = True
            #         break
            for channel in RELATED_CHANNELS:
                try:
                    member = await bot.get_chat_member(
                        chat_id=channel, user_id=update.from_user.id
                    )
                    if member.status != "member":
                        is_not_subbed = True
                        break
                except TelegramBadRequest:
                    return False
            return is_not_subbed


@rtr.message(CommandStart(), NotASub())
async def not_a_sub(
    message: Message, command: CommandObject, db_session: AsyncSession
) -> None:

    user = await get_user_by_telegram_id(message.from_user.id, db_session)
    if user is None:
        text = (
            "✨ Приветствую!\n\n"
            "Чтобы войти в пространство Матрики и получить стартовый бонус 33 ⚡️, подпишитесь на наши каналы.\n\n"
            "👇 Это ваш ключ к началу пути:\n"
        )
        user: User | None = await first_start_routine(
            command=command, message=message, db_session=db_session
        )

    else:
        text = (
            "🔒 Доступ закрыт\n\n"
            "Чтобы открыть знания и образы Матрики, необходимо быть в кругу наших подписчиков. Энергия течет только там, где есть связь.\n\n"
            "Подпишитесь на каналы, чтобы продолжить путь 👇\n"
        )
    text += "@neiro_office\n@nion_neiro"

    await message.answer(text, reply_markup=ReplyKeyboardRemove())


#     member = await bot.get_chat_member(
#         chat_id="@neiro_office", user_id=message.from_user.id  # or channel_id
#     )
#     await message.answer(f"Member status: {member.status}")
