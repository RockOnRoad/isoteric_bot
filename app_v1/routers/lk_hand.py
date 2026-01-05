import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from db.crud import get_user_by_telegram_id
from keyboards import InlineKbd
from schemas import LkButton, LkTopUp, ReferalLink

logger = logging.getLogger(__name__)
lk_rtr = Router()


#  ----------- LK MAIN MESSAGE -----------


async def lk_handler(update: Message | CallbackQuery, db_session: AsyncSession) -> None:
    profile = await get_user_by_telegram_id(update.from_user.id, db_session)
    name = profile.name

    msg = (
        "🧑‍💫 Личный кабинет\n"
        f"<b>{name}, здесь всё, что связано с твоими разборами и энергией ✨</b>\n"
        """<b>🔮 Доступные генерации: XXX</b>
(разборы и AI-образы, которые ты можешь создать)

📣 Приглашайте друзей и зарабатывайте бонусы на генерации: +10% с трат каждого приглашённого.

💳 Способы оплаты:
— Карты российских банков
— СБП, СберPay, T-Pay, Мир
"""
    )

    buttons = {
        "💰 Пополнить": LkButton(button="top_up").pack(),
        "👥 Пригласи друга": LkButton(button="invite_friend").pack(),
        "🤹‍♀️ Наши боты": LkButton(button="our_bots").pack(),
        # "❓ Помощь": LkButton(button="help").pack(),
    }
    kbd = InlineKbd(buttons=buttons, width=2)

    if isinstance(update, Message):
        await update.answer(msg, reply_markup=kbd.markup)
    elif isinstance(update, CallbackQuery):
        await update.message.edit_text(msg, reply_markup=kbd.markup)
    else:
        return


lk_rtr.message.register(lk_handler, F.text == "👤 Личный кабинет")
lk_rtr.callback_query.register(lk_handler, LkButton.filter(F.button == "back"))


#  ----------- TOP UP -----------


@lk_rtr.callback_query(LkButton.filter(F.button == "top_up"))
async def top_up(callback: CallbackQuery) -> None:

    msg = (
        "<b>🪙  Пополнение баланса</b>\n\n"
        "<b>💰 Ваши доступные генерации: ХХХ</b>\n\n"
        "Чтобы продолжить, пополните баланс — выберите удобный пакет ниже.\n\n"
        """<b>🎄Сейчас действует Новогодняя акция:</b>
за каждую покупку оживления мы начисляем <b>+10 бананов</b> в боте для генерации и редактирования изображений <b>БананоГен</b> в подарок 💝

Перед оплатой можно посмотреть документы:
Оферта | Обработка персональных данных
"""
    )
    buttons = {
        "✨ Купить 1 генерацию — 250 ₽": LkTopUp(kreds="250").pack(),
        "Купить 3 + 1 фото 🎁 - 699 ₽ ": LkTopUp(kreds="699").pack(),
        "Купить 5 + 2 фото 🎁 - 999 ₽ ": LkTopUp(kreds="999").pack(),
        "Купить 20 + 5 фото 🎁 - 3499 ₽": LkTopUp(kreds="3499").pack(),
        "🔙 Назад": LkButton(button="back").pack(),
    }
    kbd = InlineKbd(buttons=buttons, width=2)
    await callback.message.edit_text(msg, reply_markup=kbd.markup)


#  ----------- INVITE FRIEND -----------


@lk_rtr.callback_query(LkButton.filter(F.button == "invite_friend"))
async def invite_friend(callback: CallbackQuery) -> None:

    msg = (
        "<b>🍒 Реферальная программа</b>\n\n"
        "👥 Приведено пользователей: <b>XXX</b>\n"
        "💰 Заработано: <b>XXX</b> ₽\n"
        "🔗 Ваша ссылка:\n"
        "https://t.me/xxxxx?start=ref_3\n\n"
        "<b>💡 Как это работает:</b>\n"
        "1. Делитесь ссылкой с друзьями.\n"
        "2. За каждое пополнение друга — вы получаете +10% от его суммы себе на счет.\n\n"
        "🚀 Пригласите друзей и окупите свои генерации.\n\n"
        "📋 Последние рефералы:\n"
        "• ...\n"
    )

    buttons = {
        "📤 Поделиться ссылкой ": ReferalLink(button="share_link").pack(),
        "🔙 Назад": LkButton(button="back").pack(),
    }
    kbd = InlineKbd(buttons=buttons, width=1)
    await callback.message.edit_text(msg, reply_markup=kbd.markup)


#  ----------- OUR BOTS -----------


@lk_rtr.callback_query(LkButton.filter(F.button == "our_bots"))
async def our_bots(callback: CallbackQuery) -> None:
    await callback.message.answer("🤹‍♀️ Наши боты")


#  ----------- HELP -----------


@lk_rtr.callback_query(LkButton.filter(F.button == "help"))
async def help(callback: CallbackQuery) -> None:
    msg = (
        "<b>🆘 Нужна помощь?</b>\n"
        "Никакой паники, сейчас всё решим 💪\n\n"
        "<b>👨‍💻 Администратор:</b>\n"
        "@b_chernenko — всегда на связи.\n\n"
        "<b>✍️ Пишите, если:</b>\n"
        "— что-то пошло не так 🛠\n"
        "— не прошла оплата 💸\n"
        "— нужна подсказка или совет 😎\n\n"
        "<b>📎 Полезное:</b>\n"
        "📄 Пользовательское соглашение\n"
        "📄 Согласие на обработку персональных данных\n\n"
        "<b>⌨ Команды бота:</b>\n"
        "/start — начать\n"
        "/balance — баланс\n"
        "/payment — пополнить"
    )

    buttons = {
        "🔙 Назад": LkButton(button="back").pack(),
    }
    kbd = InlineKbd(buttons=buttons, width=2)
    await callback.message.edit_text(msg, reply_markup=kbd.markup)
