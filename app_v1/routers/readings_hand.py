import logging
import yaml
from pathlib import Path

from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import COST
from services import OpenAIClient
from schemas import ReadingsDomain, ReadingsSub, ReadingsStates, BalanceCheck, LkButton
from keyboards import InlineKbd
from db.crud import (
    get_user_by_telegram_id,
    update_user_info,
    get_user_balance,
    decrease_user_balance,
)


logger = logging.getLogger(__name__)
readings_rtr = Router()


#  ----------- READINGS ----------- (main)


async def handle_readings_main(
    update: Message | CallbackQuery, state: FSMContext, db_session: AsyncSession
) -> None:

    if isinstance(update, CallbackQuery):
        # Проверка на то, что пользователь не переключился на другой раздел
        current_state = await state.get_state()
        if current_state != ReadingsStates.aspect and current_state is not None:
            await update.answer("Этот диалог завершён")
            return
        await update.answer()

    elif isinstance(update, Message):

        await state.clear()

        user = await get_user_by_telegram_id(update.from_user.id, db_session)
        try:
            await state.update_data(
                name=user.name, birthday=user.birthday, sex=user.sex
            )
        except AttributeError as e:
            await update.answer(
                (
                    f"Мы ещё не знакомы, чтобы делать разборы cначала нужно познакомиться.\n"
                    "Для этого введи команду /start"
                )
            )
            return
    await state.set_state(ReadingsStates.domain)

    name = await state.get_value("name")

    msg = (
        "<b>🔮 Разборы Матрицы Судьбы</b>\n\n"
        f"""{name}, мы уже увидели твой центральный код. Теперь можно точечно разобрать отдельные сферы: деньги, отношения, предназначение, кармические задачи, ресурсное состояние или сделать полный разбор сразу.

Каждый разбор — это отдельный фокус: я беру нужные вершины твоей Матрицы, смотрю связи между арканами и перевожу их на понятный язык — без страшилок, с опорой на психологию и твои реальные ситуации.

<b>Выбери ниже, с какой сферы начнём 👇</b>
"""
    )

    readings_main_buttons = {
        "💸 Деньги": ReadingsDomain(button="wealth").pack(),
        "🧿 Центральный Аркан": ReadingsDomain(button="central_arcana").pack(),
        "❤️ Отношения": ReadingsDomain(button="relations").pack(),
        "🔮 Предназначение": ReadingsDomain(button="purpose").pack(),
        "🧬 Карма": ReadingsDomain(button="karma").pack(),
        "🌿 Ресурс": ReadingsDomain(button="resource").pack(),
        "📆 Личный год": ReadingsDomain(button="personal_year").pack(),
        "🌟 Личность": ReadingsDomain(button="personality").pack(),
        "📘 Полный разбор": ReadingsDomain(button="full_reading").pack(),
        "❤️‍🩹 Другие разборы": ReadingsDomain(button="other_readings").pack(),
    }
    kbd = InlineKbd(buttons=readings_main_buttons, width=2)

    if isinstance(update, Message):
        await update.answer(msg, reply_markup=kbd.markup)
    elif isinstance(update, CallbackQuery):
        await update.message.edit_text(msg, reply_markup=kbd.markup)


readings_rtr.message.register(handle_readings_main, F.text == "🔮 Разборы")
readings_rtr.callback_query.register(
    handle_readings_main, ReadingsDomain.filter(F.button == "back")
)


#  ----------- REDINGS ASPECTS -----------


@readings_rtr.callback_query(
    ReadingsDomain.filter(),
    StateFilter(ReadingsStates.domain, ReadingsStates.witch),
)
async def handle_buttons(
    call: CallbackQuery, callback_data: ReadingsDomain, state: FSMContext
) -> None:

    await call.answer()
    context = await state.get_data()
    if context:

        domain = callback_data.button

        # Загружаем данные из YAML файла
        yaml_path = Path(__file__).parent.parent / "schemas" / "readings_map.yml"
        with open(yaml_path, "r", encoding="utf-8") as f:
            readings_data = yaml.safe_load(f)

        domain_data = readings_data[domain]
        desc_header = domain_data["description_header"]
        desc = domain_data["description"]
        desc_footer = domain_data["description_footer"]

        # Преобразуем кнопки из YAML формата в CallbackData
        buttons = {}
        for aspect_value, button_data in domain_data["buttons"].items():
            # Обрабатываем как строку (простой формат) или как объект (с полем label)
            button_text = button_data["label"]

            if aspect_value == "back":
                buttons[button_text] = ReadingsDomain(button="back").pack()
            else:
                buttons[button_text] = ReadingsSub(
                    domain=domain, aspect=aspect_value
                ).pack()

        msg = f"<b>{desc_header}</b>\n{desc}\n<b>{desc_footer}</b>"

        kbd = InlineKbd(buttons=buttons, width=1)

        current_state = await state.get_state()
        if current_state == ReadingsStates.witch:
            await call.message.answer(msg, reply_markup=kbd.markup)
        else:
            await call.message.edit_text(msg, reply_markup=kbd.markup)

        await state.update_data(cost=COST["reading"])
        await state.set_state(ReadingsStates.aspect)
    else:
        return


#  ----------- REDINGS RESPONSE -----------


@readings_rtr.callback_query(
    ReadingsSub.filter(), ReadingsStates.aspect, BalanceCheck()
)
async def handle_response(
    call: CallbackQuery,
    callback_data: ReadingsSub,
    state: FSMContext,
    db_session: AsyncSession,
) -> None:
    logger.info(
        f"{call.from_user.id} @{call.from_user.username} - 'readings_generation'"
    )

    await call.answer()
    data = await state.get_data()

    yaml_path = Path(__file__).parent.parent / "schemas" / "readings_map.yml"
    with open(yaml_path, "r", encoding="utf-8") as f:
        readings_data = yaml.safe_load(f)

    if data:
        #  Collecting context for prompt
        context = {}
        context["name"] = data.get("name")
        context["sex"] = data.get("sex")
        context["birthday"] = data.get("birthday")
        context["domain"] = callback_data.domain
        context["aspect"] = callback_data.aspect

        #  Getting response from OpenAI
        client = OpenAIClient(auto_create_conv=True)
        answer, conversation_id = await client.chatgpt_response(
            feature="readings", context=context
        )

        #  saving conversation to database
        await update_user_info(
            call.from_user.id, {"latest_conversation": conversation_id}, db_session
        )
        await state.update_data(conversation_id=conversation_id)

        user = await get_user_by_telegram_id(call.from_user.id, db_session)

        new_balance = await decrease_user_balance(
            user.id,
            COST["reading"],
            db_session,
        )

        await state.update_data(cost=COST["follow_up"])

        #  Отправка ответа
        try:
            await call.message.edit_text(answer)
        except TelegramBadRequest:
            await call.message.answer(answer)

    else:
        return


#  ----------- NO READINGS FOR POOR -----------


@readings_rtr.callback_query(ReadingsSub.filter(), ReadingsStates.aspect)
async def handle_no_readings_for_poor(
    call: CallbackQuery,
    state: FSMContext,
    db_session: AsyncSession,
) -> None:

    user_balance = await get_user_balance(call.from_user.id, db_session)
    cost = await state.get_value("cost")

    logger.info(
        f"{call.from_user.id} @{call.from_user.username} - 'no_readings_for_poor (ub:{user_balance} cost:{cost})'"
    )

    await call.answer()

    buttons = {
        "🪙 Пополнить баланс": LkButton(button="top_up").pack(),
    }
    kbd = InlineKbd(buttons=buttons, width=1)

    await call.message.answer(
        (
            "У вас недостаточно средств для просмотра этого раздела\n"
            "Пополните баланс и попробуйте снова\n\n"
            f"Ваш баланс: {user_balance}\n"
            f"Стоимость генерации: {cost}"
        ),
        reply_markup=kbd.markup,
    )
