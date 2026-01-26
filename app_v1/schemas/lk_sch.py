from aiogram.filters.callback_data import CallbackData


class LkButton(CallbackData, prefix="lk"):
    button: str


class LkTopUp(CallbackData, prefix="lk_top_up"):
    rub: int


#  ----------- TARIFFS -----------


TARIFFS = {
    99: {
        "name": "✨ Искорка",
        "kreds": 100,
    },
    499: {
        "name": "🌊 Поток",
        "kreds": 550,
    },
    999: {
        "name": "💎 Ресурс",
        "kreds": 1300,
    },
    1999: {
        "name": "👑 Изобилие",
        "kreds": 3000,
    },
}


REFERRAL_BONUS_PERCENT = 0.1
