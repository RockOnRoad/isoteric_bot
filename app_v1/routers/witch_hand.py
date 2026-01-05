import asyncio
import logging

from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, BufferedInputFile, FSInputFile
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import COST
from db.crud import (
    # get_or_create_user,
    update_user_info,
    get_user_by_telegram_id,
    decrease_user_balance,
)
from keyboards import InlineKbd
from schemas import (
    BioStates,
    BioCorrect,
    main_reply_kbd,
    BalanceCheck,
    ReadingsDomain,
    ReadingsStates,
)
from services import GoogleAI, OpenAIClient

logger = logging.getLogger(__name__)
witch_rtr = Router()


#  ----------- FREE GENERATION (aka Witchcraft) -----------


@witch_rtr.callback_query(
    BioCorrect.filter(F.button == "yes"), BioStates.edit_or_confirm
)
async def stir_the_cauldron(
    call: CallbackQuery, state: FSMContext, db_session: AsyncSession
) -> None:
    logger.info(f"{call.from_user.id} @{call.from_user.username} - 'stir_the_cauldron'")

    msg_generating_image = await call.message.edit_text(
        f"🌀 Соединяюсь с полем твоей Матрицы..."
    )

    # #  updating user telegram info in database
    # user_id = call.from_user.id
    # username = call.from_user.username
    # first_name = call.from_user.first_name
    # last_name = call.from_user.last_name
    # await get_or_create_user(user_id, username, first_name, last_name, db_session)

    #  getting fsm data
    fsm_data = await state.get_data()
    # {'name': "Даниил", 'sex': 'm', 'birthday_counter': 0, 'birthday': '17.04.1990', 'edited': False,}
    data = {
        "name": fsm_data["name"],
        "sex": fsm_data["sex"],
        "birthday": fsm_data["birthday"],
    }
    await state.clear()

    #  generating image
    client = GoogleAI()
    photo: BufferedInputFile | None = await client.generate_picture(
        feature="first",
        context=data,
        state=state,
    )
    # photo = FSInputFile(
    #     "app_v1/src/assets/owl_pic_620_6b3d4bb80adc24b34ad43895d6d7ae8e.jpg"
    # )

    #  updating user input info in database
    user_id = call.from_user.id
    await update_user_info(user_id, data, db_session)
    await msg_generating_image.delete()
    await asyncio.sleep(0.2)
    msg_generating_text = await call.message.answer(
        f"🔢 Рассчитываю центральный аркан ..."
    )

    # getting message
    client = OpenAIClient(auto_create_conv=False)
    answer, conversation_id = await client.chatgpt_response(
        feature="first", context=data
    )

    readings_main_buttons = {
        "💸 Деньги": ReadingsDomain(button="wealth").pack(),
        "❤️ Отношения": ReadingsDomain(button="relations").pack(),
        "🔮 Предназначение": ReadingsDomain(button="purpose").pack(),
        "🧬 Карма": ReadingsDomain(button="karma").pack(),
        "🌿 Ресурс": ReadingsDomain(button="resource").pack(),
        "📘 Полный разбор": ReadingsDomain(button="full_reading").pack(),
    }
    kbd = InlineKbd(buttons=readings_main_buttons, width=2)

    await msg_generating_text.delete()
    try:
        # caption = f"{data['name']}, я получила твой центральный код"
        await call.message.answer_photo(
            photo=photo,
            # caption=caption,
            reply_markup=main_reply_kbd.markup,
        )
    except TelegramBadRequest as e:
        logger.error(f"Error sending photo: {e}")
        pass

    #  Подготовка к переходу к разделу разборов
    user = await get_user_by_telegram_id(call.from_user.id, db_session)
    await state.set_state(ReadingsStates.witch)
    await state.update_data(name=user.name, birthday=user.birthday, sex=user.sex)

    await call.message.answer(answer, reply_markup=kbd.markup)
    # await call.message.answer("answer", reply_markup=kbd.markup)


#  ----------- FOLLOW UP RESPONSE -----------


@witch_rtr.message(BalanceCheck())
async def follow_up_response(
    message: Message, state: FSMContext, db_session: AsyncSession
) -> None:
    context = await state.get_data()
    if context:
        state_name: str | None = await state.get_state()
        logger.info(
            f"{message.from_user.id} @{message.from_user.username} - '{state_name} follow up'"
        )
        #  Getting conversation id from database
        conversation_id = context.get("conversation_id")
        #  Getting response from OpenAI
        client = OpenAIClient(conv=conversation_id)
        answer = await client.chatgpt_response_follow_up(prompt=message.text)

        user = await get_user_by_telegram_id(message.from_user.id, db_session)

        if answer:
            new_balance = await decrease_user_balance(
                user.id,
                COST["follow_up"],
                db_session,
            )

        await message.answer(answer)

    else:
        return
