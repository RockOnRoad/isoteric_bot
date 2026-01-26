from aiogram.exceptions import TelegramBadRequest
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import RELATED_CHANNELS, bot
from db.crud import upsert_user_bonus, increase_user_balance
from schemas import BONUSES


async def sub_2_check(user_id: int) -> bool:
    sub_statuses = (
        "member",
        "administrator",
        "creator",
        "restricted",
        "kicked",
    )
    subbed: bool = True
    for channel in RELATED_CHANNELS:
        try:
            member = await bot.get_chat_member(
                chat_id=channel, user_id=user_id  # or channel_id
            )
        except TelegramBadRequest as e:
            if e.message == "Bad Request: member list is inaccessible":
                continue
        if member.status not in sub_statuses:
            subbed = False
            break
    return subbed


async def apply_sub_2_bonus(user_id: int, session: AsyncSession):
    await upsert_user_bonus(
        user_id=user_id,
        bonus_name="sub_2",
        amount=BONUSES["sub_2"]["amount"],
        deposited=True,
        session=session,
    )
    await increase_user_balance(
        user_id=user_id,
        amount=BONUSES["sub_2"]["amount"],
        session=session,
    )
    return True
