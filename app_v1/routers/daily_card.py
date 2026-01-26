from datetime import date
import logging
import xml.sax.saxutils as saxutils

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from google.genai.errors import ClientError

from core.config import COST, GOOGLE_AI_MODEL, OPENAI_MODEL
from db.crud import (
    get_user_by_telegram_id,
    update_user_info,
    decrease_user_balance,
    add_generation,
)
from keyboards import InlineKbd
from schemas import LkButton
from services import (
    GoogleAI,
    OpenAIClient,
    MessageAnimation,
    handle_google_ai_error,
    OpenAIUnsupportedLocation,
    handle_openai_error,
)


logger = logging.getLogger(__name__)
dc_rtr = Router()


#  ----------- DAILY CARD ----------- (main)


async def handle_daily_card_main(
    update: Message | CallbackQuery, state: FSMContext, db_session: AsyncSession
) -> None:
    await state.clear()

    user = await get_user_by_telegram_id(update.from_user.id, db_session)
    latest_daily_card = user.latest_daily_card

    cost = COST["daily_card"]

    request = {
        "job": "daily_card",
        "name": user.name,
        "sex": user.sex,
        "birthday": user.birthday,
    }
    gen_data = {
        "user_id": user.id,
        "model": f"{GOOGLE_AI_MODEL}, {OPENAI_MODEL}",
        "request": request,
        "cost": COST["daily_card"],
        "gen_type": "image, text",
    }
    generation = None

    if user.balance < cost:

        text = (
            f"Для открытия этого разбора необходимо {cost}⚡️.\n"
            f"Сейчас на вашем балансе: {user.balance}⚡️.\n\n"
            "Мы остановились буквально в шаге от ответа. Вселенная любит энергообмен — давайте пополним ресурс, чтобы поток не прерывался.\n\n"
            "Нажмите кнопку ниже, чтобы выбрать пакет энергии 👇\n"
        )

        buttons = {
            "🪙 Пополнить баланс": LkButton(button="top_up").pack(),
        }
        kbd = InlineKbd(buttons=buttons, width=1)

        if isinstance(update, CallbackQuery):
            await update.message.edit_text(text, reply_markup=kbd.markup)
        elif isinstance(update, Message):
            await update.answer(text, reply_markup=kbd.markup)

        logger.info(
            f"{update.from_user.id} @{update.from_user.username} - 'no daily card for poor (ub:{user.balance} cost:{cost})'"
        )

        gen_data["gen_status"] = "not_enough_balance"
        generation = await add_generation(session=db_session, commit=True, **gen_data)
        return

    elif latest_daily_card is None or latest_daily_card != date.today():

        context = {
            "name": user.name,
            "sex": user.sex,
            "birthday": user.birthday,
            "current_date": date.today(),
        }

        # Анимация сообщения во время генерации ответа
        animation_while_generating_image = MessageAnimation(
            message_or_call=update,
            base_text="✨ Настраиваюсь на поток",
        )
        await animation_while_generating_image.start()

        try:
            #  Получаем текст
            client = OpenAIClient(auto_create_conv=True)
            answer, conversation_id = await client.chatgpt_response(
                feature="daily_card", context=context, max_length=1020
            )
        except OpenAIUnsupportedLocation as e:
            gen_data["gen_status"] = "error"
            generation = await add_generation(
                session=db_session, commit=True, **gen_data
            )
            await handle_openai_error(
                error=e,
                upd=update,
                job="daily_card",
                animation=animation_while_generating_image,
            )
            return

        context["chatGPT_answer"] = answer

        try:
            #  Получаем изображение
            client = GoogleAI()
            picture: BufferedInputFile | None = await client.generate_picture(
                feature="daily_card",
                context=context,
                #  Сразу после начала генерации сбрасываем состояние чтобы не стартанула следующая генерация
                state=state,
            )
            # picture = FSInputFile(
            #     "app_v1/src/assets/owl_pic_620_6b3d4bb80adc24b34ad43895d6d7ae8e.jpg"
            # )

            gen_data["gen_status"] = "success"
            generation = await add_generation(
                session=db_session, commit=True, **gen_data
            )

        except ClientError as e:
            #  Сохранение записи о генерации в базу данных
            gen_data["gen_status"] = "error"
            generation = await add_generation(
                session=db_session, commit=True, **gen_data
            )
            await handle_google_ai_error(
                error=e,
                upd=update,
                job="daily_card",
                animation=animation_while_generating_image,
            )
            return

        await update_user_info(
            user_id=update.from_user.id,
            data={"latest_daily_card": date.today()},
            session=db_session,
        )

        await animation_while_generating_image.stop()

        if isinstance(update, CallbackQuery):
            await update.message.edit_text("Вы еще не получили карту дня")
        elif isinstance(update, Message):
            await update.answer_photo(photo=picture, caption=answer)

        await decrease_user_balance(user.id, COST["daily_card"], db_session)

        logger.info(
            f"{update.from_user.id} @{update.from_user.username} - 'daily card generation'"
        )
    else:

        text = (
            f"{saxutils.escape(user.name)}, мы уже открыли карту этого дня. ✨\n"
            "Пространство не меняет свои вибрации от повторных вопросов — это лишь создаёт лишний шум.\n"
            "Энергия уже запущена.\n"
            "Сейчас важнее не спрашивать снова, а действовать.\n"
            "Перечитайте утреннее послание, там есть всё, что нужно.\n"
        )

        if isinstance(update, CallbackQuery):
            await update.message.edit_text("Вы уже получили карту дня")
        elif isinstance(update, Message):
            await update.answer(text)

        logger.info(
            f"{update.from_user.id} @{update.from_user.username} - 'daily card already generated today'"
        )

        gen_data["gen_status"] = "already_generated_today"
        generation = await add_generation(session=db_session, commit=True, **gen_data)
        return


dc_rtr.message.register(handle_daily_card_main, F.text == "🃏 Карта Дня")
# ai_portraits_rtr.callback_query.register(
#     handle_ai_portraits_main, AiPortraitGenerate.filter(F.button == "back")
# )
