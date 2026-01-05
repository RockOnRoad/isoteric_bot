from aiogram.filters.callback_data import CallbackData


class CalculateArcana(CallbackData, prefix="calculate_arcana"):
    button: str


class DeleteFunc(CallbackData, prefix="del_func"):
    button: str
