import logging
import json

from aiogram import Router
from aiogram.filters import Command, Filter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from db.crud import (
    get_user_by_telegram_id,
    change_user_balance,
)
from core.config import settings
from services import get_admin_stats

logger = logging.getLogger(__name__)
rtr = Router()


class AdminCheck(Filter):
    """Filter to check if the user is an admin (owner) of the bot."""

    async def __call__(self, update: Message | CallbackQuery) -> bool:
        with open("app_v1/core/roles.json", "r") as f:
            roles = json.load(f)
        return str(update.from_user.id) in roles["admins"]


#  ----------- GIVE BALANCE -----------


#  /give_balance tg_id цифра
@rtr.message(Command("give_balance"), AdminCheck())
async def give_or_take_balance(
    message: Message, db_session: AsyncSession, state: FSMContext
) -> None:
    user_id = int(message.text.split()[1])
    amount = int(message.text.split()[2])

    user = await get_user_by_telegram_id(int(user_id), db_session)

    new_balance = await change_user_balance(user.id, int(amount), db_session)

    text = (
        f"Пользователю <b>{user_id}</b>\n\n"
        if amount > 0
        else f"У пользователя <b>{user_id}</b>\n\n"
    )

    text += (
        f"➕ Начислено: <b>{amount} ⚡️</b>\n"
        if amount > 0
        else f"➖ Снято: <b>{amount} ⚡️</b>\n"
    )
    text += f"💰 Стало: <b>{new_balance} ⚡️</b>"

    await message.answer(text)


#  ----------- ADMIN STATS -----------
@rtr.message(Command("admin"), AdminCheck())
async def admin_stats(message: Message, db_session: AsyncSession) -> None:
    stats = await get_admin_stats(db_session)
    await message.answer(stats)
