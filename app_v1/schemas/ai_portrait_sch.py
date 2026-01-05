from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.state import State, StatesGroup


#  ----------- AI-PORTRAITS STATES -----------


class AiPortraitStates(StatesGroup):
    domain = State()
    aspect = State()
    another_birthday = State()


#  ----------- AI-PORTRAITS CALLBACK DATA -----------


class AiPortrait(CallbackData, prefix="ai_portrait"):
    button: str


class AiPortraitGenerate(CallbackData, prefix="ai_portrait_generate"):
    button: str
