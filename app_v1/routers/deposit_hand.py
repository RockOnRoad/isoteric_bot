import logging

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from email_validator import validate_email, EmailNotValidError
from sqlalchemy.ext.asyncio import AsyncSession

from db.crud import (
    get_user_by_telegram_id,
    create_payment,
    get_payment_by_payment_id,
    update_user_info,
)
from keyboards import InlineKbd
from schemas import LkTopUp, YKOperations, EmailStates, TARIFFS
from services import PaymentService, TopupRoutine
from core.config import settings

logger = logging.getLogger(__name__)
tu_rtr = Router()


#  ----------- E-MAIL HANDLER -----------


@tu_rtr.message(EmailStates.email)
async def email_handler(
    message: Message, state: FSMContext, db_session: AsyncSession
) -> None:

    email = message.text.strip()

    try:
        validate_email(email)

        rub = await state.get_value("rub")
        await state.clear()

        #  Сохраняем email в бд
        await update_user_info(
            user_id=message.from_user.id, data={"mail": email}, session=db_session
        )

        buttons = {
            "Продолжить": LkTopUp(rub=rub).pack(),
        }
        kbd = InlineKbd(buttons=buttons, width=2)
        await message.answer("✅ Email принят", reply_markup=kbd.markup)
        return

    except EmailNotValidError:
        await message.answer("Проверьте что email указан корректно\nВведите ещё раз")


#  ----------- CALL TO PAY -----------


@tu_rtr.callback_query(LkTopUp.filter())
async def top_up(
    call: CallbackQuery,
    callback_data: LkTopUp,
    state: FSMContext,
    db_session: AsyncSession,
) -> None:

    # Проверяем, указан ли у пользователя email
    user = await get_user_by_telegram_id(tg_id=call.from_user.id, session=db_session)
    if user.mail is None:
        await state.set_state(EmailStates.email)
        await state.update_data(rub=callback_data.rub)
        await call.message.answer("🧾 На какой email отправить чек?")
        return

    payment_service = PaymentService()
    rub_amount = callback_data.rub
    kreds = TARIFFS.get(rub_amount, {}).get("kreds")

    #  Создаем платеж в YooKassa
    payment_data = payment_service.create_payment(
        kreds=kreds,
        amount_rub=rub_amount,
        chat_id=call.message.chat.id,
        email=user.mail,
        # email=user.mail,
    )

    #  Сохраняем данные платежа в state
    await state.update_data(
        payment_link=str(payment_data["confirmation_url"]),
        payment_amount=payment_data["amount"],
    )

    # Сохраняем платеж в БД (amount - кредиты, rub_amount - рубли)
    if kreds is None:
        logger.error(f"Kreds is None for amount {rub_amount}")
        kreds = rub_amount

    await create_payment(
        user_id=user.id,
        payment_id=payment_data["payment_id"],
        amount=kreds,
        rub_amount=rub_amount,
        status="pending",
        session=db_session,
    )

    buttons = {
        "🔄 Проверить платеж": YKOperations(
            operation="check", payment_id=payment_data["payment_id"]
        ).pack(),
    }
    kbd = InlineKbd(buttons=buttons, width=2)

    await call.message.edit_text(
        (
            f"<b>Пополнение баланса</b>\n\n"
            f"<b>ID платежа:</b> {payment_data['payment_id']}\n"
            f"<b>Сумма:</b> {payment_data['amount']} ₽\n\n"
            f"<b>Ссылка для оплаты:</b> {payment_data['confirmation_url']}"
        ),
        reply_markup=kbd.markup,
    )


#  ----------- CHECK PAYMENT -----------


@tu_rtr.callback_query(YKOperations.filter(F.operation == "check"))
async def payment_status(
    call: CallbackQuery,
    callback_data: YKOperations,
    state: FSMContext,
    db_session: AsyncSession,
) -> None:
    payment_service = PaymentService(payment_id=callback_data.payment_id)
    payment_status_data: dict | None = payment_service.get_status_success()
    #  payment_status_data: {'status': 'succeeded', 'metadata': {'cms_name': 'yookassa_sdk_python', 'chat_id': '...'}, 'amount': Decimal('699.00')}

    if payment_status_data is None:

        await call.message.delete()

        payment_link = await state.get_value("payment_link")
        payment_amount = await state.get_value("payment_amount")

        buttons = {
            "🔄 Проверить платеж": YKOperations(
                operation="check", payment_id=callback_data.payment_id
            ).pack(),
        }
        kbd = InlineKbd(buttons=buttons, width=1)

        await call.message.answer(
            (
                f"<b>Пополнение баланса</b>\n\n"
                f"<b>ID платежа:</b> {callback_data.payment_id}\n"
                f"<b>Сумма:</b> {payment_amount} ₽\n"
                "⚫️ <b>Платеж ещё не прошёл</b>\n\n"
                f"<b>Ссылка для оплаты:</b> {payment_link}\n"
            ),
            reply_markup=kbd.markup,
        )
        return

    elif payment_status_data["status"] == "succeeded":

        payment = await get_payment_by_payment_id(
            payment_id=callback_data.payment_id,
            session=db_session,
        )
        if payment.status == "completed":
            pass

        else:

            user = await get_user_by_telegram_id(
                tg_id=call.from_user.id, session=db_session
            )
            if user is None:
                logger.error(f"User with tg_id {call.from_user.id} not found")
                return

            #  Запускаем рутину пополнения баланса
            topup_routine = TopupRoutine(session=db_session, user_id=user.id)
            await topup_routine.process_successful_payment(payment=payment)

        await call.message.edit_text(
            (
                f"<b>Ваш баланс пополнен на {payment.amount} энергии ⚡️</b>\n\n"
                "Вы выбрали путь Изобилия и развития. Вселенная всегда щедро возвращает тем, кто не боится инвестировать в свою Душу.\n"
                "Теперь инструменты Матрицы готовы к работе.\n\n"
                "👇 Куда направим этот ресурс прямо сейчас?"
            )
        )
        await state.clear()
        return
    # else:
