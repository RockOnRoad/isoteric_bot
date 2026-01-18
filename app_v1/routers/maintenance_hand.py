import os
import logging
from re import M

import asyncio
from aiogram import Router, F
from aiogram.filters import Command, Filter
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings, bot
from db.database import engine
from db.crud import (
    get_user_by_telegram_id,
    decrease_user_balance,
    increase_user_balance,
)
from keyboards import InlineKbd
from prompts import PROMPT_TEMPLATES
from services import calculate_arcana, GoogleAI, OpenAIClient, tst_webhook
from schemas import CalculateArcana, DeleteFunc

logger = logging.getLogger(__name__)
mnt_rtr = Router()


class ArcanaStates(StatesGroup):
    arcana = State()


class OwnerCheck(Filter):
    """Filter to check if the user is the owner of the bot."""

    async def __call__(self, update: Message | CallbackQuery) -> bool:
        return str(update.from_user.id) in settings.owners


#  ----------- ADMIN HELP -----------


@mnt_rtr.message(Command("a-help"), OwnerCheck())
async def a_help(update: Message | CallbackQuery, state: FSMContext) -> None:

    text = (
        "<b>Админские подсказки:</b>\n"
        "/arcana - вычисление аркана даты рождения\n"
        "/models_openai - доступные модели OpenAI\n"
        "/templates - тест шаблонизатора\n"
        "/image - генерация изображения с помощью OpenAI\n"
        "/models_google - доступные модели Gemini\n"
        "/delete - тест удаления сообщений\n"
        "/withdraw &lt;user_id&gt; &lt;amount&gt; - снятие баланса\n"
        "/deposit &lt;user_id&gt; &lt;amount&gt; - пополнение баланса\n"
        "/zip &lt;text&gt; - разделение текста на пары\n"
    )

    await update.answer(text)


#  ----------- CALCULATE ARCANA -----------


# @mnt_rtr.message(Command("arcana"))
async def arcana(update: Message | CallbackQuery, state: FSMContext) -> None:
    logger.info(f"{update.from_user.id} @{update.from_user.username} - 'arcana'")

    await state.set_state(ArcanaStates.arcana)

    msg = "Введите дату рождения в формате <b>ДД.ММ.ГГГГ</b>"

    if isinstance(update, Message):
        await update.answer(msg)
    elif isinstance(update, CallbackQuery):
        await update.message.edit_text(msg)
    else:
        return


mnt_rtr.message.register(arcana, Command("arcana"))
mnt_rtr.callback_query.register(arcana, CalculateArcana.filter(F.button == "calculate"))


@mnt_rtr.message(ArcanaStates.arcana)
async def handle_arcana_message(message: Message, state: FSMContext) -> None:
    await state.clear()
    birthday: str = message.text
    arcana: dict = calculate_arcana(birthday)

    msg = f"""
Аркан дня: {arcana["day_arcana"]}
Аркан месяца: {arcana["month_arcana"]}
Аркан года: {arcana["year_arcana"]}

<b>Аркан даты рождения:</b> {arcana.get("main_arcana", "")}
Центральный аркан: {arcana.get("the_arcana", "")}
    """

    buttons = {"Повторить": CalculateArcana(button="calculate").pack()}

    kbd = InlineKbd(buttons=buttons, width=2)

    await message.answer(msg, reply_markup=kbd.markup)


#  ----------- CURRENT MODELS -----------


@mnt_rtr.message(Command("models_openai"), OwnerCheck())
async def models(update: Message | CallbackQuery, state: FSMContext) -> None:

    client = OpenAIClient()
    models = await client.get_models()
    msg = "Модели OpenAI:\n"
    for model in models:
        msg += f"{model}\n"
    await update.answer(msg)


#  ----------- MODELS TEMPLATES -----------


@mnt_rtr.message(Command("templates"), OwnerCheck())
async def templates(update: Message | CallbackQuery, state: FSMContext) -> None:
    free_mode_explanation = PROMPT_TEMPLATES["free_mode_explanation"]
    raw = "блабла"
    readings_mode_explanation = PROMPT_TEMPLATES["readings_mode_explanation"]
    tmp1: str = free_mode_explanation.render(raw=raw)
    text: str = readings_mode_explanation.render(tmp1=tmp1)
    print(text)


#  ----------- CHATGPT IMAGE -----------


@mnt_rtr.message(Command("image"), OwnerCheck())
async def image(update: Message | CallbackQuery, state: FSMContext) -> None:
    client = OpenAIClient()
    image_bytes = await client.chatgpt_image(
        prompt="Make image in the same style but for arcana 13 (Death)",
    )
    await update.answer_photo(photo=image_bytes)


#  ----------- GOOGLE IMAGE -----------


@mnt_rtr.message(Command("models_google"), OwnerCheck())
async def google_image(update: Message | CallbackQuery, state: FSMContext) -> None:
    client = GoogleAI()
    models = client.google_models()
    msg = "Модели Gemini:\n"
    for model in models:
        msg += f"{model.name}\n"
    await update.answer(msg)


#  ----------- TEST MESSAGE DELETION -----------


@mnt_rtr.message(Command("delete"), OwnerCheck())
async def delete(message: Message | CallbackQuery, state: FSMContext) -> None:

    buttons = {"Button 1": DeleteFunc(button="button1").pack()}
    kbd = InlineKbd(buttons=buttons, width=2)

    await message.answer("Message 1", reply_markup=kbd.markup)


@mnt_rtr.callback_query(DeleteFunc.filter(F.button == "button1"))
async def button1(callback: CallbackQuery, state: FSMContext) -> None:

    msg1 = await callback.message.edit_text("Message 1")
    await asyncio.sleep(1)
    await msg1.delete()
    photo = BufferedInputFile(
        open(
            "app_v1/src/assets/owl_pic_620_6b3d4bb80adc24b34ad43895d6d7ae8e.jpg", "rb"
        ).read(),
        filename="test.jpg",
    )
    msg2 = await callback.message.answer_photo(photo=photo)
    await asyncio.sleep(1)
    await msg2.delete()
    await asyncio.sleep(1)
    msg3 = await callback.message.answer("Message 3")
    await asyncio.sleep(1)
    await msg3.delete()


#  ----------- DECREASE BALANCE -----------


@mnt_rtr.message(Command("withdraw"), OwnerCheck())
async def decrease_balance(
    message: Message, db_session: AsyncSession, state: FSMContext
) -> None:

    user_id = message.text.split()[1]
    amount = message.text.split()[2]

    user = await get_user_by_telegram_id(int(user_id), db_session)

    new_balance = await decrease_user_balance(user.id, int(amount), db_session)
    await message.answer(f"Баланс: {new_balance}")


#  ----------- DEPOSIT BALANCE -----------


@mnt_rtr.message(Command("deposit"), OwnerCheck())
async def deposit_balance(
    message: Message, db_session: AsyncSession, state: FSMContext
) -> None:
    user_id = message.text.split()[1]
    amount = message.text.split()[2]

    user = await get_user_by_telegram_id(int(user_id), db_session)

    new_balance = await increase_user_balance(user.id, int(amount), db_session)
    await message.answer(f"Баланс: {new_balance}")


#  ----------- SPLIT IN PAIRS -----------


@mnt_rtr.message(Command("zip"), OwnerCheck())
async def zips(message: Message, state: FSMContext) -> None:
    text = message.text.split()[1]
    one_by_one = text.split("_")
    await message.answer(f"Length: {len(one_by_one)}")
    for key, value in zip(one_by_one[::2], one_by_one[1::2]):
        await message.answer(f"{key}: {value}")


#  ----------- TEST WEBHOOK -----------


@mnt_rtr.message(Command("webhook"), OwnerCheck())
async def webhook(message: Message, state: FSMContext) -> None:
    await tst_webhook(message)


#  ----------- GET A LIST OF CHANNEL SUBS -----------


@mnt_rtr.message(Command("cn_subs"), OwnerCheck())
async def cn_subs(
    message: Message, db_session: AsyncSession, state: FSMContext
) -> None:

    user_id = message.text.split()[1]
    user = await get_user_by_telegram_id(int(user_id), db_session)

    member = await bot.get_chat_member(
        chat_id="@neiro_office", user_id=user.id  # or channel_id
    )
    print(f"Member: {member}")
    print(f"Member is member: {member.is_member}")

    member2 = await bot.get_chat_member(
        chat_id="@nion_neiro", user_id=user.id  # or channel_id
    )
    print(f"Member2: {member2}")
    print(f"Member2 is member: {member2.is_member}")
    await message.answer(f"Member status: {member.status}\n{member2.status}")


#  ----------- TABLE NAMES -----------


@mnt_rtr.message(Command("table_names"), OwnerCheck())
async def table_names(message: Message, state: FSMContext) -> None:
    async with engine.begin() as conn:
        tables = await conn.run_sync(
            lambda sync_conn: inspect(sync_conn).get_table_names()
        )

    await message.answer(f"Tables: {tables}")


#  ----------- GET ALL ENTRIES -----------
