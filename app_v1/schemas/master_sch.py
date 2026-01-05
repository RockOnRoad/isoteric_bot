from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Filter
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.fsm.context import FSMContext
from db.crud.users_crud import get_user_balance


from keyboards import ReplyKbd


#  ----------- BALANCE CHECK -----------


class BalanceCheck(Filter):
    """Filter to check if the users have enough balance to afford generation"""

    async def __call__(
        self,
        update: Message | CallbackQuery,
        db_session: AsyncSession,
        state: FSMContext,
    ) -> bool:
        if not update.from_user:
            return False

        user_balance = (
            await get_user_balance(user_id=update.from_user.id, session=db_session) or 0
        )

        data = await state.get_data()
        cost = data.get("cost")

        if cost is None:
            return False

        return user_balance >= cost


#  ----------- BIO STATES -----------


class BioStates(StatesGroup):
    """FSM states for bio collection flow."""

    name = State()
    edit_name = State()
    to_sex = State()
    sex = State()
    birthday = State()
    confirm = State()
    edit_or_confirm = State()


#  ----------- MAIN REPLY KBD -----------

buttons = ("🔮 Разборы", "🎭 AI-Образы", "🃏 Карта Дня", "👤 Личный кабинет")
main_reply_kbd = ReplyKbd(buttons=buttons, width=2)
