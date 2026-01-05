from aiogram.filters.callback_data import CallbackData


class LkButton(CallbackData, prefix="lk"):
    button: str


class LkTopUp(CallbackData, prefix="lk_top_up"):
    kreds: str


class ReferalLink(CallbackData, prefix="invite_friend"):
    button: str
