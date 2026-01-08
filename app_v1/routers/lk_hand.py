import logging
from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message, CallbackQuery, FSInputFile
from dns import message
from sqlalchemy.ext.asyncio import AsyncSession

from db.crud import (
    get_user_by_telegram_id,
    get_user_referrals,
    get_user_referral_bonuses_total,
)
from keyboards import InlineKbd
from schemas import LkButton, LkTopUp, ReferalLink, TARIFFS

logger = logging.getLogger(__name__)
lk_rtr = Router()

#  ----------- LK MAIN MESSAGE -----------


async def lk_handler(update: Message | CallbackQuery, db_session: AsyncSession) -> None:
    user = await get_user_by_telegram_id(update.from_user.id, db_session)
    name = user.name

    msg = (
        "👤 Личное пространство\n\n"
        f"{name}, здесь центр управления вашей энергией и доступом к знаниям. ✨\n\n"
        f"<b>💎 Ваш баланс: {user.balance} ⚡️</b>\n\n"
        "Любой запрос к Матрике = <b>33⚡️</b>.\n\n"
        "🤝 Кармический менеджмент\n"
        "Приглашайте близких искать свой путь.\n"
        "Вы будете получать <b>+10% энергии</b> на свой счет от суммы любых пополнений каждого друга.\n\n"
        "<b>🔗 Ваша пригласительная ссылка:</b>\n"
        f"<code>https://t.me/MatrikaSoulBot?start=ref_{user.id}</code>\n\n"
        "<b>💳 Пополнение баланса:</b>\n"
        "Работаем со всеми картами РФ, СБП, SberPay, T-Pay.\n\n"
        "<b>👇 Управление:</b>\n"
    )

    buttons = {
        "💰 Пополнить": LkButton(button="top_up").pack(),
        "👥 Пригласи друга": LkButton(button="invite_friend").pack(),
        "🤹‍♀️ Наши боты": LkButton(button="our_bots").pack(),
        # "❓ Помощь": LkButton(button="help").pack(),
    }
    kbd = InlineKbd(buttons=buttons, width=2)

    if isinstance(update, Message):
        await update.answer(msg, reply_markup=kbd.markup, disable_web_page_preview=True)
    elif isinstance(update, CallbackQuery):
        try:
            await update.message.edit_text(
                msg, reply_markup=kbd.markup, disable_web_page_preview=True
            )
        except TelegramBadRequest:
            await update.message.delete()
            await update.message.answer(
                msg, reply_markup=kbd.markup, disable_web_page_preview=True
            )
    else:
        return


lk_rtr.message.register(lk_handler, F.text == "👤 Личный кабинет")
lk_rtr.callback_query.register(lk_handler, LkButton.filter(F.button == "back"))


#  ----------- TOP UP -----------


@lk_rtr.callback_query(LkButton.filter(F.button == "top_up"))
async def top_up(callback: CallbackQuery, db_session: AsyncSession) -> None:

    user = await get_user_by_telegram_id(callback.from_user.id, db_session)

    msg = (
        # "<b>🪙  Пополнение баланса</b>\n\n"
        f"Сейчас у вас: <b>{user.balance}</b> энергии.\n\n"
        "Энергия нужна, чтобы открывать глубинные сферы Матрицы (Деньги, Отношения, Таланты) и создавать визуальные AI-образы.\n\n"
        "Пополните баланс, чтобы продолжить путешествие к себе. Чем больше пакет, тем больше энергии я начислю в подарок.\n"
        "Выбирайте сердцем 👇\n\n"
        "<b>✨ «Искорка»</b>\n"
        "100 энергии\n"
        "<b>👛 99 руб.</b>\n"
        "<i>(Для быстрого старта)</i>\n\n"
        "<b>🌊 «Поток»</b>\n"
        "550 энергии (+51 в подарок)\n"
        "<b>👛 499 руб.</b>\n"
        "<i>(Хватит на пару сфер)</i>\n\n"
        "<b>💎 «Ресурс»</b>\n"
        "1300 энергии (+301 в подарок)\n"
        "<b>👛 999 руб.</b>\n"
        "<i>(Глубокое погружение)</i>\n\n"
        "<b>👑 «Изобилие»</b>\n"
        "3000 энергии (+1001 в подарок!)\n"
        "<b>👛 1999 руб.</b>\n"
        "<i>(Полный доступ + запас на будущее)</i>\n\n"
        "Выберите свою опцию:\n\n"
        "Перед пополнением ознакомьтесь с документами:\n"
        "📄 Оферта | 📄 Обработка персональных данных\n"
    )

    # Формируем кнопки с тарифами
    buttons = {}
    for rub, tariff_data in TARIFFS.items():
        button_text = f"{tariff_data['name']} {tariff_data['kreds']}⚡️"
        buttons[button_text] = LkTopUp(rub=rub).pack()

    buttons["🔙 Назад"] = LkButton(button="back").pack()
    kbd = InlineKbd(buttons=buttons, width=2)
    await callback.message.edit_text(msg, reply_markup=kbd.markup)


#  ----------- INVITE FRIEND -----------


@lk_rtr.callback_query(LkButton.filter(F.button == "invite_friend"))
async def invite_friend(callback: CallbackQuery, db_session: AsyncSession) -> None:
    user = await get_user_by_telegram_id(callback.from_user.id, db_session)
    referrals = await get_user_referrals(user_id=user.id, session=db_session)

    referrals_count = len(referrals)
    total_earned = await get_user_referral_bonuses_total(
        user_id=user.id, session=db_session
    )

    msg = (
        "<b>🤝 Энергия связей</b>\n\n"
        f"{user.name}, это ваш круг влияния. Когда вы делитесь инструментом развития с другими, Вселенная возвращает вам ресурс 🔮\n\n"
        f"<b>👥 В вашем круге:</b> {referrals_count} чел.\n"
        f"<b>💎 Начислено бонусов:</b> {total_earned}⚡️\n"
        f"🔗 Ваша пригласительная ссылка:\n"
        f"<code>https://t.me/MatrikaSoulBot?start=ref_{user.id}</code>\n"
        "*(Нажмите на ссылку, чтобы скопировать)*\n\n"
        "<b>💡 Закон энергообмена:</b>\n"
        "1. Отправьте ссылку друзьям или опубликуйте в соцсетях.\n"
        "2. Как только друг пополнит баланс, вы моментально получите <b>+10% энергии</b> от суммы его пополнения.\n\n"
        "<b>🚀 Делитесь пользой — и открывайте свои сферы и AI-образы бесплатно.</b>\n\n"
        "<b>📋 Последние присоединившиеся:</b>\n"
        # f"• {list_of_last_referrals}\n"
    )

    buttons = {
        "🔙 Назад": LkButton(button="back").pack(),
    }
    kbd = InlineKbd(buttons=buttons, width=1)
    await callback.message.edit_text(msg, reply_markup=kbd.markup)


#  ----------- OUR BOTS -----------


@lk_rtr.callback_query(LkButton.filter(F.button == "our_bots"))
async def our_bots(callback: CallbackQuery) -> None:

    text = (
        "В нашей семейке ботов Нейроофис всё просто и под рукой ✨\n\n"
        "<b>Для контента и творчества:</b>\n"
        "🍌 @Bananogenbot — генерация изображений\n"
        "📸 @clickclickgenbot — нейрофотосессия за секунды\n"
        "✨ @MagiaPicbot — оживление фото и видео\n"
        "🎨 @photolivegenbot — движение в любимых кадрах\n"
        "🎵 @pesnyaAibot — песня за 15 секунд\n"
        "🎙 @iVoxOfficialBot — озвучка красивыми голосами\n"
        "<b>Для бизнеса:</b>\n\n"
        "🛍 @mpstudiopicbot — карточки для WB / Ozon\n"
        "<b>Для себя:</b>\n\n"
        "🔮 @MatrikaSoulBot — Матрица Судьбы: деньги, отношения, предназначение\n\n"
        "🔒 Заглядывайте в @bananogenprompts — там готовые идеи и примеры.\n"
        "🔥 Выберите бота и попробуйте прямо сейчас."
    )

    picture = FSInputFile("app_v1/src/assets/2026-01-06 14.25.58.jpg")

    buttons = {
        "🔙 Назад": LkButton(button="back").pack(),
    }
    kbd = InlineKbd(buttons=buttons, width=1)

    await callback.message.delete()
    await callback.message.answer_photo(
        photo=picture, caption=text, reply_markup=kbd.markup
    )


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
