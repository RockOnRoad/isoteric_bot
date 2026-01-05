from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.state import State, StatesGroup


#  ----------- READINGS STATES -----------


class DailyCardStates(StatesGroup):
    main = State()
