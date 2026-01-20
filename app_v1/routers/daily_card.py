from datetime import date
import logging

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import COST
from db.crud import get_user_by_telegram_id, update_user_info, decrease_user_balance
from services import GoogleAI, OpenAIClient
from keyboards import InlineKbd
from schemas import LkButton
from services import MessageAnimation


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

    if latest_daily_card is None or latest_daily_card != date.today():

        await update_user_info(
            user_id=update.from_user.id,
            data={"latest_daily_card": date.today()},
            session=db_session,
        )

        context = {
            "name": user.name,
            "sex": user.sex,
            "birthday": user.birthday,
            "current_date": date.today(),
        }

        # Анимация сообщения во время генерации ответа
        animation_while_generating_response = MessageAnimation(
            message_or_call=update,
            base_text="✨ Настраиваюсь на поток",
        )
        await animation_while_generating_response.start()

        #  Получаем текст
        client = OpenAIClient(auto_create_conv=True)
        answer, conversation_id = await client.chatgpt_response(
            feature="daily_card", context=context, max_length=1020
        )

        context["chatGPT_answer"] = answer

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

        await animation_while_generating_response.stop()

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
            f"{user.name}, мы уже открыли карту этого дня. ✨\n"
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


dc_rtr.message.register(handle_daily_card_main, F.text == "🃏 Карта Дня")
# ai_portraits_rtr.callback_query.register(
#     handle_ai_portraits_main, AiPortraitGenerate.filter(F.button == "back")
# )
