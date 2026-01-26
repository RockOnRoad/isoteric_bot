import logging
import xml.sax.saxutils as saxutils

from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from sqlalchemy.ext.asyncio import AsyncSession

from db import crud, models as mdl
import schemas as sch
import services as srv
from keyboards import InlineKeyboard


logger = logging.getLogger(__name__)
rtr = Router()


#  ----------- START -----------


async def handle_start_main(
    update: Message | CallbackQuery,
    state: FSMContext,
    db_session: AsyncSession,
    command: CommandObject | None = None,
) -> None:
    user = await crud.get_user_by_telegram_id(update.from_user.id, db_session)
    if user is None:
        user: mdl.User | None = await srv.first_start_routine(
            command=command, message=update, db_session=db_session
        )

    #  Check if user already received sub_2 bonus
    sub_2_bonus = await crud.get_user_bonus_by_name(
        user_id=user.id,
        bonus_name="sub_2",
        session=db_session,
    )

    subbed: bool = await srv.sub_2_check(user_id=user.user_id)

    #  Check if user has sub_2 bonus
    if sub_2_bonus is None or not sub_2_bonus.deposited:
        # if not sub_2_bonus.deposited:
        #  Check if user is subscribed to the channels
        if subbed:
            #  Increase user balance and add sub_2 bonus
            await srv.apply_sub_2_bonus(user_id=user.id, session=db_session)

            if isinstance(update, Message):
                await update.answer(f"+ {sch.BONUSES['sub_2']['amount']}⚡️")
            else:
                await update.message.edit_text(f"+ {sch.BONUSES['sub_2']['amount']}⚡️")
        else:
            buttons = (
                {
                    "text": "Нейроофис",
                    "url": "https://t.me/neiro_office",
                },
                {
                    "text": "Нион",
                    "url": "https://t.me/nion_neiro",
                },
                {
                    "text": "Открыть дверь в Матрику",
                    "callback_data": sch.StartCallback(trigger="enter_matrix"),
                },
            )
            kbd = InlineKeyboard(buttons=buttons, width=2)

            if isinstance(update, Message):
                text = (
                    "✨ Приветствую!\n\n"
                    "Чтобы войти в пространство Матрики и получить стартовый бонус 33 ⚡️, подпишитесь на наши каналы.\n\n"
                    "👇 Это ваш ключ к началу пути:\n"
                )
                await update.answer(text, reply_markup=kbd.markup)
            else:
                text = (
                    "🔒 Доступ закрыт\n\n"
                    "Чтобы открыть знания и образы Матрики, необходимо быть в кругу наших подписчиков. Энергия течет только там, где есть связь.\n\n"
                    "Подпишитесь на каналы, чтобы продолжить путь 👇\n"
                )
                try:
                    await update.message.edit_text(text, reply_markup=kbd.markup)
                except TelegramBadRequest as e:
                    if (
                        e.message
                        == "Bad Request: message is not modified: specified new message content and reply markup are exactly the same as a current content and reply markup of the message"
                    ):
                        update.message.delete()
                        await update.message.edit_text(text, reply_markup=kbd.markup)
                    else:
                        raise e
            return

    # Если пользователь прошёл начальный опрос - показываем главную клавиатуру
    if user.birthday:
        name = saxutils.escape(user.name)
        text = (
            f"{name}, Вы снова в <b>Матрике • Код Твоей Души</b> ✨\n"
            "Я готова продолжить Ваш разбор с того места, где Вы остановились — или сразу открыть нужную сферу 🌿\n\n"
            "<b>Куда пойдём сейчас? 👇</b>"
        )
        #  Если пользователь есть в БД и у него есть день рождения - показываем главную клавиатуру
        if isinstance(update, Message):
            await update.answer(text, reply_markup=sch.main_reply_kbd.markup)
        else:
            await update.message.answer(text, reply_markup=sch.main_reply_kbd.markup)
        await state.clear()
        return

    else:
        text = """
Добро пожаловать в Матрику • Код Твоей Души ✨
<b>Здорово, что ты здесь.</b>

Здесь мы бережно разбираем твою Матрицу Судьбы по <b><u>дате рождения</u></b>: характер, денежный канал, отношения, кармические задачи и родовые истории — всё в мягком, честном и безопасном формате 🌿

Матрица — это не магия и не угадайка. Это геометрия твоей души: набор чисел, через который видны сильные стороны, направления роста и природные энергии. Я опираюсь на математику энергий, психологию и возможности нейросетей, чтобы превратить всё это в ясные подсказки и живые образы ✨

Как всё будет происходить:
1. Сначала я посчитаю твой главный аркан и покажу, какую энергию ты несёшь в мир 💫
2. Затем ты сможешь выбрать разбор глубже: деньги 💸, любовь ❤️, предназначение 🔮 или полный анализ
3. Параллельно мы создадим твой энергетический AI-образ — визуальный портрет твоей энергии 🎭
Первая короткая распаковка — в подарок 🎁

Давай знакомиться.
Как мне к тебе обращаться?
<b>(Напиши, пожалуйста, своё имя 👇)</b>
"""

        if isinstance(update, Message):
            await update.answer(text, reply_markup=ReplyKeyboardRemove())
        else:
            await update.message.answer(text, reply_markup=ReplyKeyboardRemove())

        await state.set_state(sch.BioStates.name)
        return

    # if user is not None and user.birthday:
    #     pass
    # else:
    #     pass
    # if user is None:
    #     pass


rtr.message.register(handle_start_main, CommandStart())
rtr.callback_query.register(handle_start_main, sch.StartCallback.filter())
