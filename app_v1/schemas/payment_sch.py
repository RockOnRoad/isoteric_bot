from aiogram.filters.callback_data import CallbackData


class YKOperations(CallbackData, prefix="yk"):
    operation: str
    payment_id: str | None = None
