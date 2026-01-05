import logging

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from db.crud import get_user_by_telegram_id
from schemas import DailyCardStates
from keyboards import InlineKbd

logger = logging.getLogger(__name__)
dc_rtr = Router()


#  ----------- DAILY CARD ----------- (main)


async def handle_daily_card_main(
    update: Message | CallbackQuery, state: FSMContext, db_session: AsyncSession
) -> None:

    user = await get_user_by_telegram_id(update.from_user.id, db_session)
    name = user.name

    await state.set_state(DailyCardStates.main)

    if isinstance(update, CallbackQuery):
        await update.message.edit_text(f"Карта для: {name}")
    elif isinstance(update, Message):
        await update.answer(f"Карта для: {name}")


dc_rtr.message.register(handle_daily_card_main, F.text == "🃏 Карта Дня")
# ai_portraits_rtr.callback_query.register(
#     handle_ai_portraits_main, AiPortraitGenerate.filter(F.button == "back")
# )
