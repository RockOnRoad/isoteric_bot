import asyncio
import logging
import yaml
from pathlib import Path

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, BufferedInputFile, FSInputFile
from sqlalchemy.ext.asyncio import AsyncSession
from google.genai.errors import ClientError

from core.config import COST
from db.crud import get_user_by_telegram_id, get_user_balance, decrease_user_balance
from keyboards import InlineKbd
from schemas import (
    AiPortrait,
    AiPortraitGenerate,
    AiPortraitStates,
    BalanceCheck,
    LkButton,
)
from services import GoogleAI, MessageAnimation, handle_google_ai_error

logger = logging.getLogger(__name__)
ai_portraits_rtr = Router()


#  ----------- AI-PORTRAITS ----------- (main)


async def handle_ai_portraits_main(
    update: Message | CallbackQuery, state: FSMContext, db_session: AsyncSession
) -> None:

    if isinstance(update, CallbackQuery):
        # Проверка на то, что пользователь не переключился на другой раздел
        current_state = await state.get_state()
        if (
            current_state != AiPortraitStates.aspect
            and current_state != AiPortraitStates.another_birthday
            and current_state is not None
        ):
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
                    f"Мы ещё не знакомы, чтобы собрать образ cначала нужно познакомиться.\n"
                    "Для этого введи команду /start"
                )
            )
            return
    await state.set_state(AiPortraitStates.domain)

    name = await state.get_value("name")

    msg = (
        "<b>🎭 AI-образы по Матрице Судьбы</b>\n\n"
        f"""<b>{name}</b>, иногда один точный образ работает сильнее, чем длинный текст.
В этом разделе я создаю 🪄 для тебя <b>личные энергетические талисманы — AI-картины 🃏</b> по твоим арканам: про деньги, любовь, женский магнетизм и даже теневую сторону, чтобы вернуть ресурс, включить внутреннюю силу и зафиксировать нужное состояние. Через них работать с намерением и состоянием.\n\n
"""
        "<b>Выбери, какой образ создадим прямо сейчас 👇</b>"
    )

    ai_portraits_buttons = {
        "🌿 Ресурс и сила": AiPortrait(button="resource_and_power").pack(),
        "🎎 Женский магнетизм": AiPortrait(button="female_magnetism").pack(),
        "💸 Энергия денег": AiPortrait(button="energy_of_money").pack(),
        "🌙 Твоя тень": AiPortrait(button="your_shadow").pack(),
        "💞 Образ любви": AiPortrait(button="love_portrait").pack(),
        "👥 Совместимость": AiPortrait(button="compatibility").pack(),
        "🎁 Подарок подруге": AiPortrait(button="gift_to_friend").pack(),
    }

    kbd = InlineKbd(buttons=ai_portraits_buttons, width=2)

    if isinstance(update, CallbackQuery):
        await update.message.answer(msg, reply_markup=kbd.markup)
    else:
        await update.answer(msg, reply_markup=kbd.markup)


ai_portraits_rtr.message.register(handle_ai_portraits_main, F.text == "🎭 AI-Образы")
ai_portraits_rtr.callback_query.register(
    handle_ai_portraits_main, AiPortraitGenerate.filter(F.button == "back")
)


#  ----------- AI-PORTRAITS BUTONS -----------


@ai_portraits_rtr.callback_query(AiPortrait.filter(), AiPortraitStates.domain)
async def handle_buttons(
    call: CallbackQuery,
    callback_data: AiPortrait,
    state: FSMContext,
    db_session: AsyncSession,
) -> None:

    #  Получаем пользователя из базы данных
    user = await get_user_by_telegram_id(call.from_user.id, db_session)
    sex = user.sex
    name = user.name
    birthday = user.birthday

    #  Обновляем данные в FSM
    portrait = callback_data.button
    await state.update_data(
        domain=callback_data.button,
        sex=sex,
        name=name,
        birthday=birthday,
    )

    # Загружаем данные из YAML файла
    yaml_path = Path(__file__).parent.parent / "schemas" / "ai_portraits_map.yml"
    with open(yaml_path, "r", encoding="utf-8") as f:
        ai_portraits_data = yaml.safe_load(f)

    portrait_data = ai_portraits_data[portrait]
    try:
        desc = portrait_data["description"]
    except KeyError:
        desc = (
            portrait_data["description_male"]
            if sex == "m"
            else portrait_data["description_female"]
        )

    price = f"💎 Энергообмен: {COST['ai_portrait']} ⚡️ | За открытие любой темы 🔓"

    desc_footer = portrait_data["description_footer"]

    if portrait in (
        "resource_and_power",
        "female_magnetism",
        "energy_of_money",
        "your_shadow",
        "love_portrait",
    ):

        await state.set_state(AiPortraitStates.aspect)

        msg = f"{desc}\n{price}\n<b>{desc_footer}</b>"
        buttons = {
            "🪄 Создать AI-образ✨": AiPortraitGenerate(button="generate").pack(),
            "🔙 Назад": AiPortraitGenerate(button="back").pack(),
        }
        kbd = InlineKbd(buttons=buttons, width=2)

    elif portrait in ("compatibility", "gift_to_friend"):

        await state.set_state(AiPortraitStates.another_birthday)

        msg = f"{desc}\n{price}\n{desc_footer}"
        buttons = {
            "🔙 Назад": AiPortraitGenerate(button="back").pack(),
        }
        kbd = InlineKbd(buttons=buttons, width=2)

    await state.update_data(cost=COST["ai_portrait"])
    await call.message.edit_text(msg, reply_markup=kbd.markup)


#  ----------- AI-PORTRAITS ANOTHER BIRTHDAY -----------


@ai_portraits_rtr.message(AiPortraitStates.another_birthday)
async def handle_another_birthday_message(message: Message, state: FSMContext) -> None:

    #  Добавляем дату рождения второго человека в контекст
    await state.update_data(another_birthday=message.text)
    await state.set_state(AiPortraitStates.aspect)

    msg = "Хорошо, я зафиксировала дату рождения второго человека 🌟\n\n"
    "Теперь перейдём к созданию AI-образа 🎨"

    buttons = {
        "🔙 Назад": AiPortraitGenerate(button="back").pack(),
        "🪄 Создать AI-образ✨": AiPortraitGenerate(button="generate").pack(),
    }
    kbd = InlineKbd(buttons=buttons, width=2)

    await message.answer(msg, reply_markup=kbd.markup)


#  ----------- AI-PORTRAITS ANOTHER BIRTHDAY AND NAME -----------


#  ----------- AI-PORTRAITS GENERATE -----------


@ai_portraits_rtr.callback_query(
    AiPortraitGenerate.filter(F.button == "generate"),
    AiPortraitStates.aspect,
    BalanceCheck(),
)
async def handle_generate_portrait(
    call: CallbackQuery, state: FSMContext, db_session: AsyncSession
) -> None:
    logger.info(
        f"{call.from_user.id} @{call.from_user.username} - 'handle_generate_ai_portrait'"
    )

    await call.answer()

    context = await state.get_data()

    if context:

        # Анимация сообщения во время генерации ответа
        animation_while_generating_picture = MessageAnimation(
            message_or_call=call,
            base_text="✨ Настраиваюсь на поток",
        )
        await animation_while_generating_picture.start()

        try:
            #  Получаем изображение
            client = GoogleAI()
            picture: BufferedInputFile | None = await client.generate_picture(
                feature="ai_portraits",
                context=context,
                #  Сразу после начала генерации сбрасываем состояние чтобы не стартанула следующая генерация
                state=state,
            )
        except ClientError as e:
            await handle_google_ai_error(
                error=e, upd=call, animation=animation_while_generating_picture
            )
            return
        await animation_while_generating_picture.stop()

        await call.message.delete()
        await asyncio.sleep(0.2)

        # Подгружаем фразочки
        yaml_path = Path(__file__).parent.parent / "schemas" / "ai_portraits_map.yml"
        with open(yaml_path, "r", encoding="utf-8") as f:
            ai_portraits_data = yaml.safe_load(f)

        caption_title = ai_portraits_data[context["domain"]]["caption_title"]
        msg = (
            f"✨ Готово, {context['name']}. Это образ {caption_title}\n"
            # "**ПОДСТАВЛЯЕТСЯ ТЕКСТ: КОРОТКАЯ ТРАКТОВКА КАРТОЧКИ**\n"
            "Сохрани его и возвращайся, когда хочется мягкости, принятия и близости 💗\n"
        )

        buttons = {
            "🎭 В меню AI-образов": AiPortraitGenerate(button="back").pack(),
            # "📤 Поделиться": AiPortraitGenerate(button="share").pack(),
        }
        kbd = InlineKbd(buttons=buttons, width=1)

        user = await get_user_by_telegram_id(call.from_user.id, db_session)

        await animation_while_generating_picture.stop()

        await call.message.answer_photo(
            photo=picture, caption=msg, reply_markup=kbd.markup
        )
        # await call.message.answer(msg, reply_markup=kbd.markup)
        await decrease_user_balance(user.id, COST["ai_portrait"], db_session)
    else:
        await state.clear()
        return


#  ----------- NO AI-PORTRAITS FOR POOR -----------


@ai_portraits_rtr.callback_query(AiPortraitGenerate.filter(), AiPortraitStates.aspect)
async def handle_no_ai_portraits_for_poor(
    call: CallbackQuery,
    state: FSMContext,
    db_session: AsyncSession,
) -> None:

    user_balance = await get_user_balance(call.from_user.id, db_session)
    cost = await state.get_value("cost")

    logger.info(
        f"{call.from_user.id} @{call.from_user.username} - 'no_ai_portraits_for_poor (ub:{user_balance} cost:{cost})'"
    )

    await call.answer()

    buttons = {
        "🪙 Пополнить баланс": LkButton(button="top_up").pack(),
    }
    kbd = InlineKbd(buttons=buttons, width=1)

    await call.message.answer(
        (
            f"Для открытия этого образа необходимо {cost}⚡️.\n"
            f"Сейчас на вашем балансе: {user_balance}⚡️.\n\n"
            "Мы остановились буквально в шаге от ответа. Вселенная любит энергообмен — давайте пополним ресурс, чтобы поток не прерывался.\n\n"
            "Нажмите кнопку ниже, чтобы выбрать пакет энергии 👇\n"
        ),
        reply_markup=kbd.markup,
    )
