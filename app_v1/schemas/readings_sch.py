from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.state import State, StatesGroup


#  ----------- READINGS STATES -----------


class ReadingsStates(StatesGroup):
    witch = State()
    domain = State()
    aspect = State()


#  ----------- READINGS CALLBACK DATA -----------


class ReadingsDomain(CallbackData, prefix="domain"):
    button: str


class ReadingsSub(CallbackData, prefix="readings_sub"):
    domain: str
    aspect: str
