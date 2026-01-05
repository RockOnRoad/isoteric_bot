from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.state import State, StatesGroup


#  ----------- E-MAIL STATES -----------


class EmailStates(StatesGroup):
    email = State()
