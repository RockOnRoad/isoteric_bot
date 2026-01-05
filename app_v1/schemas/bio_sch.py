from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.state import State, StatesGroup


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


#  ----------- BIO CALLBACK DATA -----------


class BioEdit(CallbackData, prefix="bio_next"):
    button: str


class BioCorrect(CallbackData, prefix="bio_correct"):
    button: str


class BioSex(CallbackData, prefix="bio_sex"):
    sex: str
